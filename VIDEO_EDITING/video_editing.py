import os
import logging
import random
import shutil
from moviepy import *

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Folder paths and common parameters

# Video Related Parameters
video_folder_path = 'VIDEOS'
story_upload_folder_path = 'STORY_TO_UPLOAD'

# GIF Related Parameters
gif_list = ["Ronaldo.gif","Messi.gif"]
gif_file = random.choice(gif_list)
overlay_gif_path = f'VIDEO_EDITING/GIF/{gif_file}'

# counter related parameters
counter_file = 'VIDEO_EDITING/../counter.txt'

# Reel Related Paramters
reel_width, reel_height = 1080, 1920

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
        previous_reel_path = os.path.join(story_upload_folder_path, f'reel_{reel_number - 1}.mp4')
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
            
def clean_up_files(*files):
    """Delete intermediate video files after the final video is created."""
    for file_path in files:
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Deleted file: {file_path}")
        else:
            logging.warning(f"File not found, skipping deletion: {file_path}")
            
def process_video(input_video_path, reel_number):
    gif_overlay_path = os.path.join(story_upload_folder_path, f'story_gif_{reel_number}.mp4')
    final_output_path = os.path.join(story_upload_folder_path, f'story_{reel_number}.mp4')
        
    def overlay_gif():
        """
        Overlays a GIF onto the final video efficiently.
        """
        # Load the final video
        video = VideoFileClip(input_video_path)

        # Load the GIF as a VideoClip
        overlay_gif_clip = VideoFileClip(overlay_gif_path, has_mask=True)  # 'has_mask' keeps transparency

        # Resize GIF
        overlay_gif_clip = overlay_gif_clip.resized(width=video.w + 4000)
   
        # Trim or Loop the GIF to match the video duration
        print("gif duration = ",overlay_gif_clip.duration)
        print("video duration =",video.duration)
        
        if overlay_gif_clip.duration > video.duration:
            overlay_gif_clip = overlay_gif_clip.subclipped(0, video.duration)  # Trim GIF

        # Set overlay position
        gif_y = -350
        gif_x = -2200
        
        print(f"GIF Position: (x={gif_x}, y={gif_y})")
        print(f"GIF Dimensions: (w={overlay_gif_clip.w}, h={overlay_gif_clip.h})")
        print(f"Video Dimensions: (w={video.w}, h={video.h})")
    
        overlay_gif_clip = overlay_gif_clip.with_position((gif_x, gif_y))

        # Merge overlay GIF with video
        final_clip = CompositeVideoClip([video, overlay_gif_clip])

        # Save the output video
        final_clip.write_videofile(gif_overlay_path, codec="libx264", audio_codec="aac", fps=video.fps)

        # Close the Clip
        final_clip.close()

    # Step 1 - Overlay Gifs
    overlay_gif()
    # Step 2 - Clean up some files
    shutil.copy(gif_overlay_path,final_output_path)
    clean_up_files(gif_overlay_path)

def main():
    # Getting the reel number from counter file.
    reel_number = get_reel_number()
    print(f"Reel Number : {reel_number}")
    
    # Remove the previous day's reel before starting today's processing
    remove_previous_reel(reel_number)
    
    # Get the input video from video folder.
    input_video_path = get_input_video(reel_number)
    
    # Process the input video
    process_video(input_video_path, reel_number)

if __name__ == "__main__":
    main()
