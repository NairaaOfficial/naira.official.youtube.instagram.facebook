import http.client
import json
import sys
import io
import time
import os
import csv
import random
import urllib.parse
from dotenv import load_dotenv
from datetime import datetime
from moviepy import *

# Set the standard output to handle UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Define your access token, Instagram account ID, and the video details
# Get All required Tokens and Ids,
load_dotenv()
ACCOUNT_ID = os.getenv('INSTAGRAM_ACCOUNT_ID')
BASE_URL = os.getenv('INSTAGRAM_BASE_URL')
APP_ID = os.getenv('APP_ID')
APP_SECRET = os.getenv('APP_SECRET')
ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
API_VERSION = os.getenv('API_VERSION')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def initialize_connection():
    """Initialize the HTTP connection to Instagram Graph API."""
    return http.client.HTTPSConnection(BASE_URL)

def get_audio_recommendations(conn, recommendation_type="FACEBOOK_POPULAR_MUSIC", countries="IN"):
    # Define endpoint and parameters
    endpoint = f"/{API_VERSION}/audio/recommendations"
    params = urllib.parse.urlencode({
        "type": recommendation_type,
        "available_countries": countries,  # Add available_countries parameter here
        "access_token": ACCESS_TOKEN
    })

    # Make the GET request
    conn.request("GET", f"{endpoint}?{params}")
    
    # Get the response
    response = conn.getresponse()
    data = response.read().decode("utf-8")
    audio_object_response = json.loads(data)
    print("audio_object_response = ", audio_object_response)
    
    return audio_object_response

def check_access_token(conn):
    """
    Check if the current access token is valid.
    If not, refresh the token.
    """
    # global ACCESS_TOKEN  # Update global variable
    endpoint = f"/{API_VERSION}/debug_token?input_token={ACCESS_TOKEN}&access_token={ACCESS_TOKEN}"
    conn.request("GET", endpoint)
    response = conn.getresponse()
    data = json.loads(response.read().decode('utf-8'))
    print("check_access_token_response = ", data)

    expires_at = data["data"]["expires_at"]
    print("expires_at = ",data["data"]["expires_at"])  
    token_expires_one = datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')
    print("Token expires on:", token_expires_one)
    current_time = datetime.now().timestamp()  # Current timestamp in UTC
    print("current_time = ",current_time)
    remaining_days = (expires_at - current_time) / 86400  # Convert seconds to days
    print("remaining_days = ",int(remaining_days))
    
    # Check the token's validity
    if int(remaining_days) == 2:
        print("Access token is invalid or expired. Refreshing...")
        refresh_access_token(conn)
    else:
        print("Access token is valid.")

def refresh_access_token(conn):
    """Refresh the access token using the App credentials."""
    global ACCESS_TOKEN  # Update the global variable
    params = urllib.parse.urlencode({
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": ACCESS_TOKEN,
    })
    conn.request("GET", f"/{API_VERSION}/oauth/access_token?{params}")
    response = conn.getresponse()
    data = json.loads(response.read().decode("utf-8"))
    print("refresh_access_token_response = ", data)
    if 'access_token' in data:
        new_access_token = data['access_token']
        update_env_file("INSTAGRAM_ACCESS_TOKEN", new_access_token)
        print("Access token refreshed and updated in the .env file.")
        # Reload environment variables to update the token for the current session
        os.environ['INSTAGRAM_ACCESS_TOKEN'] = new_access_token
        ACCESS_TOKEN = new_access_token  # Update in-memory token
    else:
        print("Failed to refresh access token:", data.get('error', 'Unknown error'))

def update_env_file(key, value):
    """
    Updates the specified key-value pair in the .env file.
    If the key doesn't exist, it will be added.
    """
    env_file = "INSTAGRAM/.env"
    updated_lines = []
    key_found = False

    # Read the file and update the key if it exists
    if os.path.exists(env_file):
        with open(env_file, "r") as file:
            for line in file:
                if line.startswith(f"{key}="):
                    updated_lines.append(f"{key}={value}\n")
                    key_found = True
                else:
                    updated_lines.append(line)

    # If the key is not found, append it
    if not key_found:
        updated_lines.append(f"{key}={value}\n")

    # Write back the updated content to the file
    with open(env_file, "w") as file:
        file.writelines(updated_lines)
    print(f"Updated {key} in .env file.")

def create_story_media_object(conn):
    """Create a media object for a Story."""
    endpoint = f"/{API_VERSION}/{ACCOUNT_ID}/media"
    payload = {
        "media_type": "STORIES",
        "upload_type": "resumable",
        "access_token": ACCESS_TOKEN
    }

    headers = {"Content-Type": "application/json"}
    conn.request("POST", endpoint, json.dumps(payload), headers)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    story_response = json.loads(data)
    print("story_response = ", story_response)
    if "id" in story_response:
        print("Media object created with ID:", story_response["id"])
        return story_response["id"], story_response["uri"]
    else:
        print("Error creating media object:", story_response)
        return None, None

