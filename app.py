import os
from flask import Flask, request, render_template
from pytube import YouTube
from moviepy.editor import VideoFileClip

app = Flask(__name)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        youtube_url = request.form["youtube_url"]
        if youtube_url:
            try:
                # Output file paths
                video_output_path = os.path.abspath("test.mp4")
                audio_output_path = os.path.abspath("audio.wav")

                # Step 1: Extract the video from the YouTube link
                yt = YouTube(youtube_url)
                stream = yt.streams.get_highest_resolution()
                stream.download(output_path=os.path.dirname(video_output_path), filename=os.path.basename(video_output_path))

                # Step 2: Extract audio from the video
                video_clip = VideoFileClip(video_output_path)
                audio_clip = video_clip.audio
                audio_clip.write_audiofile(audio_output_path, codec="pcm_s16le")

                # Clean up - remove the video file
                # os.remove(video_output_path)

                return f"Audio extracted successfully. <a href='/'>Go back</a>"
            except Exception as e:
                return f"An error occurred: {str(e)} <a href='/'>Go back</a>"
        else:
            return "Please enter a YouTube URL. <a href='/'>Go back</a>"

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
