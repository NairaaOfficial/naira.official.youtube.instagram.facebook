#!/usr/bin/python

import http.client
import httplib2
import os
import random
import sys
import time
import json
import requests

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

titles = [
    "From Nothing to Something: Watch It Built from Scratch! #shorts",
    "How It’s Made from Scratch: You Won’t Believe the Process! #shorts",
    "The Art of Building from Scratch – Subscribe for More! #shorts",
    "Creating Masterpieces from Scratch – Like and Watch! #shorts",
    "Want to See It Built? Hit Like and Watch Now! #shorts",
    "From Raw Materials to Perfection: Built from Scratch! #shorts",
    "Mind-Blowing Build! Watch It Made from Scratch – Follow! #shorts",
    "Witness the Magic: Built from Scratch – Like and Subscribe! #shorts",
    "Can You Guess How This is Made? Built from Scratch! #shorts"
]

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
  http.client.IncompleteRead, http.client.ImproperConnectionState,
  http.client.CannotSendRequest, http.client.CannotSendHeader,
  http.client.ResponseNotReady, http.client.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google API Console at
# https://console.cloud.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "YOUTUBE/secrets.json"
OAUTH_FILE = "YOUTUBE/oauth2.json"

# Get All required Tokens and Ids,
load_dotenv()
EMAIL = os.getenv('YOUTUBE_EMAIL')
PASSWORD = os.getenv('YOUTUBE_PASSWORD')
REDIRECT_URI = os.getenv('YOUTUBE_REDIRECT_URI')

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the API Console
https://console.cloud.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__), CLIENT_SECRETS_FILE))

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

def get_authenticated_service():
    if os.path.exists(OAUTH_FILE):
        # Check if token is expired and refresh if needed
        if not is_token_valid(OAUTH_FILE):
            print("Access token has expired. Refreshing...")
            new_access_token = refresh_access_token(OAUTH_FILE)
            if new_access_token is None:
                print("Failed to refresh the access token. Reauthorizing the app.")
                # Reauthorize the user here
                credentials = authorize()
                return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,credentials=credentials)
            else:
                print("Access token is still valid.")
        else:
            print("Access token is still valid.")
            
        # Load credentials
        credentials = load_credentials()
        print("credentials = ",credentials)
        return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,credentials=credentials)
    else:
        credentials = authorize()
        return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,credentials=credentials)

def is_token_valid(oauth_file):
    
    # Load the current access token
    with open(oauth_file, "r") as file:
        oauth_data = json.load(file)
    current_access_token = oauth_data.get("access_token")
    """
    Check if the given access token is valid using Google's tokeninfo endpoint.
    """
    token_info_url = "https://oauth2.googleapis.com/tokeninfo"
    params = {"access_token": current_access_token}
    
    try:
        response = requests.get(token_info_url, params=params)
        if response.status_code == 200:
            token_info = response.json()
            expires_in = int(token_info.get("expires_in", 0))
            print("expires_in = ",expires_in)
            # If expires_in > 0, the token is still valid
            return expires_in > 0
        else:
            print(f"Token validation failed: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"Error while validating token: {e}")
        return False

def refresh_access_token(oauth_file):
    # Logic to refresh the token
    client_id, client_secret = load_client_secrets(oauth_file)
    refresh_token = load_refresh_token(oauth_file)

    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        token_data = response.json()
        print("TOKEN DATA = ",token_data)
        new_access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in")
        save_access_token(oauth_file, new_access_token, expires_in)
        return new_access_token
    
    # Handle invalid_grant error (e.g., refresh token expired or revoked)
    elif response.status_code == 400 and "invalid_grant" in response.json():
        print("Refresh token invalid or expired. Reauthorizing...")

        # Delete the OAuth file to force reauthorization
        os.remove(oauth_file)
        print(f"OAuth file '{oauth_file}' deleted. Please reauthorize the app.")

        # Optionally, call a function to handle reauthorization here
        return None  # Indicating that reauthorization is required

    else:
        print(f"Failed to refresh token: {response.status_code} {response.text}")
        return None

def save_access_token(oauth_file, new_access_token, expires_in):
    with open(oauth_file, 'r') as file:
        data = json.load(file)

    data["access_token"] = new_access_token
    with open(oauth_file, 'w') as file:
        json.dump(data, file)
    print(f"Access token updated successfully in {oauth_file}")

def load_client_secrets(oauth_file):
    with open(oauth_file, 'r') as file:
        data = json.load(file)
    return data.get("client_id"), data.get("client_secret")

def load_refresh_token(oauth_file):
    with open(oauth_file, 'r') as file:
        data = json.load(file)
    return data.get("refresh_token")

def save_credentials(credentials):
    """Save credentials to the OAuth file."""
    with open(OAUTH_FILE, "w") as token:
        data = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }
        json.dump(data, token)

