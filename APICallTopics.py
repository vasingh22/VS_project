#This script was used to make the topic_summaries folder where we have different topics and the summary associated with it 
#It ws used using the gemini API key 


import os
import re
import time
import requests
import pandas as pd
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube


YOUTUBE_API_KEY = "AIzaSyCjHFSmCTKpqDswl5lxq9RfsHAb0qROxzs"
GEMINI_API_KEY = "AIzaSyCpSZrRwnLrjDcEI2K2AEefN2OxSRfGavw"   # For Google Generative AI (Gemini)

genai.configure(api_key=GEMINI_API_KEY)

CHANNEL_ID = "UC4a-Gbdw7vOaccHmFo40b9g"


NUM_VIDEOS = 150


OUTPUT_CSV = "output_topics_summaries.csv"


DELAY_BETWEEN_VIDEOS = 5
DELAY_BETWEEN_API_CALLS = 2

def get_uploads_playlist(channel_id, api_key):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "contentDetails", "id": channel_id, "key": api_key}
    response = requests.get(url, params=params)
    data = response.json()
    try:
        return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except (KeyError, IndexError):
        print("Could not retrieve uploads playlist id.")
        return None

def get_video_ids_from_playlist(playlist_id, api_key, max_results=NUM_VIDEOS):
    video_ids = []
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": max_results,
        "key": api_key
    }
    response = requests.get(url, params=params)
    data = response.json()
    for item in data.get("items", []):
        video_ids.append(item["snippet"]["resourceId"]["videoId"])
    return video_ids

def get_video_analytics(video_id, api_key):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",  # not pulling duration here, but can if needed
        "id": video_id,
        "key": api_key
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data.get("items"):
        item = data["items"][0]
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        return {
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "publishedAt": snippet.get("publishedAt", ""),
            "viewCount": statistics.get("viewCount", "0"),
            "likeCount": statistics.get("likeCount", "0"),
            "commentCount": statistics.get("commentCount", "0")
        }
    else:
        print(f"No analytics found for video {video_id}")
        return None

