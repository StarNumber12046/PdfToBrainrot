import argparse
import enum
import io
import os
import random
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip
import numpy as np
from moviepy.editor import CompositeVideoClip, TextClip
from moviepy.editor import CompositeAudioClip, VideoFileClip, AudioFileClip
import moviepy.audio.fx.all as afx
import moviepy.video.fx.all as vfx
from moviepy.video.fx.loop import loop
from moviepy.audio.fx.audio_loop import audio_loop
from pypdf import PdfReader
from gtts import gTTS
import replicate
import dotenv
import requests
import langs
from openai import OpenAI
from elevenlabs import Voice, VoiceSettings, play, save
from elevenlabs.client import ElevenLabs

dotenv.load_dotenv(".env")
deepseek = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com"
)

elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY", ""))


def add_subtitles_to_video(
    video_clip, whisper_chunks, font_path="arial.ttf", font_size=48, text_color="white"
):
    """
    Adds subtitles to the video based on OpenAI Whisper chunks.

    Args:
        video_clip (VideoFileClip): The original video.
        whisper_chunks (list): A list of Whisper output chunks, each with "start", "end", and "text".
        font_path (str): Path to the font file to use.
        font_size (int): Font size for the text.
        text_color (str): Text color (e.g., "white", "black", "#RRGGBB").

    Returns:
        CompositeVideoClip: A new video with text overlay.
    """
    text_clips = []

    for chunk in whisper_chunks:
        start_time = chunk["timestamp"][0]
        end_time = chunk["timestamp"][1]
        text = chunk["text"]

        # Create a transparent image for the text
        img_width = video_clip.w
        img_height = 100  # Height for the subtitle box
        img = Image.new(
            "RGBA", (img_width, img_height), (0, 0, 0, 0)
        )  # Transparent background
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            raise ValueError(
                f"Font file not found at {font_path}. Please provide a valid font file."
            )

        # Calculate text bounding box and position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (img_width - text_width) // 2
        y = (img_height - text_height) // 2

        # Draw the text onto the image
        draw.text(
            (x, y),
            text,
            font=font,
            fill=text_color,
            stroke_fill="black",
            stroke_width=2,
        )

        # Convert PIL image to a MoviePy ImageClip
        text_clip = (
            ImageClip(np.array(img))
            .set_duration(end_time - start_time)
            .set_position(
                ("center", "center")
            )  # Position at the bottom center of the video
            .set_start(start_time)
        )

        text_clips.append(text_clip)

    # Overlay text clips on the video
    return CompositeVideoClip([video_clip, *text_clips])


def get_random_file_from_directory(directory):
    files = list(directory.glob("*"))
    return random.choice(files) if files else None


def generate_elevenlabs_audio(text: str, voice_id: str) -> io.BytesIO:
    audio = elevenlabs_client.generate(
        text=text,
        voice=Voice(
            voice_id=voice_id,
            settings=VoiceSettings(
                stability=0.75, similarity_boost=0.5, style=0.5, use_speaker_boost=True
            ),
        ),
    )
    return io.BytesIO(b"".join(list(audio)))


def get_pdf_text(pdf_path: Path) -> str:
    if not str(pdf_path).endswith(".pdf"):
        with open(pdf_path, "r") as fp:
            return fp.read()
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def google_text_to_speech(text: str, lang: str) -> io.BytesIO:
    out = io.BytesIO()
    tts = gTTS(text, lang=lang)
    tts.write_to_fp(out)
    return out


def text_to_speech(provider: str, text: str, lang: str) -> io.BytesIO:
    language = langs.LANGS[lang]
    match provider:
        case "google":
            return google_text_to_speech(text, language["tts_lang"])
        case "elevenlabs":
            return generate_elevenlabs_audio(text, language["voice_id"])
        case _:
            raise Exception("Provider not supported")


def get_audio_file_path(audio_bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(audio_bytes.getvalue())
        temp_file.flush()
        return temp_file.name


def create_audio_clip_from_path(audio_file_path):
    return AudioFileClip(audio_file_path)


def upload_to_tixte(file_path):
    """
    Uploads a file to Tixte and returns the upload and deletion URLs.

    :param file_path: Path to the file to be uploaded.
    :return: A tuple containing the upload URL and deletion URL, or an error message.
    """
    url = "https://api.tixte.com/v1/upload"
    headers = {"Authorization": os.getenv("TIXTE_API_KEY")}
    data = {
        "payload_json": '{"domain": "<yourdomain>"}'.replace(
            "<yourdomain>", os.getenv("TIXTE_DOMAIN", "")
        )
    }

    try:
        with open(file_path, "rb") as file:
            files = {"file": (file_path, file)}
            response = requests.post(url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            json_response = response.json()
            upload_url = json_response.get("data", {}).get("direct_url")
            deletion_url = json_response.get("data", {}).get("deletion_url")
            print(json_response)
            return upload_url, deletion_url
        else:
            return f"Error: {response.status_code}", response.text

    except FileNotFoundError:
        return "Error: File not found", None
    except Exception as e:
        return f"Error: {str(e)}", None


def summarize_text(text: str, system_prompt: str, model: str) -> str:
    match model:
        case "deepseek-chat":
            response = deepseek.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {"role": "user", "content": text},
                ],
                stream=False,
            )
            print(response.choices[0].message.content)
            return (
                (response.choices[0].message.content or "")
                .replace("#", "")
                .replace("*", "")
            )
        case "llama-3.1":
            buf = ""
            for event in replicate.stream(
                "meta/meta-llama-3.1-405b-instruct",
                input={
                    "top_k": 50,
                    "top_p": 0.9,
                    "prompt": text,
                    "max_tokens": 4096,
                    "min_tokens": 0,
                    "temperature": 0.6,
                    "system_prompt": " ",
                    "presence_penalty": 0,
                    "frequency_penalty": 0,
                },
            ):
                buf += str(event)
            print(buf)
            return buf.replace("#", "").replace("*", "")
        case _:
            raise Exception("Model not supported")