def load_credentials():
    """Load credentials from the OAuth file."""
    if not os.path.exists(OAUTH_FILE):
        return None

    with open(OAUTH_FILE, "r") as token:
        data = json.load(token)

    credentials = Credentials.from_authorized_user_info(data)
    return credentials

def authorize():
    # Create flow instance to manage OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=[YOUTUBE_UPLOAD_SCOPE])

    # The redirect URI must match the one in the Google Cloud Console
    flow.redirect_uri = REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true')

    print(f"Go to the following URL to authorize the application: {authorization_url}")
    # authorization_response = get_authorization_response(authorization_url)
    authorization_response = input("Enter authorization_response:")
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    print("credentials = ",credentials)
    save_credentials(credentials)
    return credentials

def initialize_upload(youtube, options):
    tags = None
    if options.keywords:
        tags = options.keywords.split(",")

    body = dict(
        snippet=dict(
            title=options.title,
            description=options.description,
            tags=tags,
            categoryId=options.category
        ),
        status=dict(
            privacyStatus=options.privacyStatus
        )
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )

    resumable_upload(insert_request)

# This method implements an exponential backoff strategy to resume a failed upload.
def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print("Uploading file...")
            status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print("Video id '%s' was successfully uploaded." % response['id'])
                else:
                    exit("The upload failed with an unexpected response: %s" % response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "A retriable error occurred: %s" % e

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)

def read_counter(counter_file):
    """Read the current counter value from the file, or initialize it."""
    if os.path.exists(counter_file):
        with open(counter_file, 'r') as file:
            return int(file.read())
    return 0

def read_description(description_file):
    print (description_file)
    try:
        with open(description_file, "r", encoding="utf-8") as file:
            description = file.read()
        return description
    except FileNotFoundError:
        return "Description file not found."
    except Exception as e:
        return f"An error occurred: {e}"
    
def read_tags(tags_file):
    print (tags_file)
    try:
        with open(tags_file, "r", encoding="utf-8") as file:
            tags = file.read()
        return tags
    except FileNotFoundError:
        return "Tags file not found."
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == '__main__':
    # Define a file to store the counter
    counter_file = 'counter.txt'    
    reel_number = read_counter(counter_file)
    # Execute the code
    print(f"Reel Number : {reel_number}")

    # Video file path  
    default_file_path = f"REEL_TO_UPLOAD/reel_{reel_number}.mp4"  # Link to the video file (must be accessible)
    
    # Description file path
    description_file = 'YOUTUBE/description.txt'
    description = read_description(description_file)
    print(f"Description : {description}")

    # Tag file path
    tags_file = 'YOUTUBE/tags.txt'
    tags = read_tags(tags_file)
    print(f"Tags : {tags}")
    
    title = random.choice(titles)
    print ("title = ",title)
    argparser.add_argument("--file", required=False, default=default_file_path, help="Video file to upload")
    argparser.add_argument("--title", help="Video title", default=title)
    argparser.add_argument("--description", help="Video description", default=description)
    argparser.add_argument("--category", default="27", help="Numeric video category. " + "See https://developers.google.com/youtube/v3/docs/videoCategories/list")
    argparser.add_argument("--keywords", help="Video keywords, comma separated", default=tags)
    argparser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES, default=VALID_PRIVACY_STATUSES[0], help="Video privacy status.")
    args = argparser.parse_args()

    if not os.path.exists(args.file):
        exit("Please specify a valid file using the --file= parameter.")

    youtube = get_authenticated_service()
    try:
        initialize_upload(youtube, args)
    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))