from openai import OpenAI
from os import environ
from pydantic import BaseModel

class Translator(BaseModel):
    content: str

class OpenRouter:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=environ["OPEN_ROUTER_API_KEY"]
        )

    def complete_translate(self, text: str, target_language: str) -> str:
        prompt = f"""
            translate the following text to: {target_language}:
            {text}
        """

        completion = self.client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                },
                {
                    "role": "system",
                    "content": "Bạn là một chuyên gia dịch thuật phim. Nhiệm vụ của bạn là dịch chính xác và tự nhiên các đoạn hội thoại trong phim từ ngôn ngữ nguồn sang ngôn ngữ đích, đồng thời giữ nguyên ngữ cảnh và cảm xúc của nhân vật. Đảm bảo rằng bản dịch phù hợp với văn hóa và ngôn ngữ của khán giả mục tiêu, sử dụng ngôn ngữ tự nhiên và dễ hiểu. Nếu gặp từ ngữ hoặc cụm từ khó dịch, hãy chọn cách diễn đạt tương đương trong ngôn ngữ đích để truyền tải ý nghĩa một cách chính xác."
                }
            ],
            response_format=Translator,
        )

        print(completion.choices[0].message.parsed)

        return completion.choices[0].message.parsed