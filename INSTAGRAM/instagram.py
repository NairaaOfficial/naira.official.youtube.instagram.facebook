import http.client
import json
import sys
import io
import time
import os
import random
import urllib.parse
from dotenv import load_dotenv
from datetime import datetime
import requests

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

def create_media_object(conn, caption):
    """Create a media object for a reel."""
    endpoint = f"/{API_VERSION}/{ACCOUNT_ID}/media"
    payload = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "thumb_offset": random.randint(2,7),
        "audio_name": "nairaaa.official",
        "share_to_feed": True,
        "access_token": ACCESS_TOKEN
    }
    
    headers = {"Content-Type": "application/json"}
    conn.request("POST", endpoint, json.dumps(payload), headers)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    media_object_response = json.loads(data)
    print("media_object_response = ", media_object_response)
    if "id" in media_object_response:
        print("Media object created with ID:", media_object_response["id"])
        return media_object_response["id"], media_object_response["uri"]
    else:
        print("Error creating media object:", media_object_response)
        return None, None

def upload_media(conn, upload_uri, video):
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

def publish_media_object(conn, media_id):
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

def read_caption(caption_file):
    print (caption_file)
    try:
        with open(caption_file, "r", encoding="utf-8") as file:
            caption = file.read()
        return caption
    except FileNotFoundError:
        return "Caption file not found."
    except Exception as e:
        return f"An error occurred: {e}"

def gemini_generate_text(prompt):
    """
    Uses Google Gemini API to generate text based on the input prompt.
    Returns the generated text as a string.
    """
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    params = {"key": GEMINI_API_KEY}
    response = requests.post(url, headers=headers, params=params, json=payload)
    if response.status_code == 200:
        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return "No output from Gemini API."
    else:
        return f"Error: {response.status_code} - {response.text}"

def main():
   
    # Define a file to store the counter
    counter_file = 'counter.txt'    
    reel_number = read_counter(counter_file)
    # Execute the code
    print(f"Reel Number : {reel_number}")
    
    video = f"REEL_TO_UPLOAD/reel_{reel_number}.mp4"  # Link to the video file (must be accessible)
    caption_file = 'INSTAGRAM/caption.txt'
    caption_part2 = read_caption(caption_file)
    prompt = (
        f"Write ONE single Instagram caption for a female influencer (max 500 characters) that is engaging, fun, and emotionally appealing.\n"
        "The caption must:\n"
        "- Be in English.\n"
        "- Include emojis naturally.\n"
        "- End with up to 10 trending and relevant hashtags.\n"
        "- Be written in a tone that fits short-form viral content (e.g. Reels).\n"
        "- Do not describe about any landscapes or sunsets, be it only engaging with audience.\n"
        "- Example 1 - Everything is perfect...but it would have been better if you were with me ❤️\n"
        "- Example 2 - Not every queen wears a crown — some wear calm 🙂 \n"
        "- Example 3 - On your mind yet? \n "
        "- Example 4 - Guess what I am thinking… \n"
        "- Example 5 - Just a little fiery today \n"
        "- Example 6 - Just me being me \n"
        "- Example 7 - Happy Vibes 🙂😇 \n"
        "- Example 9 - Look, but don’t blink 👀💁🏻‍♀️ \n"
        "- Example 10 - Your crush ?? 👀💁🏻‍♀️ \n"
        "- Example 11 - Dressed up for You 🫶🏻💞 \n"
        "- Example 12 - Golden Hours \n"
        "- Example 13 - Is the view distracting… or motivating? 🙄 \n"
        "- Example 14 - Careful what you wish for, you might just get it \n"
        "- Example 15 - No rush. I’m not going anywhere. 🩷 \n"
        "- Example 16 - Just a soft soul finding her way 💞 🩷 \n"
        "- Example 17 - Be patient with me… I’m still learning how to be seen. 🤷🏻‍♀️ \n"
        "- Example 18 - I called you, are you coming? ✨🤨🤭 \n"
        "- Example 19 - I see you 👀👀 \n"
        "- Example 20 - I smile when I read your replies. Don’t tell anyone. 🤫🙃 \n"
        "- Example 21 - Can I be Your Crush 🤗😻 \n"
        "- Example 22 - No Botox, no filter, no surgery—just me in my most Feminine 🤍🤍 \n"
        "STRICT RULE: Do NOT include any introductions, explanations, or say anything like 'here is your caption'. Output ONLY the caption text — nothing else."
    )
    caption_part1 = gemini_generate_text(prompt)
    caption = caption_part1 + caption_part2
    print(f"Caption : {caption}")
    conn = initialize_connection()
    
    # Check and refresh access token before proceeding
    print("ACCESS TOKEN = ",ACCESS_TOKEN)
    check_access_token(conn)    
    print("ACCESS TOKEN = ",ACCESS_TOKEN)
    
    # Step 1: Create the media object
    response = get_audio_recommendations(conn)
    media_object_id,upload_uri = create_media_object(conn, caption)
    if not media_object_id:
        return  # Exit if media object creation fails
    
    # Step 2: Upload the media object
    upload_media(conn,upload_uri,video)

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
    publish_media_object(conn, media_object_id)

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
