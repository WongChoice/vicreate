# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt
RUN pip install --no-cache-dir --upgrade pytube
RUN pip install --no-cache-dir SpeechRecognition
RUN pip install --no-cache-dir pysrt  # Add this line to install the 'pysrt' module
# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production


# Run Gunicorn with Gevent
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:80", "--worker-class", "gevent", "--timeout", "0"]