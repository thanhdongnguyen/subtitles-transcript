from .openrouter import OpenRouter
from .gemini import Gemini
from .openai import OpenAI

openrouter = OpenRouter()
gemini = Gemini()

PROVIDERS = ["openrouter", "gemini"]
SEQUENCE_PROVIDER = {
    "openrouter": openrouter,
    "gemini": gemini,
}

async def proxy_provider_translate(
        prompt: str, system_prompt: str = "", provider: str = "openrouter", max_retry: int = 0,
        model: str = ""
) -> str:
    try:

        if provider == "openrouter":
            return await openrouter.call_provider(prompt=prompt, system_prompt=system_prompt, model=model)
        elif provider == "gemini":
            return await gemini.call_provider(prompt=prompt, system_prompt=system_prompt, model=model)
        else:
            return await openrouter.call_provider(prompt=prompt, system_prompt=system_prompt, model=model)
    except Exception as e:
        # if max_retry == 5:
        raise e
        # return await proxy_provider_translate(prompt, system_prompt, provider, max_retry - 1)


async def proxy_translate_chunk(text: str, origin_lang: str, target_lang: str) -> str:
    prompt = f"Translate this from origin_lang: {origin_lang} to {target_lang}: {text}"
    system_prompt = """
                    You are an experienced semantic translator, specialized in creating SRT files. Separate translation segments with the '<<<>>>' symbol.
                    Note: 
                        - Only return translated text"""

    return await proxy_provider_translate(prompt, system_prompt, model="gemini-1.5-flash", provider="gemini")

async def proxy_translate_segment(text: str, chunk: str, origin_lang: str, target_lang: str) -> str:
    system_prompt = f"""
    You are an experienced semantic translator, specialized in creating SRT files. 
           Note: 
               - Only return translated text
           This is text original of {origin_lang} language: 
           {chunk}
"""
    prompt = f"""
           Translate this segment from {origin_lang} to {target_lang}: {text}
           """
    return await proxy_provider_translate(prompt=prompt, system_prompt=system_prompt, model="gemini-1.5-flash", provider="gemini")