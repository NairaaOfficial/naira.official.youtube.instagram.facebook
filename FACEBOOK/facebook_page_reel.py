import http.client
import json
import sys
import io
import time
import os
import random
import urllib.parse
from datetime import datetime
import requests

# Set the standard output to handle UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Define your access token, Facebook account ID, and the video details
# Get All required Tokens and Ids,
ACCOUNT_ID = os.environ['FACEBOOK_ACCOUNT_ID']
BASE_URL = os.environ['FACEBOOK_BASE_URL']
APP_ID = os.environ['APP_ID']
APP_SECRET = os.environ['APP_SECRET']
ACCESS_TOKEN = os.environ['FACEBOOK_ACCESS_TOKEN']
API_VERSION = os.environ['API_VERSION']
RENDER_BASE_VIDEO_URL = os.environ['RENDER_BASE_VIDEO_URL']
GEMINI_IMAGE_VIDEO_CAPTION_KEY = os.environ['GEMINI_IMAGE_VIDEO_CAPTION_KEY']

DEFAULT_TEXT = [
    "Would you rather cuddle all night or steal kisses all day? 😘",
    "Guess what I’m wearing right now… or should I just show you? 👀",
    "Be honest: You like it naughty or nice? 😏",
    "Just got out of the shower… feeling cute 🫣",
    "Who wants to help me pick tonight’s lingerie? 👀",
    "My DMs are getting wild lately… should I share a peek? 😜",
    "Is it a red flag if a guy doesn’t text back within an hour? 🤔",
    "Big chest or big heart? Be honest! ❤️",
    "Lace or leather tonight? What’s your vibe? 😈",
    "Woke up feeling like trouble today… who’s joining me? 😈",
    "Good night babes… or should I say bad night? 😏",
    "Morning kisses or midnight cuddles? What’s your pick? 🌙",
    "I have a secret… but I need 10 likes to tell 👀",
    "Last night’s dream was NOT safe for work… should I share? 😜",
    "I might have a crush on someone here… guess who? 😘",
    "If I were your naughty secretary… what would you make me do? 😏",
    "POV: You walk in and see me in your shirt… what happens next? 😘",
    "Let’s play pretend: I’m the boss, and you’re late to work… explain yourself. 😈",
    "Finish this: If we were on a date, I’d… 💕",
    "Use 3 emojis to describe me… I dare you! 😘",
    "What’s the first thing you’d say if we met in person? 😏",
    "Truth or dare in comments? Let’s play! 😈",
    "First one to comment gets a personal question 👄",
    "I dare you to DM me your wildest fantasy… who’s brave enough? 😜",
    "Would you rather be kissed under the stars or in the rain? 🌧️✨",
    "Guess what color my nails are today… or should I just show you? 💅",
    "Naughty or nice? Which side of me do you want to see tonight? 😘",
    "Just slipped into something comfy… or maybe not. 🫣",
    "Who’s up for a late-night chat? My DMs are open… for now. 👀",
    "Is it a dealbreaker if someone doesn’t like cuddles? 🤔",
    "Big smile or big hugs? What’s more important? ❤️",
    "Satin or silk tonight? What’s your choice? 😈",
    "Woke up feeling like a queen today… who’s my king? 👑",
    "Sweet dreams, or should I say spicy dreams? 😏",
    "Morning coffee or morning kisses? What’s your vibe? ☕😘",
    "I have a confession… but I need 20 comments to spill it. 👀",
    "Last night’s thoughts were a little too wild… should I share? 😜",
    "I might have a favorite follower… guess who? 😘",
    "If I were your personal trainer… how would you behave? 😏",
    "POV: You catch me stealing your hoodie… what do you do? 😘",
    "Let’s imagine: I’m the teacher, and you’re the naughty student… explain yourself. 😈",
    "Finish this: If we were stuck on an island, I’d… 💕",
    "Use 3 words to describe me… I dare you! 😘",
    "What’s the first thing you’d do if we met in real life? 😏",
    "Truth or dare: Tell me your biggest secret in the comments. 😈",
    "First one to reply gets a flirty DM… who’s in? 👄",
    "I dare you to send me your favorite emoji… let’s see who’s bold. 😜"
]

def initialize_connection():
    """Initialize the HTTP connection to Facebook Graph API."""
    return http.client.HTTPSConnection(BASE_URL)

def get_gemini_caption(prompt):
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
    params = {"key": GEMINI_IMAGE_VIDEO_CAPTION_KEY}
    response = requests.post(url, headers=headers, params=params, json=payload)
    if response.status_code == 200:
        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return random.choice(DEFAULT_TEXT)
    else:
        return random.choice(DEFAULT_TEXT)

def filter_generated_text(text):
    """
    Filters the generated text to remove any unwanted content, such as special characters like * or **.
    """
    # Remove all occurrences of * and ** from the text
    filtered_text = text.replace("*", "")
    filtered_text = filtered_text.replace("\"", "")
    return filtered_text

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
        update_env_file("FACEBOOK_ACCESS_TOKEN", new_access_token)
        print("Access token refreshed and updated in the .env file.")
        # Reload environment variables to update the token for the current session
        os.environ['FACEBOOK_ACCESS_TOKEN'] = new_access_token
        ACCESS_TOKEN = new_access_token  # Update in-memory token
    else:
        print("Failed to refresh access token:", data.get('error', 'Unknown error'))

