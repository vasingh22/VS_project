
#This script was used for downloading the data from Khan Academy and Saving it in the CSV file and Videos to videos folder

import os
import pandas as pd
import yt_dlp

def download_videos_from_csv(csv_file):
    
    os.makedirs("videos", exist_ok=True)
    
    df = pd.read_csv(csv_file)

    for index, row in df.iterrows():
        if "Video Link" not in row or pd.isna(row["Video Link"]):
            print(f"Row {index} is missing a 'Video Link' value. Skipping.")
            continue
        
        video_link = row["Video Link"]
        if "youtube.com/watch?v=" not in video_link:
            print(f"Skipping invalid YouTube link in row {index}: {video_link}")
            continue
    
        ydl_opts = {
            'outtmpl': 'videos/%(id)s.%(ext)s',
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                print(f"Downloading video: {video_link}")
                info = ydl.extract_info(video_link, download=False)
            
                video_id = info.get("id", "unknown_id")
                video_ext = info.get("ext", "mp4")  # The detected or chosen extension
                output_path = os.path.join("videos", f"{video_id}.{video_ext}")

                
                if os.path.exists(output_path):
                    print(f"Video {video_id} already downloaded at {output_path}. Skipping.")
                    continue

              
                ydl.download([video_link])
                print(f"Downloaded {video_id}.{video_ext} successfully.")
            except Exception as e:
                print(f"Failed to download {video_link}: {e}")

    print("All downloads attempted.")

if __name__ == "__main__":
    CSV_FILE_PATH = "output_topics_summaries.csv"
    download_videos_from_csv(CSV_FILE_PATH)
