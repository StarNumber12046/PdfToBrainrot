from openai import OpenAI
import replicate
import os
import google.generativeai as genai


def deepseek_summarize(text: str, system_prompt: str) -> str:
    deepseek = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com"
    )
    response = deepseek.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        stream=False,
    )
    return response.choices[0].message.content or ""


def llama_summarize(text: str, system_prompt: str) -> str:
    buf = ""
    for event in replicate.stream(
        "meta/meta-llama-3.1-405b-instruct",
        input={"prompt": text, "max_tokens": 4096},
    ):
        buf += str(event)
    return buf


def gemini_summarize(text: str, system_prompt: str) -> str:

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])  # type: ignore

    # Create the model
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192 * 2,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(  # type: ignore
        model_name="gemini-1.5-flash",
        generation_config=generation_config,  # type: ignore
        system_instruction=system_prompt,
    )

    chat_session = model.start_chat(history=[])

    response = chat_session.send_message(text)

    return response.text


def summarize_text(text: str, system_prompt: str, model: str) -> str:
    print("Summarizing text with model:", model)
    match model:
        case "deepseek-chat":
            return (
                deepseek_summarize(text, system_prompt)
                .replace("#", "")
                .replace("*", "")
            )
        case "llama-3.1":
            return (
                llama_summarize(text, system_prompt).replace("#", "").replace("*", "")
            )
        case "gemini-1.5-flash":
            return (
                gemini_summarize(text, system_prompt).replace("#", "").replace("*", "")
            )
        case _:
            raise ValueError("Model not supported")
