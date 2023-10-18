# Import necessary modules from Flask and your application
from flask import Flask, request, render_template
import os
from pytube import YouTube
from moviepy.editor import VideoFileClip

# Create a Flask app instance
app = Flask(__name__)

# Define the routes and view functions
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    youtube_url = request.form['youtube_url']

    # Define paths for the video and audio folders within the app directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    video_folder = os.path.join(app_dir, "video")
    audio_folder = os.path.join(app_dir, "audio")

    # Ensure the video and audio folders exist, create them if not
    os.makedirs(video_folder, exist_ok=True)
    os.makedirs(audio_folder, exist_ok=True)

    # Initialize the error_message variable
    error_message = None

    # Step 1: Extract the video from the YouTube link
    try:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
        if stream:
            video_output_path = os.path.join(video_folder, "test.mp4")
            stream.download(output_path=video_folder, filename="test.mp4")
            print("Video downloaded successfully.")
        else:
            error_message = "No suitable video stream found."
    except Exception as e:
        error_message = f"An error occurred while downloading the video: {str(e)}"

    # Step 2: Extract audio from the video
    if not error_message:
        try:
            video_clip = VideoFileClip(video_output_path)
            audio_output_path = os.path.join(audio_folder, "audio.wav")
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(audio_output_path, codec="pcm_s16le")
            print("Audio extracted successfully.")

            # Close the video file to release the resources
            video_clip.reader.close()
        except Exception as e:
            error_message = f"An error occurred while extracting audio: {str(e)}"

    # Clean up - remove the video file if there was no error
    if os.path.exists(video_output_path) and not error_message:
        #os.remove(video_output_path)
        print("Video file removed.")

    if error_message:
        print(error_message)
        return error_message

    return f"Audio file saved at {audio_output_path}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
