import argparse
from pathlib import Path
from moviepy.editor import (
    CompositeAudioClip,
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
)
import dotenv
import replicate
from media.audio import (
    create_audio_clip_from_path,
    get_audio_file_path,
    process_background_audio,
)
from media.video import process_background_video
from media.subtitles import add_subtitles_to_video
from services.tts import text_to_speech
from services.summarizer import summarize_text
from services.tixte import upload_to_tixte
from utils.file_utils import get_random_file_from_directory, get_pdf_text
import langs

dotenv.load_dotenv(".env")


def main(
    input_path: Path,
    output_path: Path,
    video_path: Path,
    audio_path: Path,
    no_sub: bool,
    no_summary: bool,
    lang: str,
    model: str,
    voice_provider: str,
    volume: float,
):
    try:
        print("Getting text from PDF")
        text = get_pdf_text(input_path).replace("\n", "")
        lang_config = langs.LANGS[lang]

        # Generate TTS audio
        if not no_summary:
            print("Summarizing text")
            summarized_text = summarize_text(text, lang_config["system_prompt"], model)
            print("Generating TTS audio")
            tts_audio = text_to_speech(
                voice_provider,
                summarized_text,
                lang_config["tts_lang"],
                lang_config["voice_id"],
            )
        else:
            print("Generating TTS audio")
            tts_audio = text_to_speech(
                voice_provider, text, lang_config["tts_lang"], lang_config["voice_id"]
            )

        tts_clip_path = get_audio_file_path(tts_audio)
        tts_clip = create_audio_clip_from_path(tts_clip_path)

        # Process video and audio
        print("Processing video")
        video_clip = process_background_video(
            video_clip=VideoFileClip(str(video_path)), min_duration=tts_clip.duration
        )
        print(f"Processing audio (volume: {volume})")
        audio_clip = process_background_audio(
            audio_clip=AudioFileClip(str(audio_path)),
            min_duration=tts_clip.duration,
            volume=volume,
        )

        # Handle subtitles if needed
        final_clip = CompositeVideoClip([video_clip])
        if not no_sub:
            print("Uploading TTS audio to Tixte")
            clip_url = upload_to_tixte(tts_clip_path)[0]
            output = replicate.run(
                "vaibhavs10/incredibly-fast-whisper:3ab86df6c8f54c11309d4d1f930ac292bad43ace52d10c80d87eb258b3c9f79c",
                input={
                    "audio": clip_url,
                    "language": lang_config["whisper_lang"],
                    "timestamp": "word",
                },
            )
            print("Adding subtitles to video")
            final_clip = add_subtitles_to_video(video_clip, output["chunks"])  # type: ignore

        # Combine audio tracks
        print("Combining audio tracks")
        final_clip.audio = CompositeAudioClip([audio_clip, tts_clip])

        # Write output file
        print("Writing output file")
        final_clip.write_videofile(str(output_path))

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise
    finally:
        # Clean up resources
        try:
            final_clip.close()  # type: ignore
            video_clip.close()  # type: ignore
            audio_clip.close()  # type: ignore
        except:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate video content with narration and music."
    )
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
    parser.add_argument("--no-sub", action="store_true", help="Do not add subtitles")
    parser.add_argument(
        "--no-summary", action="store_true", help="Do not summarize the text"
    )
    parser.add_argument(
        "--model", type=str, default="deepseek-chat", help="AI model to use"
    )
    parser.add_argument(
        "--voice-provider", type=str, default="google", help="Voice provider"
    )
    parser.add_argument(
        "--volume", type=float, default=0.3, help="Background audio volume"
    )
    parser.add_argument("--lang", type=str, default="en", help="Content language")

    args = parser.parse_args()

    video_path = args.video or get_random_file_from_directory(Path("video"))
    audio_path = args.audio or get_random_file_from_directory(Path("audio"))

    if not video_path or not audio_path:
        print("Error: Could not find video or audio file.")
        exit(1)

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
