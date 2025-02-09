import os
import time
import pandas as pd
from googleapiclient.discovery import build

# ---------------------------
# Configuration & API Setup
# ---------------------------
API_KEY = 'AIzaSyCjHFSmCTKpqDswl5lxq9RfsHAb0qROxzs'  # Replace with your actual API key
INPUT_CSV = 'khan_academy_videos.csv'        # CSV with your 500 videos
OUTPUT_CSV = 'khan_academy_videos_enriched.csv'  # Output CSV with additional details

# Build the YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

# ---------------------------
# Read Existing CSV Data
# ---------------------------
df_input = pd.read_csv(INPUT_CSV)

# Assume the CSV contains a column named 'video_id' or 'id'
if 'video_id' in df_input.columns:
    video_ids = df_input['video_id'].tolist()
elif 'id' in df_input.columns:
    video_ids = df_input['id'].tolist()
else:
    raise ValueError("Input CSV must contain a 'video_id' or 'id' column.")

print(f"Found {len(video_ids)} video IDs.")

# ---------------------------
# Function to Enrich Video Details
# ---------------------------
def fetch_video_details(video_id_batch):
    """
    Fetch detailed information for a batch of video IDs.
    Returns a list of dictionaries with enriched video details.
    """
    try:
        request = youtube.videos().list(
            part="snippet,statistics,contentDetails,topicDetails,recordingDetails,status",
            id=",".join(video_id_batch)
        )
        response = request.execute()
    except Exception as e:
        print(f"Error during API call: {e}")
        return []
    
    details_list = []
    for item in response.get('items', []):
        video_data = {}
        video_data['video_id'] = item.get('id')
        
        # --- Snippet Information ---
        snippet = item.get('snippet', {})
        video_data['title'] = snippet.get('title')
        video_data['description'] = snippet.get('description')
        video_data['publishedAt'] = snippet.get('publishedAt')
        video_data['channelId'] = snippet.get('channelId')
        video_data['channelTitle'] = snippet.get('channelTitle')
        video_data['tags'] = ", ".join(snippet.get('tags', [])) if snippet.get('tags') else None
        video_data['categoryId'] = snippet.get('categoryId')
        video_data['defaultLanguage'] = snippet.get('defaultLanguage')
        video_data['localized_title'] = snippet.get('localized', {}).get('title')
        video_data['localized_description'] = snippet.get('localized', {}).get('description')
        
        # --- Statistics ---
        statistics = item.get('statistics', {})
        video_data['viewCount'] = statistics.get('viewCount')
        video_data['likeCount'] = statistics.get('likeCount')
        video_data['dislikeCount'] = statistics.get('dislikeCount')
        video_data['commentCount'] = statistics.get('commentCount')
        video_data['favoriteCount'] = statistics.get('favoriteCount')
        
        # --- Content Details ---
        contentDetails = item.get('contentDetails', {})
        video_data['duration'] = contentDetails.get('duration')
        video_data['definition'] = contentDetails.get('definition')
        video_data['caption'] = contentDetails.get('caption')
        video_data['licensedContent'] = contentDetails.get('licensedContent')
        video_data['projection'] = contentDetails.get('projection')
        
        # --- Topic Details (if available) ---
        topicDetails = item.get('topicDetails', {})
        video_data['topicCategories'] = ", ".join(topicDetails.get('topicCategories', [])) if topicDetails.get('topicCategories') else None
        video_data['relevantTopicIds'] = ", ".join(topicDetails.get('relevantTopicIds', [])) if topicDetails.get('relevantTopicIds') else None
        
        # --- Recording Details (if available) ---
        recordingDetails = item.get('recordingDetails', {})
        video_data['locationDescription'] = recordingDetails.get('locationDescription')
        video_data['location'] = recordingDetails.get('location')  # usually a dict with latitude & longitude
        video_data['recordingDate'] = recordingDetails.get('recordingDate')
        
        # --- Status ---
        status = item.get('status', {})
        video_data['uploadStatus'] = status.get('uploadStatus')
        video_data['privacyStatus'] = status.get('privacyStatus')
        video_data['license'] = status.get('license')
        video_data['embeddable'] = status.get('embeddable')
        video_data['publicStatsViewable'] = status.get('publicStatsViewable')
        
        details_list.append(video_data)
    
    return details_list

# ---------------------------
# Process Videos in Batches
# ---------------------------
enriched_videos = []
batch_size = 50

for i in range(0, len(video_ids), batch_size):
    batch_ids = video_ids[i:i+batch_size]
    print(f"Processing batch {i} to {i+len(batch_ids)-1}...")
    batch_details = fetch_video_details(batch_ids)
    enriched_videos.extend(batch_details)
    time.sleep(1)  # Pause to respect rate limits

# ---------------------------
# Save Enriched Data to CSV
# ---------------------------
df_enriched = pd.DataFrame(enriched_videos)
df_enriched.to_csv(OUTPUT_CSV, index=False)
print(f"Enriched data for {len(df_enriched)} videos saved to {OUTPUT_CSV}.")
