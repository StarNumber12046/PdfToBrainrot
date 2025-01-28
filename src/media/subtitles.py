from moviepy.editor import CompositeVideoClip, ImageClip, VideoFileClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from typing import List, Dict


def add_subtitles_to_video(
    video_clip: VideoFileClip,
    whisper_chunks: List[Dict],
    font_path: str = "arial.ttf",
    font_size: int = 48,
    text_color: str = "white",
) -> CompositeVideoClip:
    text_clips = []

    for chunk in whisper_chunks:
        start_time = chunk["timestamp"][0]
        end_time = chunk["timestamp"][1]
        text = chunk["text"]

        img_width = video_clip.w
        img_height = 100
        img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            raise ValueError(f"Font file not found at {font_path}")

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (img_width - text_width) // 2
        y = (img_height - text_height) // 2

        draw.text(
            (x, y),
            text,
            font=font,
            fill=text_color,
            stroke_fill="black",
            stroke_width=2,
        )

        text_clip = (
            ImageClip(np.array(img))
            .set_duration(end_time - start_time)
            .set_position(("center", "center"))
            .set_start(start_time)
        )

        text_clips.append(text_clip)

    return CompositeVideoClip([video_clip, *text_clips])
