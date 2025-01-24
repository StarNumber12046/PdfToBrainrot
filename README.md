# Video Content Generator

A Python tool that generates video content by combining background video, audio, and text-to-speech narration with optional subtitles. Perfect for creating automated content for social media platforms.

## Features

- Converts text/PDF input into narrated video content
- Supports multiple languages (English, Italian)
- Multiple text-to-speech providers (Google TTS, ElevenLabs)
- Automatic text summarization using AI models (DeepSeek, LLaMA)
- Automatic subtitle generation using Whisper
- Background music volume control
- 9:16 aspect ratio optimization for social media
- Random background video/audio selection from directories

## Prerequisites

- Python 3.10+
- FFmpeg installed on your system
- Required API keys:
  - DeepSeek API key (for summarization)
  - ElevenLabs API key (for premium TTS)
  - Tixte API key (for subtitle generation)
  - Replicate API token (for whisper subtitle generation and llama-3.1)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd video-content-generator
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your API keys:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
REPLICATE_API_TOKEN=your_replicate_api_key
TIXTE_API_KEY=your_tixte_api_key
TIXTE_DOMAIN=your_tixte_domain
```

## Usage

Basic usage:

```bash
python src/main.py --input input.txt --output output.mp4
```

Full options:

```bash
python src/main.py \
  --input input.txt \
  --output output.mp4 \
  --video background.mp4 \
  --audio background.mp3 \
  --lang en \
  --model deepseek-chat \
  --voice-provider google \
  --volume 0.3 \
  --no-sub \
  --no-summary
```

### Arguments

- `--input`: Path to input text/PDF file (required)
- `--output`: Path to output video file (required)
- `--video`: Path to background video file (optional)
- `--audio`: Path to background audio file (optional)
- `--lang`: Language code (default: "en")
- `--model`: AI model for summarization ("deepseek-chat" or "llama-3.1")
- `--voice-provider`: TTS provider ("google" or "elevenlabs")
- `--volume`: Background audio volume (0.0-1.0, default: 0.3)
- `--no-sub`: Disable subtitle generation
- `--no-summary`: Disable text summarization

### Directory Structure

The tool expects the following directory structure:
audio/ : contains audio tracks for background music
video/ : contains video tracks that will be used as background