def main(
    input_path,
    output_path,
    video_path,
    audio_path,
    no_sub,
    no_summary,
    lang,
    model,
    voice_provider,
    volume,
):
    try:
        text = get_pdf_text(input_path).replace("\n", "")  # maybe?
        lang = langs.LANGS[lang]
        if not no_summary:
            tts_clip_path = get_audio_file_path(
                text_to_speech(
                    voice_provider,
                    summarize_text(text, lang["system_prompt"], model),
                    lang["tts_lang"],
                )
            )
        else:
            tts_clip_path = get_audio_file_path(
                text_to_speech(voice_provider, text, lang["tts_lang"])
            )
        tts_clip = create_audio_clip_from_path(tts_clip_path)
        # Load the clips
        video_clip = VideoFileClip(str(video_path))
        audio_clip = AudioFileClip(str(audio_path))

        min_duration = tts_clip.duration

        # Loop video and audio if they're shorter than TTS duration
        if video_clip.duration < min_duration:
            num_loops = int(np.ceil(min_duration / video_clip.duration))
            video_clip = loop(video_clip, duration=min_duration)

        if audio_clip.duration < min_duration:
            num_loops = int(np.ceil(min_duration / audio_clip.duration))
            audio_clip = audio_clip = audio_loop(audio_clip, duration=min_duration)

        # Trim both clips to the exact duration needed
        video_clip = video_clip.subclip(0, min_duration)
        audio_clip = audio_clip.subclip(0, min_duration).fx(afx.volumex, volume)  # type: ignore
        clip_path = upload_to_tixte(tts_clip_path)[0]
        # Calculate the desired width for a 9:16 aspect ratio
        cropped_clip_width = video_clip.h * 9 / 16

        # Calculate the x-coordinates to center the crop
        x1 = (video_clip.w - cropped_clip_width) / 2
        x2 = x1 + cropped_clip_width

        # Crop the video to a 9:16 aspect ratio, centered
        video_clip = video_clip.crop(x1=x1, x2=x2, y1=0, y2=video_clip.h)
        print(clip_path)
        try:
            final_clip = video_clip
            if not no_sub:
                output = replicate.run(
                    "vaibhavs10/incredibly-fast-whisper:3ab86df6c8f54c11309d4d1f930ac292bad43ace52d10c80d87eb258b3c9f79c",
                    input={
                        "audio": clip_path,
                        "language": lang["whisper_lang"],
                        "timestamp": "word",
                    },
                )
                print(output)

                # Combine video and audio
                video_with_subs = add_subtitles_to_video(
                    video_clip, output["chunks"]  # type: ignore
                )
                final_clip = video_with_subs
            final_clip.audio = CompositeAudioClip([audio_clip, tts_clip])

            # Write the output file
            final_clip.write_videofile(str(output_path))
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            raise
        finally:
            # Clean up resources
            try:
                final_clip.close()  # type: ignore
            except:
                pass
            video_clip.close()
            audio_clip.close()

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine video and audio files.")
    parser.add_argument(
        "--input", type=Path, required=True, help="Path to the input file"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Path to the output file"
    )
    parser.add_argument(
        "--video", type=Path, default=None, help="Path to the video file"
    )
    parser.add_argument(
        "--audio", type=Path, default=None, help="Path to the audio file"
    )
    parser.add_argument(
        "--no-sub", type=argparse.BooleanOptionalAction, help="Do not add subtitles to the produced video"  # type: ignore
    )
    parser.add_argument(
        "--no-summary", type=argparse.BooleanOptionalAction, help="Do not summarize the text"  # type: ignore
    )
    parser.add_argument(
        "--model", type=str, default="deepseek-chat", help="Model to use"
    )
    parser.add_argument(
        "--voice-provider", type=str, default="google", help="Voice provider"
    )
    parser.add_argument("--volume", type=float, default=0.3, help="Volume of the audio")
    parser.add_argument("--lang", type=str, default="en", help="Language of the pdf")
    args = parser.parse_args()

    args = parser.parse_args()

    video_path = (
        args.video if args.video else get_random_file_from_directory(Path("video"))
    )
    audio_path = (
        args.audio if args.audio else get_random_file_from_directory(Path("audio"))
    )

    if not video_path or not audio_path:
        print("Error: Could not find a video or audio file.")
    else:
        main(
            args.input,
            args.output,
            video_path,
            audio_path,
            args.no_sub,
            args.no_summary,
            args.lang,
            args.model,
            args.voice_provider,
            args.volume,
        )
