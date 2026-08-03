import requests
from app.config import settings


def generate_answer(prompt: str, model: str = None) -> str:
    """
    Send a prompt to a local Ollama server and return the generated text.
    Raises a RuntimeError with a clear message if Ollama isn't reachable.
    """
    model_name = model or settings.OLLAMA_MODEL
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"

    try:
        response = requests.post(
            url,
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Could not connect to Ollama. Make sure it's running "
            f"({settings.OLLAMA_BASE_URL}) and that you've pulled the model "
            f"with: ollama pull {model_name}"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama request timed out. Try a smaller model or shorter context.")

    data = response.json()
    return data.get("response", "").strip()
