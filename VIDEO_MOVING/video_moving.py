import os
import logging
import shutil

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Video Related Parameters
video_folder_path = 'VIDEOS'
reel_upload_folder_path = 'REEL_TO_UPLOAD'

# Text/csv related parameters
counter_file = 'VIDEO_MOVING/../counter.txt'

def get_reel_number():
    """Read the current counter value from the file, or initialize it."""
    if os.path.exists(counter_file):
        with open(counter_file, 'r') as file:
            return int(file.read())
    return 0

def remove_previous_reel(reel_number):
    """
    Remove the previous day's reel from the REEL_TO_UPLOAD folder.
    
    Parameters:
        reel_number (int): The current reel number.
    """
    if reel_number > 1:
        previous_reel_path = os.path.join(reel_upload_folder_path, f'reel_{reel_number - 1}.mp4')
        if os.path.exists(previous_reel_path):
            os.remove(previous_reel_path)
            logging.info(f"Removed previous day's reel: {previous_reel_path}")
        else:
            logging.warning(f"Previous day's reel not found: {previous_reel_path}")

def get_input_video(reel_number):
    ## Loop over the video folder and get the input video path
    for filename in os.listdir(video_folder_path):
        if filename.startswith("Video") and filename.endswith(f"_{reel_number}.mp4"):
            input_video_path = os.path.join(video_folder_path, filename) 
            logging.info(f'Processing {filename} as reel_{reel_number}')

    return input_video_path

def copy_to_upload_folder(current_reel_path, reel_number):
    """
    Copy the current day's reel to the REEL_TO_UPLOAD folder.
    
    Parameters:
        current_reel_path (str): Path of the current day's processed reel.
        reel_number (int): The current reel number.
    """
    if not os.path.exists(reel_upload_folder_path):
        os.makedirs(reel_upload_folder_path)
    destination_path = os.path.join(reel_upload_folder_path, f'reel_{reel_number}.mp4')
    shutil.copy(current_reel_path, destination_path)  # Move the file to avoid duplicates
    logging.info(f"Copied reel_{reel_number} to REEL_TO_UPLOAD folder.")
           
def main():
    # Getting the reel number from counter file.
    reel_number = get_reel_number()
    print(f"Reel Number : {reel_number}")
    
    # Remove the previous day's reel before starting today's processing
    remove_previous_reel(reel_number)
    
    # Get the input video from video folder.
    input_video_path = get_input_video(reel_number)
            
    # Copy the final processed reel to REEL_TO_UPLOAD
    copy_to_upload_folder(input_video_path, reel_number)
            
if __name__ == "__main__":
    main()
