import http.client
import urllib.parse
import json
import time
import sys
import io
import os
import random
from datetime import datetime
from dotenv import load_dotenv

# Set the standard output to handle UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Define your access token, Facebook account ID, and the video details
# Get All required Tokens and Ids,
load_dotenv()
ACCOUNT_ID = os.getenv('FACEBOOK_ACCOUNT_ID')
BASE_URL = os.getenv('FACEBOOK_BASE_URL')
RENDER_BASE_IMAGE_URL = os.getenv('RENDER_BASE_IMAGE_URL')
APP_ID = os.getenv('APP_ID')
APP_SECRET = os.getenv('APP_SECRET')
ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN')
API_VERSION = os.getenv('API_VERSION')
GEMINI_FACEBOOK_IMAGE_VIDEO_KEY = os.getenv('GEMINI_FACEBOOK_IMAGE_VIDEO_KEY')

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
    """Initialize the HTTP connection to Instagram Graph API."""
    return http.client.HTTPSConnection(BASE_URL)

def get_gemini_caption(prompt):
    """
    Uses OpenRouter API to generate text based on the input prompt.
    Returns the generated text as a string.
    """
    conn = http.client.HTTPSConnection("openrouter.ai")
    headers = {
        "Authorization": f"Bearer {GEMINI_FACEBOOK_IMAGE_VIDEO_KEY}",
        "Content-Type": "application/json",
    }
    payload = json.dumps({
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    })

    conn.request("POST", "/api/v1/chat/completions", body=payload, headers=headers)
    response = conn.getresponse()
    if response.status == 200:
        result = json.loads(response.read().decode("utf-8"))
        try:
            return result["choices"][0]["message"]["content"]
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
    env_file = "THREADS/.env"
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

def get_image_urls_for_day(counter, max_attempts=20):
    """
    Returns a list of valid image URLs for a given day.
    Stops when an image is not found or max_attempts is reached.
    """
    urls = []
    for idx in range(1, max_attempts + 1):
        url = f"{RENDER_BASE_IMAGE_URL}/{counter}_{idx}.png"
        parsed_url = urllib.parse.urlparse(url)
        conn = http.client.HTTPSConnection(parsed_url.netloc)
        conn.request("HEAD", parsed_url.path)
        response = conn.getresponse()
        if response.status == 200:
            urls.append(url)
        else:
            break
    return urls

def publish_post(conn, message, link=None, published=True):
    endpoint = f"/{API_VERSION}/{ACCOUNT_ID}/feed"
    payload = {
        "message": message,
        "access_token": ACCESS_TOKEN,
        "published": str(published).lower()
    }
    if link:
        payload["link"] = link

    headers = {
        "Content-Type": "application/json"
    }

    conn.request("POST", endpoint, body=json.dumps(payload), headers=headers)
    response = conn.getresponse()
    if response.status == 200:
        print("Text published successfully:", json.loads(response.read().decode("utf-8")))
    else:
        print("Failed to publish text:", json.loads(response.read().decode("utf-8")))

def publish_post_with_images(conn, message, image_urls, published=True):
    """
    Publish a post with multiple images.
    :param conn: HTTP connection object
    :param message: The text message for the post
    :param image_urls: List of image URLs to include in the post
    :param published: Whether the post should be published immediately
    """
    # Step 1: Upload each image and collect their IDs
    photo_ids = []
    for image_url in image_urls:
        endpoint = f"/{API_VERSION}/{ACCOUNT_ID}/photos"
        payload = {
            "url": image_url,
            "access_token": ACCESS_TOKEN,
            "published": "false"  # Upload but don't publish yet
        }
        headers = {
            "Content-Type": "application/json"
        }
        conn.request("POST", endpoint, body=json.dumps(payload), headers=headers)
        response = conn.getresponse()
        if response.status == 200:
            result = json.loads(response.read().decode("utf-8"))
            photo_ids.append(result["id"])  # Collect the photo ID
        else:
            print("Failed to upload image:", json.loads(response.read().decode("utf-8")))

    # Step 2: Create a post referencing the uploaded images
    if photo_ids:
        endpoint = f"/{API_VERSION}/{ACCOUNT_ID}/feed"
        payload = {
            "message": message,
            "attached_media": [{"media_fbid": photo_id} for photo_id in photo_ids],
            "access_token": ACCESS_TOKEN,
            "published": str(published).lower()
        }
        headers = {
            "Content-Type": "application/json"
        }
        conn.request("POST", endpoint, body=json.dumps(payload), headers=headers)
        response = conn.getresponse()
        if response.status == 200:
            print("Post published successfully:", json.loads(response.read().decode("utf-8")))
        else:
            print("Failed to publish post:", json.loads(response.read().decode("utf-8")))
    else:
        print("No images were uploaded. Post not created.")

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
        
# Example usage
if __name__ == "__main__":
 
    # Define a file to store the counter
    counter_file = 'counter_image.txt'
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

    image_urls = get_image_urls_for_day(counter)
    print("Image URLs for the day:", image_urls)

    conn = initialize_connection()
    
    # Check and refresh access token before proceeding
    print("ACCESS TOKEN = ",ACCESS_TOKEN)
    check_access_token(conn)    
    print("ACCESS TOKEN = ",ACCESS_TOKEN)
    
    try:
        publish_post_with_images(conn, caption, image_urls)
    except Exception as e:
        print("❌ Failed to publish images:", e)

    conn.close()