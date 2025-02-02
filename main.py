# -*- coding: utf-8 -*-
from os import environ, path
from os.path import join, dirname
import os, sys
from typing import List, Annotated

import pysrt
import yt_dlp
import uuid
import pydub
import shutil
import asyncio
from cleantext import clean

sys.path.append(os.path.abspath(join(dirname(__file__), path.pardir)))

from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware

from loguru import logger
from errors.error import get_error
from langdetect import detect
from providers import proxy_translate_chunk, proxy_translate_segment

app = FastAPI(
    title="Subtitle Translation API",
    description="List API Translate Subtitle",
    version="1.0.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

logger.add("logs/subtitle.log", rotation="1 day", format="{time} {level} {message}", level="DEBUG", backtrace=True, diagnose=True)

LANGUAGE = {
    "en": "English",
    "vi": "Vietnamese",
    "ar": "Arabic",
    "zh": "Chinese",
    "es": "Spanish",
}

ALLOWED_EXTENSIONS = {'srt', 'vtt'}

CHAR_SPLIT = "<<<>>>"

# @app.errorhandler(Exception)
# def error_handler(e):
#     logger.error(f"Internal server error: {e}")
#     return get_error(500), 500
#


@app.get('/health')
def health_check():
    return 'OK', 200

# @app.route("/v1/translate", methods=["POST"])
# async def translate():
#     try:
#         form = request.get_json()
#         if 'language' not in form:
#             return get_error(17)
#         if 'url' not in form:
#             return get_error(18)
#         if 'headers' not in form:
#             return get_error(19)
#
#
#         if form['language'] not in LANGUAGE:
#             return get_error(25)
#
#         op = OAI()
#         openrouter = OpenRouter()
#         gemini = Gemini()
#
#         filename = f"{uuid.uuid4()}.mp3"
#         output_download = join(dirname(__file__), "upload", filename)
#         download_m3u8_to_mp3(form['url'], form["headers"], output_download)
#         if not os.path.exists(output_download):
#             return get_error(26)
#
#         print("Đang chuyển đổi file audio sang text ....")
#         res = op.transcription(output_download)
#         print("Đang lấy thông tin file subtitle ....")
#         parse_sub = pysrt.from_string(res)
#         processing_sub = ''
#
#         subtitle_texts = [sub.text for sub in parse_sub]
#
#         # 3. Chia nhỏ nội dung (chunk) để tránh vượt giới hạn request
#         chunks = chunk_subtitle_lines(subtitle_texts, max_length=30)
#
#         translated_chunks = []
#         for c in chunks:
#             trans = gemini.complete_translate(c, LANGUAGE[form['language']])
#             print(f"origin: {c} | trans: {trans} \n")
#             translated_chunks.append(trans)
#
#         translated_lines = []
#         for chunk in translated_chunks:
#             for line in chunk.split("<|>"):
#                 translated_lines.append(line)
#
#         if len(translated_lines) != len(parse_sub):
#             print("Cảnh báo: Số dòng sau dịch không khớp với số dòng ban đầu.")
#             min_len = min(len(translated_lines), len(parse_sub))
#         else:
#             min_len = len(parse_sub)
#
#         for i in range(min_len):
#             parse_sub[i].text = translated_lines[i]
#
#         for s in parse_sub:
#
#             processing_sub += f"{s.index}\n"
#             processing_sub += f"{s.start} --> {s.end}\n"
#             processing_sub += f"{s.text}\n\n"
#
#         return {"success": True, "data": processing_sub}
#     except Exception as e:
#         logger.error(f"Error: {e}")
#         return get_error(500), 500

@app.post("/v1/translate/file")
async def translate_file(file: UploadFile, language: Annotated[str, Form()]):
    try:
        if file.filename == '':
            return get_error(20)
        if not file or allowed_file(file.filename) is False:
            return get_error(20)

        filename = f"{uuid.uuid4()}.{get_extension(file.filename)}"
        filepath = join(dirname(__file__), 'upload', filename)
        contents = file.file.read()
        with open(filepath, "wb") as f:
            f.write(contents)

        if language not in LANGUAGE:
            return get_error(25)

        content = open(filepath, "r", encoding="utf-8")
        parse_content = content.read()
        try:
            parse_srt = pysrt.from_string(parse_content)
        except Exception as e:
            os.remove(filepath)
            return get_error(28)
        os.remove(filepath)

        subtitle_texts = [sub.text for sub in parse_srt]
        chunks = chunk_subtitle_lines(subtitle_texts, max_length=49)

        translated_lines = await translate_chunks(chunks, language)
        if len(translated_lines) != len(parse_srt):
            print("Cảnh báo: Số dòng sau dịch không khớp với số dòng ban đầu.")

        processing_sub = ""
        for index, s in enumerate(parse_srt):
            translated_text = translated_lines[index]
            processing_sub += f"{s.index}\n"
            processing_sub += f"{s.start} --> {s.end}\n"
            processing_sub += f"{translated_text}\n\n"

        return {"success": True, "data": processing_sub}

    except Exception as e:
        logger.error(f"Error: {e}")
        return get_error(500), 500

async def translate_chunks(chunks: List[str], language: str) -> List[str]:
    translated_lines = []
    for index, c in enumerate(chunks):

        code_origin_lang = detect(c)
        origin_lang = "" if code_origin_lang not in LANGUAGE else LANGUAGE[code_origin_lang]

        split_content_root = c.split(CHAR_SPLIT)
        segment = len(split_content_root)
        trans = await proxy_translate_chunk(text=c, origin_lang=origin_lang, target_lang=LANGUAGE[language])

        split_content_translated = trans.split(CHAR_SPLIT)
        segment_res = len(split_content_translated)

        if segment_res != segment:
            print(
                f"data_origin: {c}, \n ------------ \n data_translate: {trans} \n translated: {segment_res}, origin: {segment}, index: {index}\n\n\n")

            trans = await handler_segment_translate(split_content_root, LANGUAGE[language])

            print(f"Re-Translate, index: {index}, origin: {segment}, translated: {len(trans.split(CHAR_SPLIT))} \n")

        translated_lines += trans.split(CHAR_SPLIT)
    return translated_lines

async def handler_segment_translate(segments: List[str], lang: str) -> str:
    translated_segment = ""

    origin_chunk = "".join(segments)

    origin_lang = detect(origin_chunk)

    print(f"Detect lang: {origin_lang}")
    origin_lang = "" if origin_lang not in LANGUAGE else LANGUAGE[origin_lang]

    responses = await asyncio.gather(*[proxy_translate_segment(chunk=origin_chunk, text=c, origin_lang=origin_lang, target_lang=lang) for c in segments])

    for index, seg_trans in  enumerate(responses):
        print(f"translate each segment: {seg_trans} \n")

        translated_segment += f"{seg_trans} {CHAR_SPLIT}" if index < len(segments) - 1 else seg_trans

    # for index, c in  enumerate(segments):
    #     seg_trans = openrouter.complete_translate_segment(chunk=origin_chunk, text=c, origin_lang=origin_lang, target_lang=lang)
    #
    #     print(f"translate each segment: {seg_trans} \n")
    #
    #     translated_segment += f"{seg_trans} {CHAR_SPLIT}" if index < len(segments) - 1 else seg_trans

    return translated_segment



def allowed_file(filename):
    return '.' in filename and get_extension(filename) in ALLOWED_EXTENSIONS


def get_extension(filename):
    return filename.rsplit('.', 1)[1].lower()

def clean_text (text: str) -> str:
    # origin_lang = detect(text)
    text = text.replace("<i>", "").replace("</i>", "").replace("<b>", "").replace("</b>", "").replace("<u>", "").replace("</u>", "")
    return clean(text)

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
        line = clean_text(line)
        if current_index == max_length:
            current_chunk += line
            current_index = 0
            chunks.append(current_chunk)
            current_chunk = ""
            continue

        if index == len(subtitle_lines) - 1:
            chunks.append(current_chunk)
        else:
            current_chunk += line + f" {CHAR_SPLIT} "
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



# if __name__ == "__main__":
#     app.r(port=4001, debug=True, threaded=False, use_reloader=False)

