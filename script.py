#!/usr/bin/env python3
"""
This script fetches a variety of data from a YouTube channel using the YouTube Data API.
Data collected include:

1. **Channel Data:**
   - Channel ID, Name, Description, Published Date.
   - Subscriber Count, Total Views, and Video Count.

2. **Video Data (from the channel's uploads):**
   - Basic Information: Video ID, Title, Description, Published Date, Thumbnails, Tags, Category ID.
   - Engagement Metrics: View Count, Like Count, Comment Count.
   - Content Details: Duration, Definition, Dimension, Caption Availability, Licensed Content.

3. **Playlist Data:**
   - For each playlist: Playlist ID, Title, Description, and Item Count.
   - Playlist Items: Video IDs, Titles, and Published Dates for videos in each playlist.

4. **Comment Data (for a few videos for demonstration):**
   - For each comment thread: Comment text, like count, author, published date.
   - Replies (if any) are also fetched.

Each set of data is saved to its own CSV file.
"""

import csv
import json
import time
from googleapiclient.discovery import build

# Replace with your actual API key
YOUTUBE_API_KEY = "AIzaSyCjHFSmCTKpqDswl5lxq9RfsHAb0qROxzs"

# Example channel ID for Khan Academy (update as needed)
CHANNEL_ID = "UC4a-Gbdw7vOaccHmFo40b9g"


def get_service():
    """Create and return the YouTube API service object."""
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


# ===============================
# Channel Data
# ===============================
def fetch_channel_details(channel_id):
    """Fetch channel details including snippet, statistics, and contentDetails."""
    youtube = get_service()
    request = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=channel_id
    )
    response = request.execute()
    if response.get("items"):
        return response["items"][0]
    else:
        return None


def save_channel_details(channel_data, filename="channel_details.csv"):
    """Save channel details to a CSV file."""
    if channel_data is None:
        print("No channel data found.")
        return

    snippet = channel_data.get("snippet", {})
    statistics = channel_data.get("statistics", {})

    data = {
        "channel_id": channel_data.get("id"),
        "title": snippet.get("title"),
        "description": snippet.get("description"),
        "published_at": snippet.get("publishedAt"),
        "subscriber_count": statistics.get("subscriberCount"),
        "view_count": statistics.get("viewCount"),
        "video_count": statistics.get("videoCount")
    }

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        writer.writeheader()
        writer.writerow(data)
    print(f"Channel details saved to {filename}")


# ===============================
# Video Data (from Uploads)
# ===============================
def fetch_videos_from_channel_uploads(channel_id, max_videos=200):
    """
    Fetch video details from the channel's 'uploads' playlist.
    Returns a list of video details including snippet, contentDetails, and statistics.
    """
    youtube = get_service()

    # First, get the uploads playlist ID from the channel’s contentDetails
    channel_response = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()

    uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Fetch video IDs from the uploads playlist (maxResults is paginated, 50 per call)
    video_ids = []
    next_page_token = None
    while len(video_ids) < max_videos:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        for item in response.get("items", []):
            video_id = item["snippet"]["resourceId"]["videoId"]
            video_ids.append(video_id)
            if len(video_ids) >= max_videos:
                break
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    # Now fetch full details for the collected video IDs in batches (max 50 per request)
    videos = []
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(batch_ids),
            maxResults=len(batch_ids)
        )
        response = request.execute()
        videos.extend(response.get("items", []))
    return videos


def save_videos(videos, filename="videos.csv"):
    """Save video data to a CSV file."""
    fieldnames = [
        "video_id", "title", "description", "published_at",
        "thumbnails", "tags", "category_id",
        "view_count", "like_count", "comment_count",
        "duration", "definition", "dimension", "caption", "licensed_content"
    ]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for video in videos:
            snippet = video.get("snippet", {})
            content_details = video.get("contentDetails", {})
            statistics = video.get("statistics", {})

            # Save all thumbnail data as a JSON string
            thumbnails_str = json.dumps(snippet.get("thumbnails", {}))

            row = {
                "video_id": video.get("id"),
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "published_at": snippet.get("publishedAt"),
                "thumbnails": thumbnails_str,
                "tags": ", ".join(snippet.get("tags", [])) if snippet.get("tags") else "",
                "category_id": snippet.get("categoryId"),
                "view_count": statistics.get("viewCount"),
                "like_count": statistics.get("likeCount"),
                "comment_count": statistics.get("commentCount"),
                "duration": content_details.get("duration"),
                "definition": content_details.get("definition"),
                "dimension": content_details.get("dimension"),
                "caption": content_details.get("caption"),
                "licensed_content": content_details.get("licensedContent")
            }
            writer.writerow(row)
    print(f"{len(videos)} videos saved to {filename}")


# ===============================
# Playlist Data
# ===============================
def fetch_playlists(channel_id):
    """Fetch all playlists for the channel."""
    youtube = get_service()
    playlists = []
    next_page_token = None
    while True:
        request = youtube.playlists().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        playlists.extend(response.get("items", []))
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    return playlists


