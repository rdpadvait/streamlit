import logging
import os
import subprocess

import ffmpeg

from logger import logger

logger = logging.getLogger(__name__)

def download_video(url, output_path):
    logger.info(f"Downloading video from {url=}")
    cmd = ["yt-dlp", "--force-overwrite", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4", "-o", output_path, url]
    logger.info("Running command: " + " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.exists(output_path):
            logger.info(f"Downloaded video to {output_path}")
        else:
            logger.error("Error: Output file not created.")
            return None
    except subprocess.CalledProcessError as e:
        logger.error(f"youtube-dl error: {e.stderr.decode()}")
        return None

def speed_up_video(input_path, output_path, speed):
    logger.info(f"Speeding up video by {speed} for {input_path=}")
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-filter_complex", f"[0:v]setpts={1/speed}*PTS[v];[0:a]atempo={speed}[a]",
        "-map", "[v]",
        "-map", "[a]",
        output_path,
    ]
    logger.info("Running command: " + " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.exists(output_path):
            logger.info(f"Speeded up video written to {output_path}")
        else:
            logger.error("Error: Output file not created.")
            return None
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode()}")
        return None
        
def extract_audio(video_path, output_path):
    logger.info(f"Extracting audio from video: {video_path}")
    assert output_path.endswith(".mp3"), "Output path must end with .mp3"
    try:
        stdout, stderr = (
            ffmpeg.input(video_path)
            .output(output_path, vn=None, acodec="libmp3lame", ar=16000, ac=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        if os.path.exists(output_path):
            logger.info(f"Extracted audio to {output_path}")
            return output_path
        else:
            logger.error("Error: Audio was not extracted correctly.")
            return None
    except ffmpeg.Error as e:
        logger.error(f"Error extracting audio: {e.stderr.decode()}")
        return None

def change_audio_speed(audio_file, output_file, factor):
    logger.info(f"Speeding by {factor} for {audio_file=} ")
    try:
        stdout, stderr = (
            ffmpeg.input(audio_file)
            .filter("atempo", factor)
            .output(output_file)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        logger.error(f"Error adjusting audio speed: {e.stderr.decode()}")

def merge_audio_video(video_file, audio_file, output_file):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_file,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        output_file,
    ]
    logger.info("Running command: " + " ".join(cmd))

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.exists(output_file):
            logger.info(f"Merged audio and video into {output_file}")
        else:
            logger.error("Error: Output file not created.")
            return None
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode()}")
        return None

if __name__ == "__main__":
    video_path = "/Users/saurabhpurohit/Desktop/telugu/vid_fast.mp4"
    slow_vid_path = "/Users/saurabhpurohit/Desktop/telugu/vid_slow.mp4"
    speed_up_video(video_path, slow_vid_path, 1/1.2)