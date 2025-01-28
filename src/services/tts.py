import io

from gtts import gTTS
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
import os

elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY", ""))


def google_text_to_speech(text: str, lang: str) -> io.BytesIO:
    out = io.BytesIO()
    tts = gTTS(text, lang=lang)
    tts.write_to_fp(out)
    return out


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


def text_to_speech(
    provider: str, text: str, lang: str, voice_id: str  # type: ignore
) -> io.BytesIO:
    match provider:
        case "google":
            return google_text_to_speech(text, lang)
        case "elevenlabs":
            return generate_elevenlabs_audio(text, voice_id)
        case _:
            raise ValueError("Provider not supported")