def save_playlists(playlists, filename="playlists.csv"):
    """Save playlist data to a CSV file."""
    fieldnames = ["playlist_id", "title", "description", "item_count"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for pl in playlists:
            snippet = pl.get("snippet", {})
            content_details = pl.get("contentDetails", {})
            row = {
                "playlist_id": pl.get("id"),
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "item_count": content_details.get("itemCount")
            }
            writer.writerow(row)
    print(f"{len(playlists)} playlists saved to {filename}")


def fetch_playlist_items(playlist_id):
    """
    Fetch all items (videos) within a given playlist.
    Returns a list of items (each contains snippet details).
    """
    youtube = get_service()
    items = []
    next_page_token = None
    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        items.extend(response.get("items", []))
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    return items


def save_playlist_items(playlist_items, filename="playlist_items.csv"):
    """Save playlist item data to a CSV file."""
    fieldnames = ["playlist_id", "video_id", "video_title", "published_at"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in playlist_items:
            snippet = item.get("snippet", {})
            writer.writerow({
                "playlist_id": snippet.get("playlistId"),
                "video_id": snippet.get("resourceId", {}).get("videoId"),
                "video_title": snippet.get("title"),
                "published_at": snippet.get("publishedAt")
            })
    print(f"{len(playlist_items)} playlist items saved to {filename}")


# ===============================
# Comment Data
# ===============================
def fetch_video_comments(video_id, max_comments=100):
    """
    Fetch up to max_comments for a given video.
    Returns a list of comment threads.
    """
    youtube = get_service()
    comments = []
    next_page_token = None
    while len(comments) < max_comments:
        try:
            request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat="plainText"
            )
            response = request.execute()
        except Exception as e:
            print(f"Error fetching comments for video {video_id}: {e}")
            break

        comments.extend(response.get("items", []))
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    return comments


def save_comments(comments_data, filename="comments.csv"):
    """
    Save comment threads to a CSV file.
    Each row includes:
      - video_id, comment_id, parent_id (if reply), author, comment_text, like_count, published_at, is_reply (0 for top-level, 1 for reply)
    """
    fieldnames = [
        "video_id", "comment_id", "parent_id", "author",
        "comment_text", "like_count", "published_at", "is_reply"
    ]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for thread in comments_data:
            snippet = thread.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
            # Some comment threads include the video ID in the snippet; if not, you may pass it from your code.
            video_id = thread.get("snippet", {}).get("videoId", "")
            row = {
                "video_id": video_id,
                "comment_id": thread.get("id"),
                "parent_id": "",  # Top-level comment
                "author": snippet.get("authorDisplayName"),
                "comment_text": snippet.get("textDisplay"),
                "like_count": snippet.get("likeCount"),
                "published_at": snippet.get("publishedAt"),
                "is_reply": 0
            }
            writer.writerow(row)

            # Process any replies to the top-level comment
            replies = thread.get("replies", {}).get("comments", [])
            for reply in replies:
                r_snippet = reply.get("snippet", {})
                row = {
                    "video_id": video_id,
                    "comment_id": reply.get("id"),
                    "parent_id": thread.get("id"),
                    "author": r_snippet.get("authorDisplayName"),
                    "comment_text": r_snippet.get("textDisplay"),
                    "like_count": r_snippet.get("likeCount"),
                    "published_at": r_snippet.get("publishedAt"),
                    "is_reply": 1
                }
                writer.writerow(row)
    print(f"Comments saved to {filename}")


# ===============================
# Main Execution
# ===============================
def main():
    # ----- Channel Details -----
    print("Fetching channel details...")
    channel_data = fetch_channel_details(CHANNEL_ID)
    save_channel_details(channel_data)

    # ----- Video Data -----
    print("Fetching video details from channel uploads...")
    videos = fetch_videos_from_channel_uploads(CHANNEL_ID, max_videos=200)
    save_videos(videos)

    # ----- Playlist Data -----
    print("Fetching playlists...")
    playlists = fetch_playlists(CHANNEL_ID)
    save_playlists(playlists)

    # For each playlist, fetch its items and accumulate them
    all_playlist_items = []
    for pl in playlists:
        pl_id = pl.get("id")
        print(f"Fetching items for playlist {pl_id} ...")
        items = fetch_playlist_items(pl_id)
        all_playlist_items.extend(items)
        time.sleep(1)  # slight pause to be polite with API quota
    save_playlist_items(all_playlist_items)

    # ----- Comments -----
    # For demonstration purposes, fetch comments for the first 5 videos only.
    all_comments = []
    for video in videos[:5]:
        video_id = video.get("id")
        print(f"Fetching comments for video {video_id} ...")
        comments = fetch_video_comments(video_id, max_comments=50)
        # If the API did not return the videoId in the comment thread snippet, you could add it here.
        for thread in comments:
            if not thread.get("snippet", {}).get("videoId"):
                thread["snippet"]["videoId"] = video_id
        all_comments.extend(comments)
        time.sleep(1)
    save_comments(all_comments)


if __name__ == "__main__":
    main()