def upload_story_media(conn, upload_uri, video):
    """Upload the video to the given upload URI."""
    file_size = os.path.getsize(video)
    print("Video file size:", file_size)

    # Set up the headers
    headers = {
        "Authorization": f"OAuth {ACCESS_TOKEN}",
        "offset": "0",
        "file_size": str(file_size),
        "Content-Length": str(file_size)
    }

    # Open the video file in binary mode and upload
    max_retries = 5
    for retry in range(1, max_retries + 1):
        with open(video, 'rb') as video_file:
            conn.request("POST", upload_uri, body=video_file, headers=headers)
            
            # Get the response
            response = conn.getresponse()
            data = response.read().decode('utf-8')

            try:
                upload_media_response = json.loads(data)
            except json.JSONDecodeError:
                print("Error decoding JSON response, retrying...")
                time.sleep(10)
                continue
            
            print("upload_media_response = ", upload_media_response)

            # Handle response conditions
            debug_info = upload_media_response.get('debug_info', {})
            if debug_info.get('type') == 'ProcessingFailedError' and 'Request processing failed' in debug_info.get('message', ''):
                print(f"Processing failed, retrying... ({retry}/{max_retries})")
                time.sleep(10)
                continue
            elif 'Upload Successful.' in upload_media_response.get('message', ''):
                print("Upload successful.")
                break
            else:
                print("Unexpected response, retrying...")
                time.sleep(10)
    else:
        print("Max retries reached. Upload failed.")

def check_media_status(conn, media_id):
    """Check the status of the media object to see if it is ready for publishing."""
    endpoint = f"/{API_VERSION}/{media_id}?fields=id,status,status_code,video_status"
    # Set up the headers
    headers = {
        "Authorization": f"OAuth {ACCESS_TOKEN}"
    }
    conn.request("GET", endpoint,"",headers)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    media_status = json.loads(data)

    print("Media status response:", media_status)
    return media_status.get("status_code"), media_status.get("video_status")

def publish_story_media_object(conn, media_id):
    """Publish the media object if it is ready."""
    endpoint = f"/{API_VERSION}/{ACCOUNT_ID}/media_publish"
    payload = {
        "creation_id": media_id,
        "access_token": ACCESS_TOKEN
    }

    headers = {"Content-Type": "application/json"}
    conn.request("POST", endpoint, json.dumps(payload), headers)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    publish_result = json.loads(data)

    if "id" in publish_result:
        print("Reel published successfully with ID:", publish_result["id"])
    else:
        print("Error publishing reel:", json.dumps(publish_result, ensure_ascii=False))

def read_counter(counter_file):
    """Read the current counter value from the file, or initialize it."""
    if os.path.exists(counter_file):
        with open(counter_file, 'r') as file:
            return int(file.read())
    return 0

def main():
   
    # Define a file to store the counter
    counter_file = 'counter.txt'    
    reel_number = read_counter(counter_file)
    # Execute the code
    print(f"Reel Number : {reel_number}")
    
    video = f"STORY_TO_UPLOAD/story_{reel_number}.mp4"  # Link to the video file (must be accessible)
    # Trim the video to less than 60 seconds before uploading

    if os.path.exists(video):
        with VideoFileClip(video) as clip:
            if clip.duration > 60:
                trimmed_video = f"REEL_TO_UPLOAD/reel_{reel_number}_trimmed.mp4"
                clip.subclipped(0, 55).write_videofile(trimmed_video, codec="libx264", audio_codec="aac")
                video = trimmed_video

    conn = initialize_connection()
    
    # Check and refresh access token before proceeding
    print("ACCESS TOKEN = ",ACCESS_TOKEN)
    check_access_token(conn)    
    print("ACCESS TOKEN = ",ACCESS_TOKEN)
    
    # Step 1: Create the media object
    response = get_audio_recommendations(conn)
    media_object_id,upload_uri = create_story_media_object(conn)
    if not media_object_id:
        return  # Exit if media object creation fails
    
    # Step 2: Upload the media object
    upload_story_media(conn,upload_uri,video)

    # Step 3: Check upload media status until it's ready
    max_retries = 10
    for retry in range(1,max_retries + 1):
        status_code, status = check_media_status(conn, media_object_id)
        print("Checking Upload Status Time = ", retry)
        print("Checking Upload Status Code = ",status_code)
        print("Checking Upload Status = ",status)
        if status_code == 'FINISHED' and status['uploading_phase']['status'] == 'complete':
            break
        time.sleep(60)
    
    # Step 4: Publish the media if ready    
    publish_story_media_object(conn, media_object_id)

    # Step 5: Check the published media status.
    max_retries = 10
    for retry in range(1,max_retries + 1):
        status_code, status = check_media_status(conn, media_object_id)
        print("Checking Publishing Status Time = ", retry)
        print("Checking Publishing Status Code = ",status_code)
        print("Checking Publishing Status = ",status)
        if status_code == 'PUBLISHED':
            break
        time.sleep(60)
    
    conn.close()
    
if __name__ == "__main__":
    main()
