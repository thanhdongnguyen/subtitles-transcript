# -*- coding: utf-8 -*-
from os import environ, path
from os.path import join, dirname
import os, sys
from urllib.parse import urljoin

import ffmpeg
import m3u8
import aiohttp
import aiofiles
import ffmpeg
import asyncio
import tempfile
import uuid

sys.path.append(os.path.abspath(join(dirname(__file__), path.pardir)))

from flask import Flask, request, g
from dotenv import load_dotenv
from loguru import logger
from errors.error import get_error
from flask_cors import CORS
from providers.firework import Firework

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
CORS(app)

logger.add("logs/subtitle.log", rotation="1 day", format="{time} {level} {message}", level="INFO")

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

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Download m3u8
                ts_file = await download_m3u8(form["url"], temp_dir)

                # Convert sang mp3
                output_file = os.path.join(temp_dir, f"{uuid.uuid4()}.mp3")
                await asyncio.to_thread(convert_to_mp3, ts_file, output_file)


                print(output_file, " - asdasdasd")
                # Return file
                # return FileResponse(
                #     output_file,
                #     media_type='audio/mpeg',
                #     filename=os.path.basename(output_file)
                # )
            except Exception as e:
                logger.error(f"Error download: {e}")
                return get_error(500), 500

        # fw = Firework()
        # res = fw.speech_to_text("/Users/dongnt/Desktop/truyen_test.mp3", form['language'])



        return {"success": True}
    except Exception as e:
        logger.error(f"Error: {e}")
        return get_error(500), 500


async def download_segment(session: aiohttp.ClientSession, url: str, output_path: str) -> None:
    """Download một segment của video"""
    async with session.get(url) as response:
        if response.status == 200:
            async with aiofiles.open(output_path, 'wb') as f:
                await f.write(await response.read())


async def download_m3u8(url: str, temp_dir: str) -> str:
    """Download toàn bộ video từ m3u8 playlist"""
    try:
        # Parse m3u8 playlist
        playlist = m3u8.load(url)
        print(f"playlist: {playlist}, url: {url}")
        if not playlist.segments:
            raise Exception("Invalid m3u8 playlist")

        # Tạo session để tái sử dụng connection
        async with aiohttp.ClientSession() as session:
            # Download tất cả segments song song
            tasks = []
            segment_files = []

            for i, segment in enumerate(playlist.segments):
                segment_path = os.path.join(temp_dir, f"segment_{i}.ts")
                segment_files.append(segment_path)
                tasks.append(download_segment(session, segment.uri, segment_path))

            await asyncio.gather(*tasks)

        # Ghép các segments lại
        with open(os.path.join(temp_dir, "concat_list.txt"), "w") as f:
            for segment_file in segment_files:
                f.write(f"file '{segment_file}'\n")

        output_ts = os.path.join(temp_dir, "output.ts")
        ffmpeg.input(os.path.join(temp_dir, "concat_list.txt"), f="concat", safe=0) \
            .output(output_ts, c="copy") \
            .overwrite_output() \
            .run(capture_stdout=True, capture_stderr=True)

        return output_ts

    except Exception as e:
        raise Exception(str(e))


async def convert_to_mp3(input_file: str, output_file: str) -> None:
    """Convert video sang mp3 với ffmpeg"""
    try:
        stream = ffmpeg.input(input_file)
        stream = ffmpeg.output(stream, output_file,
                               acodec='libmp3lame',
                               ab='192k',
                               ac=2,
                               ar='44100')
        ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        raise Exception(str(e))


if __name__ == "__main__":
    app.run(port=4001, debug=True, threaded=False, use_reloader=False)
