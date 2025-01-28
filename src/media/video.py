from moviepy.editor import VideoFileClip
from moviepy.video.fx.loop import loop


def process_background_video(
    video_clip: VideoFileClip, min_duration: float
) -> VideoFileClip:
    if video_clip.duration < min_duration:
        video_clip = loop(video_clip, duration=min_duration)

    video_clip = video_clip.subclip(0, min_duration)

    # Calculate 9:16 aspect ratio crop
    cropped_clip_width = video_clip.h * 9 / 16
    x1 = (video_clip.w - cropped_clip_width) / 2
    x2 = x1 + cropped_clip_width

    return video_clip.crop(x1=x1, x2=x2, y1=0, y2=video_clip.h)  # type: ignore
