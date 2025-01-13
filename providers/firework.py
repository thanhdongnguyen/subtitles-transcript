import requests
from os import environ

class Firework:


    def speech_to_text(self, file_path: str, language: str) -> str:

        with open(file_path, "rb") as f:
            response = requests.post(
                "https://audio-prod.us-virginia-1.direct.fireworks.ai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {environ['FIREWORK_API_KEY']}"},
                files={"file": f},
                data={
                    "vad_model": "silero",
                    "alignment_model": "tdnn_ffn",
                    "preprocessing": "none",
                    # "language": "vi",
                    "temperature": "0",
                    "timestamp_granularities": "segment",
                    "audio_window_seconds": "5",
                    "speculation_window_words": "4",
                    "response_format": "srt",
                    "prompt": "Please transcribe content in this video",
                },
            )

        if response.status_code == 200:
            print(response.text)
            return response.text
        else:
            print(f"Error: {response.status_code}", response.text)
