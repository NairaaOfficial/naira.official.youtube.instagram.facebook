import os
import cv2
import numpy as np
import random
import logging
import shutil
from moviepy import *

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Video Related Parameters
video_folder_path = 'VIDEOS'
reel_folder_path = 'REELS'
reel_upload_folder_path = 'REEL_TO_UPLOAD'

# Text/csv related parameters
counter_file = 'VIDEO_EDITING/../counter.txt'

# Reel Related Paramters      
reel_width, reel_height = 1080, 1920

# Image Related Parameters
# # Random integer between 1 and 10 (inclusive)
# hook_number = random.randint(1, 20)
# print(f"Hook Number : {hook_number}")
# down_overlay_image_path = f'VIDEO_EDITING/HOOKS/{hook_number}.jpg'

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

# Function to enhance the sharpness of the image
def sharpen_image(frame):
    logging.debug("Applying sharpening filter.")
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(frame, -1, kernel)

# Function to adjust the contrast of the image
def adjust_contrast(frame, alpha=1.2, beta=0):
    logging.debug("Adjusting contrast and brightness.")
    return cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

# Function to enhance color
def enhance_color(frame):
    logging.debug("Enhancing color by converting to HSV and adjusting saturation.")
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[:, :, 1] = cv2.addWeighted(hsv[:, :, 1], 1.2, hsv[:, :, 1], 0, 0)  # Increase saturation by 30%
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
           
def clean_up_files(*files):
    """Delete intermediate video files after the final video is created."""
    for file_path in files:
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Deleted file: {file_path}")
        else:
            logging.warning(f"File not found, skipping deletion: {file_path}")
            
def process_video(input_video_path, reel_number):
    output_reel_path = os.path.join(reel_folder_path, f'reel_no_audio_{reel_number}.mp4')
    video_overlay_path = os.path.join(reel_folder_path, f'reel_video_{reel_number}.mp4')
    final_output_path = os.path.join(reel_folder_path, f'reel_{reel_number}.mp4')
    
    def add_audio_to_video(input_path, output_path):
        with VideoFileClip(input_video_path) as original_clip, VideoFileClip(input_path) as cropped_clip:
            final_clip = cropped_clip.with_audio(original_clip.audio)
            final_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                bitrate="10000k",         # 10 Mbps is good for vertical HD reels
                audio_bitrate="192k",
                preset="slow"             # better quality
            )

       
    def overlay_video():

        extracted_cap = cv2.VideoCapture(input_video_path)
        if not extracted_cap.isOpened():
            logging.error(f"Could not open cropped video {input_video_path}")
            return

        fps = extracted_cap.get(cv2.CAP_PROP_FPS)
        output_reel = cv2.VideoWriter(output_reel_path, cv2.VideoWriter_fourcc(*'avc1'), fps, (reel_width, reel_height))
        print("reel_height = ",reel_height)
        print("reel_width = ",reel_width)

        # # Load and resize down overlay image
        # down_overlay_image = cv2.imread(down_overlay_image_path, cv2.IMREAD_UNCHANGED)
        # down_aspect_ratio = down_overlay_image.shape[1] / down_overlay_image.shape[0]
        # down_width = reel_width + 250
        # down_height = int(down_width / down_aspect_ratio)
        # down_overlay_image = cv2.resize(down_overlay_image, (down_width, down_height))

        # # Convert down_overlay_image to have transparency by masking black pixels
        # # Assumes the background is black (0, 0, 0)
        # lower_black = np.array([0, 0, 0])
        # upper_black = np.array([10, 10, 10])  # Small tolerance for black color
        # black_mask = cv2.inRange(down_overlay_image, lower_black, upper_black)
        
        # # Replace black pixels with transparent (alpha channel)
        # # Add alpha channel to down_overlay_image
        # bgr = down_overlay_image[:, :, :3]
        # alpha = cv2.bitwise_not(black_mask)
        # down_overlay_image = cv2.merge([bgr, alpha])
        
        while extracted_cap.isOpened():
            ret, frame = extracted_cap.read()
            if not ret:
                break
            
            enhanced_frame = frame[0:0 + reel_height, 0:0 + reel_width]
            # Apply enhancements: sharpening, contrast, and color enhancement
            # enhanced_frame = sharpen_image(enhanced_frame)
            # enhanced_frame = adjust_contrast(enhanced_frame)
            # enhanced_frame = enhance_color(enhanced_frame)
            h, w = enhanced_frame.shape[:2]
            scale = min(reel_width / w, reel_height / h)
            new_w, new_h = int(w * scale), int(h * scale)

            resized_frame = cv2.resize(enhanced_frame, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            black_background = np.zeros((reel_height, reel_width, 3), dtype=np.uint8)
            x_offset = (reel_width - new_w) // 2
            y_offset = (reel_height - new_h) // 2
            black_background[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized_frame
            # resized_frame = cv2.resize(enhanced_frame, (reel_width, reel_height), interpolation=cv2.INTER_CUBIC)
            # print("resized_frame = ",resized_frame)
            # black_background = np.zeros((reel_height, reel_width, 3), dtype=np.uint8)
            # center_x, center_y = 0,0

            # black_background[center_y:center_y + reel_height, center_x:center_x + reel_width] = resized_frame
            
            # # Add down overlay image (with transparency)
            # down_center_y = reel_height - 700
            # overlay_y1 = down_center_y
            # overlay_y2 = down_center_y + down_height
            # overlay_x1 = (reel_width - down_width) // 2
            # overlay_x2 = overlay_x1 + down_width

            # # Apply transparency of the down_overlay_image
            # for y in range(down_height):
            #     for x in range(down_width):
            #         if down_overlay_image[y, x, 3] > 0:  # Check if alpha is not 0 (not transparent)
            #             black_background[overlay_y1 + y, overlay_x1 + x] = down_overlay_image[y, x, :3]  # Copy RGB
            
            output_reel.write(black_background)

        extracted_cap.release()
        output_reel.release()
        add_audio_to_video(output_reel_path, video_overlay_path)
        
    # Step 1 - Overlay the cropped Video on a Black Background
    # overlay_video()
    # Step 2 - Clean up some files
    shutil.copy(video_overlay_path,final_output_path)
    clean_up_files(output_reel_path, video_overlay_path)

def main():
    # Getting the reel number from counter file.
    reel_number = get_reel_number()
    print(f"Reel Number : {reel_number}")
    
    # Remove the previous day's reel before starting today's processing
    remove_previous_reel(reel_number)
    
    # Get the input video from video folder.
    input_video_path = get_input_video(reel_number)
    
    # Process the input video
    # process_video(input_video_path, reel_number)
            
    # Copy the final processed reel to REEL_TO_UPLOAD
    # final_reel_path = os.path.join(input_video_path, f'reel_{reel_number}.mp4')
    copy_to_upload_folder(input_video_path, reel_number)
            
if __name__ == "__main__":
    main()