def update_env_file(key, value):
    """
    Updates the specified key-value pair in the .env file.
    If the key doesn't exist, it will be added.
    """
    env_file = "FACEBOOK/.env"
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

def get_video_url_for_day(counter):
    """
    Returns a valid video URL for a given day.
    Stops when a video is not found or max_attempts is reached.
    """
    
    url = f"{RENDER_BASE_VIDEO_URL}/Video_{counter}.mp4"
    parsed_url = urllib.parse.urlparse(url)
    conn = http.client.HTTPSConnection(parsed_url.netloc)
    conn.request("HEAD", parsed_url.path)
    response = conn.getresponse()
    if response.status == 200:
        return url
    else:
        return None
    
def create_media_object(conn):
    """Create a media object for a reel."""
    endpoint = f"/{API_VERSION}/{ACCOUNT_ID}/video_reels"
    payload = {
        "upload_phase":"start",
        "access_token": ACCESS_TOKEN
    }
    
    headers = {"Content-Type": "application/json"}
    conn.request("POST", endpoint, json.dumps(payload), headers)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    media_object_response = json.loads(data)
    print("media_object_response = ", media_object_response)
    if "video_id" in media_object_response:
        print("Media object created with ID:", media_object_response["video_id"])
        return media_object_response["video_id"],media_object_response["upload_url"]
    else:
        print("Error creating media object:", media_object_response)
        return None, None

def upload_media(conn, upload_uri, video_url):
    """Upload the video to the given upload URI."""

    # Set up the headers
    headers = {
        "Authorization": f"OAuth {ACCESS_TOKEN}",
        "file_url": video_url
    }

    # Open the video file in binary mode and upload
    max_retries = 5
    for retry in range(1, max_retries + 1):
        conn.request("POST", upload_uri, headers=headers)

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
    endpoint = f"/{API_VERSION}/{media_id}?fields=id,status"
    # Set up the headers
    headers = {
        "Authorization": f"OAuth {ACCESS_TOKEN}"
    }
    conn.request("GET", endpoint,"",headers)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    media_status = json.loads(data)

    print("Media status response:", media_status)
    return media_status.get("status")

def publish_media_object(conn, media_id, caption):
    """Publish the media object if it is ready."""
    endpoint = f"/{API_VERSION}/{ACCOUNT_ID}/video_reels"
    payload = {
        "video_id": media_id,
        "upload_phase":"finish",
        "video_state":"PUBLISHED",
        "description":caption,
        "title":"nairaa.babe",
        "access_token": ACCESS_TOKEN
    }

    headers = {"Content-Type": "application/json"}
    conn.request("POST", endpoint, json.dumps(payload), headers)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    publish_result = json.loads(data)
    
    print("publish_result = ", publish_result)
    if "post_id" in publish_result:
        print("Reel published successfully with ID:", publish_result["post_id"])
    else:
        print("Error publishing reel:", json.dumps(publish_result, ensure_ascii=False))

def read_prompt(prompt_file):
    print (prompt_file)
    try:
        with open(prompt_file, "r", encoding="utf-8") as file:
            prompt = file.read()
        return prompt
    except FileNotFoundError:
        return "prompt file not found."
    except Exception as e:
        return f"An error occurred: {e}"
    
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

def main():
   
    # Define a file to store the counter
    counter_file = 'counter_video.txt'
    counter = read_counter(counter_file)
    # Execute the code
    print(f"Counter : {counter}")
    
    caption_file = 'FACEBOOK/caption.txt'
    prompt_file = 'FACEBOOK/prompt_image_video.txt'
    user_prompt = read_prompt(prompt_file)
    caption_part1 = get_gemini_caption(user_prompt)
    print("Generated Text:", caption_part1)
    caption_part1 = filter_generated_text(caption_part1)
    caption_part2 = read_caption(caption_file)
    
    caption = caption_part1 + caption_part2
    print(f"Caption : {caption}")

    video_url = get_video_url_for_day(counter)
    print("Video URL for the day:", video_url)

    conn = initialize_connection()
    
    # Check and refresh access token before proceeding
    print("ACCESS TOKEN = ",ACCESS_TOKEN)
    check_access_token(conn)    
    print("ACCESS TOKEN = ",ACCESS_TOKEN)
    
    # Step 1: Create the media object
    response = get_audio_recommendations(conn)
    media_object_id,upload_uri = create_media_object(conn)
    if not media_object_id:
        return  # Exit if media object creation fails
    
    # Step 2: Upload the media object
    upload_media(conn,upload_uri,video_url)

    # Step 3: Check upload media status until it's ready
    max_retries = 10
    for retry in range(1,max_retries + 1):
        status = check_media_status(conn, media_object_id)
        print("Checking Upload Status Time = ", retry)
        print("Checking Upload Status = ",status)
        if status['uploading_phase']['status'] == 'complete' and status['video_status'] == 'upload_complete':
            break
        time.sleep(60)
    
    # Step 4: Publish the media if ready    
    publish_media_object(conn, media_object_id, caption)

    # Step 5: Check the published media status.
    max_retries = 10
    for retry in range(1,max_retries + 1):
        status = check_media_status(conn, media_object_id)
        print("Checking Publishing Status Time = ", retry)
        print("Checking Publishing Status = ",status)
        if status['publishing_phase']['status'] == 'complete' and status['publishing_phase']['publish_status'] == 'published':
            break
        time.sleep(60)
    
    conn.close()
    
if __name__ == "__main__":
    main()
