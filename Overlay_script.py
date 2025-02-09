import os
import re

from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

TOPIC_SUMMARY_DIR = "topic_summaries"
VIDEO_INPUT_DIR = "videos"
VIDEO_OUTPUT_DIR = "videos_with_overlays"

def parse_time_to_seconds(timestr):
    h, m, s = timestr.split(':')
    return int(h)*3600 + int(m)*60 + int(s)

def process_text_file(txt_path):
    video_id = None
    video_title = None
    segments = []

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    current_topic = None
    current_summary = None
    current_timestamp = None

    for line in lines:
        if line.startswith("Video ID:"):
            video_id = line.replace("Video ID:", "").strip()
        elif line.startswith("Video Title:"):
            video_title = line.replace("Video Title:", "").strip()
        elif line.startswith("Topic:"):
            current_topic = line.replace("Topic:", "").strip()
        elif line.startswith("Summary:"):
            current_summary = line.replace("Summary:", "").strip()
        elif line.startswith("Timestamp:"):
            current_timestamp = line.replace("Timestamp:", "").strip()
            if current_timestamp:
                match = re.match(r'(\d{2}:\d{2}:\d{2})\s*-\s*(\d{2}:\d{2}:\d{2})', current_timestamp)
                if match:
                    start_str, end_str = match.groups()
                    start_sec = parse_time_to_seconds(start_str)
                    end_sec = parse_time_to_seconds(end_str)
                    segments.append({
                        "topic": current_topic or "",
                        "summary": current_summary or "",
                        "start_sec": start_sec,
                        "end_sec": end_sec
                    })
            current_topic = None
            current_summary = None
            current_timestamp = None

    return video_id, video_title, segments

def overlay_topics(video_path, segments, output_path):
    base_clip = VideoFileClip(video_path)
    text_clips = []

    for seg in segments:
        txt_content = f"{seg['topic']}\n{seg['summary']}"
        duration = seg['end_sec'] - seg['start_sec']

        # Minimal arguments to avoid "multiple values for argument 'font'"
        text_clip = (
            TextClip(
                txt_content,
                fontsize=40,
                color="white",
                method="label"  # or "caption" + size=(width, height) if needed
            )
            .set_start(seg['start_sec'])
            .set_duration(duration)
            .set_position(('center', 'bottom'))
        )
        text_clips.append(text_clip)
    
    final_clip = CompositeVideoClip([base_clip, *text_clips])
    print(f"Processing overlay -> {output_path}")
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    
    final_clip.close()
    base_clip.close()

def main():
    os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)

    for txt_file in os.listdir(TOPIC_SUMMARY_DIR):
        if not txt_file.lower().endswith(".txt"):
            continue

        txt_path = os.path.join(TOPIC_SUMMARY_DIR, txt_file)
        video_id, video_title, segments = process_text_file(txt_path)

        if not video_id or not segments:
            print(f"Skipping {txt_file}, no video_id or no segments found.")
            continue
        
        input_video_path = os.path.join(VIDEO_INPUT_DIR, f"{video_id}.mp4")
        if not os.path.exists(input_video_path):
            print(f"Video file {input_video_path} not found. Skipping.")
            continue
        
        output_video_path = os.path.join(VIDEO_OUTPUT_DIR, f"{video_id}_with_overlay.mp4")
        if os.path.exists(output_video_path):
            print(f"Overlay video already exists for {video_id}. Skipping.")
            continue

        overlay_topics(input_video_path, segments, output_video_path)

if __name__ == "__main__":
    main()
