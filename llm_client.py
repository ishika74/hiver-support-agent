import os
from typing import Optional

from dotenv import load_dotenv
from google import genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GOOGLE_API_KEY and GEMINI_API_KEY:
    print("Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY.")

API_KEY = GOOGLE_API_KEY or GEMINI_API_KEY

if not API_KEY:
    raise ValueError(
        "No Gemini API key found. Add GOOGLE_API_KEY to your .env file."
    )

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.6-flash"


def call_llm(
    prompt: str,
    placeholder=None,
    system: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Calls Gemini and optionally updates a Streamlit placeholder.
    """

    try:
        final_prompt = prompt

        if system:
            final_prompt = f"""
System instructions:
{system}

User request:
{prompt}
"""

        config = {}

        if max_tokens is not None:
            config["max_output_tokens"] = max_tokens

        response = client.models.generate_content(
            model=model or MODEL_NAME,
            contents=final_prompt,
            config=config if config else None,
        )

        if response and response.text:
            answer = response.text.strip()
        else:
            answer = "I could not generate a response."

        if placeholder is not None:
            placeholder.markdown(answer)

        return answer

    except Exception as error:
        print(f"Gemini API error: {type(error).__name__}: {error}")

        error_message = (
            "Sorry, the AI service is temporarily unavailable. "
            "Please try again shortly."
        )

        if placeholder is not None:
            placeholder.error(error_message)

        return error_message


def generate_response(prompt: str) -> str:
    return call_llm(prompt)


def generate_reply(prompt: str) -> str:
    return call_llm(prompt)


def ask_gemini(prompt: str) -> str:
    return call_llm(prompt)