def download_video(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        yt = YouTube(video_url)
        stream = (
            yt.streams.filter(progressive=True, file_extension='mp4')
            .order_by('resolution')
            .desc()
            .first()
        )
        if stream:
            filename = f"{video_id}.mp4"
            stream.download(filename=filename)
            print(f"Downloaded video {video_id} as {filename}")
        else:
            print(f"No suitable stream found for video {video_id}")
    except Exception as e:
        print(f"Error downloading video {video_id}: {e}")

def get_transcript(video_id):
    try:
        return YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        print(f"Transcript not available for video {video_id}: {e}")
        return []

def generate_topics_summaries_timestamps(transcript):
    prompt = f"""
    Analyze the following transcript and extract at least 2-3 relevant topics.
    For each topic, provide:
    **Topic:** <Topic Title>
    **Summary:** <Short Summary (2-3 sentences)>
    **Timestamp:** hh:mm:ss - hh:mm:ss

    Transcript (first 3000 characters):
    {transcript[:3000]}

    Ensure each topic has all three elements.
    """
    try:
        response = genai.GenerativeModel("gemini-pro").generate_content(prompt)
        print("Raw Gemini response:")
        print(response.text)
        if response.text:
            return response.text.strip().split("\n\n")
        else:
            print("No response received from Gemini.")
            return []
    except Exception as e:
        print(f"Error generating topics and summaries: {e}")
        return []

def parse_timestamp_to_seconds(ts_str):
    
    pattern = r'(\d{2}:\d{2}:\d{2})\s*-\s*(\d{2}:\d{2}:\d{2})'
    match = re.match(pattern, ts_str.strip())
    if not match:
        return None, None
    
    start_str, end_str = match.groups()
    start_sec = sum(int(x) * t for x, t in zip(start_str.split(":"), [3600, 60, 1]))
    end_sec = sum(int(x) * t for x, t in zip(end_str.split(":"), [3600, 60, 1]))
    return start_sec, end_sec

def seconds_to_hhmmss(sec):
    
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def get_complete_sentence(text):
  
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    for sentence in sentences:
        if sentence:  # return the first non-empty sentence
            return sentence.strip()
    return text.strip()

def process_video_data():
    os.makedirs("topic_summaries", exist_ok=True)

    
    uploads_playlist = get_uploads_playlist(CHANNEL_ID, YOUTUBE_API_KEY)
    if not uploads_playlist:
        print("No uploads playlist available.")
        return []

   
    video_ids = get_video_ids_from_playlist(uploads_playlist, YOUTUBE_API_KEY)
    if not video_ids:
        print("No videos found in the playlist.")
        return []

    output_data = []

   
    for video_id in video_ids:
        print(f"\nProcessing video: {video_id}")
        analytics = get_video_analytics(video_id, YOUTUBE_API_KEY)
        if analytics is None:
            continue

       
        download_video(video_id)

        
        transcript_segments = get_transcript(video_id)
        if transcript_segments:
            transcript_text = " ".join(seg.get("text", "") for seg in transcript_segments)
            topic_blocks = generate_topics_summaries_timestamps(transcript_text)
        else:
            transcript_text = "Transcript not available."
            topic_blocks = []

       
        parsed_blocks = []
        for block in topic_blocks:
            cleaned_block = block.replace("**", "").strip()
            print("Cleaned block:")
            print(cleaned_block)

            if "Topic:" in cleaned_block and "Summary:" in cleaned_block and "Timestamp:" in cleaned_block:
                try:
                    topic_str = cleaned_block.split("Topic:")[1].split("Summary:")[0].strip()
                    raw_summary = cleaned_block.split("Summary:")[1].split("Timestamp:")[0].strip()
                    timestamp_str = cleaned_block.split("Timestamp:")[1].strip()

                    
                    complete_summary = get_complete_sentence(raw_summary)

                    
                    start_sec, end_sec = parse_timestamp_to_seconds(timestamp_str)
                    if start_sec is None or end_sec is None:
                        # If we can't parse, skip this block
                        continue
                    duration = end_sec - start_sec if end_sec > start_sec else 0

                    parsed_blocks.append({
                        "topic": topic_str,
                        "summary": complete_summary,
                        "orig_start": start_sec,
                        "orig_end": end_sec,
                        "duration": duration
                    })

                except Exception as parse_err:
                    print(f"Error parsing cleaned block: {cleaned_block}")
                    print(parse_err)
            else:
                print("Block does not contain all required elements. Skipping.")

        
        parsed_blocks.sort(key=lambda x: x["orig_start"])

        current_start = 0
        for pb in parsed_blocks:
            pb["new_start"] = current_start
            pb["new_end"] = current_start + pb["duration"]
            current_start = pb["new_end"]
        
        txt_file_lines = [
            f"Video ID: {video_id}",
            f"Video Title: {analytics['title']}",
            "-" * 60
        ]

       
        for pb in parsed_blocks:
            new_start_str = seconds_to_hhmmss(pb["new_start"])
            new_end_str = seconds_to_hhmmss(pb["new_end"])
            new_timestamp_str = f"{new_start_str} - {new_end_str}"

            # Save to CSV data
            output_data.append({
                "Video Title": analytics["title"],
                "Video Link": f"https://www.youtube.com/watch?v={video_id}",
                "Transcript": transcript_text,
                "Topic": pb["topic"],
                "Summary": pb["summary"],
                "Time Stamp": new_timestamp_str,
                "Published At": analytics["publishedAt"],
                "View Count": analytics["viewCount"],
                "Like Count": analytics["likeCount"],
                "Comment Count": analytics["commentCount"]
            })

            
            txt_file_lines.append(f"Topic: {pb['topic']}")
            txt_file_lines.append(f"Summary: {pb['summary']}")
            txt_file_lines.append(f"Timestamp: {new_timestamp_str}")
            txt_file_lines.append("")

        
        txt_file_path = os.path.join("topic_summaries", f"{video_id}.txt")
        with open(txt_file_path, "w", encoding="utf-8") as f:
            for line in txt_file_lines:
                f.write(line + "\n")

        time.sleep(DELAY_BETWEEN_VIDEOS)

    return output_data

def main():
    output_rows = process_video_data()
    if not output_rows:
        print("No data to save.")
        return

    # Create the final CSV
    output_df = pd.DataFrame(output_rows, columns=[
        "Video Title", "Video Link", "Transcript",
        "Topic", "Summary", "Time Stamp",
        "Published At", "View Count", "Like Count", "Comment Count"
    ])
    output_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Processing complete. Results saved to {OUTPUT_CSV}")
    print("✅ Individual topic-summary files are saved in the 'topic_summaries' folder.")

if __name__ == "__main__":
    main()
