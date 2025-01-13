# -*- coding: utf-8 -*-
from os import environ, path
from os.path import join, dirname
import os, sys
import pysrt
import yt_dlp
import subprocess
import uuid
import pydub


sys.path.append(os.path.abspath(join(dirname(__file__), path.pardir)))

from flask import Flask, request, g
from dotenv import load_dotenv
from loguru import logger
from errors.error import get_error
from flask_cors import CORS
from langdetect import detect
from providers.firework import Firework
from providers.openrouter import OpenRouter
from providers.openai import OAI

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
CORS(app)

logger.add("logs/subtitle.log", rotation="1 day", format="{time} {level} {message}", level="INFO")

LANGUAGE = {
    "en": "english",
    "vi": "vietnamese",
}

@app.errorhandler(Exception)
def error_handler(e):
    logger.error(f"Internal server error: {e}")
    return get_error(500), 500

@app.route('/health')
def health_check():
    return 'OK', 200

@app.route("/v1/translate", methods=["POST"])
async def translate():
    try:
        form = request.get_json()
        if 'language' not in form:
            return get_error(17)
        if 'url' not in form:
            return get_error(18)
        if 'headers' not in form:
            return get_error(19)


        if form['language'] not in LANGUAGE:
            return get_error(25)

        op = OAI()
        openrouter = OpenRouter()

        filename = f"{uuid.uuid4()}.mp3"
        output_download = join(dirname(__file__), "upload", filename)
        download_m3u8_to_mp3(form['url'], form["headers"], output_download)
        if not os.path.exists(output_download):
            return get_error(26)



        print("Đang chuyển đổi file audio sang text ....")
        res = op.transcription(output_download)


        print("Đang lấy thông tin file subtitle ....")

        # if os.path.exists(output_optimize):
        #     os.remove(output_optimize)

        return {"success": True, "data": res}

        parse_sub = pysrt.from_string(res)
        processing_sub = ''

        for s in parse_sub:
            # lang = detect(s.text)

            s.text = openrouter.complete_translate(s.text, LANGUAGE[form['language']])

            print(f"{s.index}\n")

            # return {"success": True, "data": s.text}

            processing_sub += f"{s.index}\n"
            processing_sub += f"{s.start} --> {s.end}\n"
            processing_sub += f"{s.text}\n\n"

        return {"success": True, "data": processing_sub}
    except Exception as e:
        logger.error(f"Error: {e}")
        return get_error(500), 500


def download_m3u8_to_mp3(m3u8_url, headers, output_filename):
    """
    Download file M3U8 và chuyển đổi sang MP3

    Parameters:
    m3u8_url (str): URL của file M3U8
    output_filename (str): Tên file MP3 đầu ra (không cần đuôi .mp3)
    """
    try:
        # Cấu hình yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{join(dirname(__file__), "upload")}/%(title)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'concurrent_fragment_downloads': 200
        }

        # Download file M3U8
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Đang tải file M3U8...")
            info = ydl.extract_info(m3u8_url, download=True)
            downloaded_file = ydl.prepare_filename(info)

        # Chuyển đổi sang MP3 sử dụng ffmpeg
        print("Đang chuyển đổi sang MP3...")
        convert_audio = pydub.AudioSegment.from_file(downloaded_file, format="mp4")


        convert_audio = convert_audio.set_channels(1)  # Chuyển về mono
        convert_audio = convert_audio.set_frame_rate(16000)  # Sample rate phổ biến cho STT
        # Chuẩn hóa âm lượng
        target_dBFS = -20
        change_in_dBFS = target_dBFS - convert_audio.dBFS
        convert_audio = convert_audio.apply_gain(change_in_dBFS)

        convert_audio.export(output_filename, format="mp3")

        # ffmpeg_command = [
        #     'ffmpeg',
        #     '-i', downloaded_file,
        #     '-codec:a', 'libmp3lame',
        #     '-q:a', '2',  # Chất lượng MP3 (0-9, 0 là tốt nhất)
        #     output_filename
        # ]
        #
        # subprocess.run(ffmpeg_command, check=True)

        # Xóa file tạm sau khi chuyển đổi
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)

        print(f"Hoàn thành! File MP3 được lưu tại: {output_filename}")

    except Exception as e:
        print(f"Có lỗi xảy ra: {str(e)}")



if __name__ == "__main__":
    app.run(port=4001, debug=True, threaded=False, use_reloader=False)

