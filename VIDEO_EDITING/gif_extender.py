from PIL import Image, ImageSequence

# === USER CONFIG ===
input_gif = "VIDEO_EDITING/GIF/gif_4.gif"
output_gif = "VIDEO_EDITING/GIF/gif_4_looped.gif"
repeat_n_times = 31  # Repeat the full GIF this many times

# Open the original GIF
original = Image.open(input_gif)

# Extract frames and durations
frames = []
durations = []

for frame in ImageSequence.Iterator(original):
    frames.append(frame.copy())
    durations.append(frame.info.get('duration', original.info.get('duration', 100)))

# Repeat frames and durations N times
repeated_frames = frames * repeat_n_times
repeated_durations = durations * repeat_n_times

# Save the repeated GIF
repeated_frames[0].save(
    output_gif,
    save_all=True,
    append_images=repeated_frames[1:],
    duration=repeated_durations,
    loop=0,
    disposal=2
)

# Calculate total duration in ms and seconds
total_duration_ms = sum(repeated_durations)
total_duration_sec = total_duration_ms / 1000

print(f"✅ Repeated GIF saved to: {output_gif}")
print(f"🕒 Final duration: {total_duration_sec:.2f} seconds ({total_duration_ms} ms)")
