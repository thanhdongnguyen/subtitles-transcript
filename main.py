# -*- coding: utf-8 -*-
from dataclasses import replace
from os import environ, path
from os.path import join, dirname
import os, sys
import pysrt
import yt_dlp
import subprocess
import uuid
import pydub
import shutil

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
        parse_sub = pysrt.from_string(res)
        processing_sub = ''

        subtitle_texts = [sub.text for sub in parse_sub]

        # 3. Chia nhỏ nội dung (chunk) để tránh vượt giới hạn request
        chunks = chunk_subtitle_lines(subtitle_texts, max_length=30)


        translated_chunks = []
        for c in chunks:
            trans = openrouter.complete_translate(c, LANGUAGE[form['language']])
            print(f"origin: {c} | trans: {trans} \n")
            translated_chunks.append(trans)

        translated_lines = []
        for chunk in translated_chunks:
            for line in chunk.split("<|>"):
                translated_lines.append(line)

        if len(translated_lines) != len(parse_sub):
            print("Cảnh báo: Số dòng sau dịch không khớp với số dòng ban đầu.")
            # Có thể cần tinh chỉnh lại cách chunk và ghép
            # Ở đây để đơn giản, ta gán min(len(...), len(...)) để tránh lỗi
            min_len = min(len(translated_lines), len(parse_sub))
        else:
            min_len = len(parse_sub)

        for i in range(min_len):
            parse_sub[i].text = translated_lines[i]

        for s in parse_sub:

            processing_sub += f"{s.index}\n"
            processing_sub += f"{s.start} --> {s.end}\n"
            processing_sub += f"{s.text}\n\n"

        return {"success": True, "data": processing_sub}
    except Exception as e:
        logger.error(f"Error: {e}")
        return get_error(500), 500


def chunk_subtitle_lines(subtitle_lines, max_length=20):
    """
    Chia nhỏ danh sách subtitle (hoặc chuỗi) thành các chunk
    có độ dài vừa phải để tránh vượt quá giới hạn token/request của API.
    max_length tuỳ chỉnh cho phù hợp.
    """
    chunks = []
    current_chunk = ""
    current_index = 0

    for index, line in enumerate(subtitle_lines):
        line = line.replace("\n", "")
        if current_index == max_length:

            current_chunk += line
            current_index = 0
            chunks.append(current_chunk)
            current_chunk = ""
            continue

        if index == len(subtitle_lines) - 1:
            chunks.append(current_chunk)
        else:
            current_chunk += line + "<|>"
        current_index += 1

        # if len(current_chunk) + len(line) + 1 > max_length:
        #     # Nếu thêm line hiện tại vào chunk mà vượt quá max_length
        #     # thì ta chốt chunk cũ và bắt đầu chunk mới.
        #     chunks.append(current_chunk)
        #     current_chunk = line + "<|>"
        # else:
        #     if current_chunk:
        #         current_chunk += line
        #     else:
        #         current_chunk = line + "<|>"

    # Đừng quên chunk cuối
    # if current_chunk:
    #     chunks.append(current_chunk)

    return chunks

def download_m3u8_to_mp3(m3u8_url, headers, output_filename):
    """
    Download file M3U8 và chuyển đổi sang MP3

    Parameters:
    m3u8_url (str): URL của file M3U8
    output_filename (str): Tên file MP3 đầu ra (không cần đuôi .mp3)
    """
    try:
        id_dir = f"{uuid.uuid4()}"
        temp_dir = join(dirname(__file__), "upload", id_dir)
        os.makedirs(temp_dir, exist_ok=True)
        # Cấu hình yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{join(dirname(__file__), "upload", id_dir)}/%(title)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'concurrent_fragment_downloads': 200,
            'no_continue': True,
        }

        # Download file M3U8
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("Đang tải file M3U8...")
                info = ydl.extract_info(m3u8_url, download=True)
                downloaded_file = ydl.prepare_filename(info)
        except Exception as e:
            print(f'Đã xảy ra lỗi khi tải xuống: {e}')
            # Xóa thư mục tạm khi xảy ra lỗi
            shutil.rmtree(temp_dir)
            print(f'Đã xóa thư mục tạm: {temp_dir}')
            raise Exception(f'Đã xảy ra lỗi khi tải xuống: {e}')

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

        # Xóa file tạm sau khi chuyển đổi
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)

        print(f"Hoàn thành! File MP3 được lưu tại: {output_filename}")

    except Exception as e:
        print(f"Có lỗi xảy ra: {str(e)}")



if __name__ == "__main__":
    app.run(port=4001, debug=True, threaded=False, use_reloader=False)

