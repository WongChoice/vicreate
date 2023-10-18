# Import necessary modules
from flask import Flask, request, render_template
import os
from pytube import YouTube
from moviepy.editor import VideoFileClip
import speech_recognition as sr
import pysrt
from tqdm import tqdm
import subprocess
import logging
from gevent.pywsgi import WSGIServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("my_logger")

# Create a Flask app instance
app = Flask(__name__)

# Define the routes and view functions
@app.route('/')
def index():
    return render_template('index.html')  # Make sure 'index.html' exists in the correct location

# Define paths for the video and audio folders within the app directory
app_dir = os.path.dirname(os.path.abspath(__file__))
video_folder = os.path.join(app_dir, "video")
audio_folder = os.path.join(app_dir, "audio")
subtitle_folder = os.path.join(app_dir, "subtitle")

# Ensure the video, audio, and subtitle folders exist, create them if not
os.makedirs(video_folder, exist_ok=True)
os.makedirs(audio_folder, exist_ok=True)
os.makedirs(subtitle_folder, exist_ok=True)

def download_video(youtube_url, output_path):
    try:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
        if stream:
            stream.download(output_path=video_folder, filename=output_path)
            logger.info("Video downloaded successfully.")
        else:
            return "No suitable video stream found."
    except Exception as e:
        return f"An error occurred while downloading the video: {str(e)}"

def extract_audio(video_path, audio_output_path):
    try:
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(audio_output_path, codec="pcm_s16le")
        video_clip.reader.close()
        logger.info("Audio extracted successfully.")
    except Exception as e:
        return f"An error occurred while extracting audio: {str(e)}"

def generate_subtitles(audio_path, subtitle_file_path):
    recognizer = sr.Recognizer()
    start = 0
    end = 0
    subtitles = []

    with sr.AudioFile(audio_path) as source:
        recognizer.adjust_for_ambient_noise(source)
        audio_duration = source.DURATION
        chunk_duration = 10
        num_chunks = int(audio_duration / chunk_duration)

        with tqdm(total=num_chunks) as pbar:
            for _ in range(num_chunks):
                try:
                    audio = recognizer.record(source, duration=chunk_duration)
                    try:
                        text = recognizer.recognize_google(audio)
                        end = start + chunk_duration
                        sub = pysrt.SubRipItem()
                        sub.text = text
                        sub.start.seconds = start
                        sub.end.seconds = end
                        subtitles.append(sub)
                        start = end
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        logger.error(f"Could not request results from Google Web Speech API: {str(e)}")
                except sr.WaitTimeoutError:
                    break
                pbar.update(1)

        pysrt.SubRipFile(items=subtitles).save(subtitle_file_path)
        logger.info(f"Subtitles saved at: {subtitle_file_path}")

# Define a function for combining video and subtitles
def combine_video_and_subtitles(video_file, input_subs, output_file):
    subprocess.run(["ffmpeg", "-i", video_file, "-vf", f"subtitles={input_subs}", output_file])
    logger.info("Subtitles synchronized successfully!")

@app.route('/download', methods=['POST'])
def download_and_generate_subtitles():
    youtube_url = request.form['youtube_url']

    # Step 1: Download the video
    video_output_path = "test.mp4"
    download_error = download_video(youtube_url, video_output_path)
    if download_error:
        return download_error

    # Step 2: Extract audio from the video
    audio_output_path = os.path.join(audio_folder, "audio.wav")
    extract_audio_error = extract_audio(os.path.join(video_folder, video_output_path), audio_output_path)
    if extract_audio_error:
        return extract_audio_error

    # Step 3: Generate subtitles
    subtitle_file_path = os.path.join(subtitle_folder, "subtitle.srt")
    generate_subtitles(audio_output_path, subtitle_file_path)

    # Step 4: Combine video and subtitles asynchronously
    from gevent import spawn
    output_file = os.path.join(app_dir, "output.mp4")
    combine_task = spawn(combine_video_and_subtitles, os.path.join(video_folder, video_output_path), subtitle_file_path, output_file)

    return f"Audio and synchronized subtitles saved at {audio_output_path} and {subtitle_file_path}, and video with subtitles at {output_file}"

if __name__ == "__main__":
    # Use Gevent to run the Flask app with asynchronous workers
    http_server = WSGIServer(('', 80), app)
    http_server.serve_forever()
