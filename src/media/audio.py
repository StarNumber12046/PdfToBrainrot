from moviepy.editor import AudioFileClip
import moviepy.audio.fx.all as afx
from moviepy.audio.fx.audio_loop import audio_loop
import io
import tempfile


def get_audio_file_path(audio_bytes: io.BytesIO) -> str:
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(audio_bytes.getvalue())
        temp_file.flush()
        return temp_file.name


def create_audio_clip_from_path(audio_file_path: str) -> AudioFileClip:
    return AudioFileClip(audio_file_path)


def process_background_audio(
    audio_clip: AudioFileClip, min_duration: float, volume: float
) -> AudioFileClip:
    if audio_clip.duration < min_duration:
        audio_clip = audio_loop(audio_clip, duration=min_duration)

    return audio_clip.subclip(0, min_duration).fx(afx.volumex, volume)  # type: ignore
