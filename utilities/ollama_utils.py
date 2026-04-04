"""
ollama_utils.py -- Ollama local LLM client with connection handling and fallback.

Wraps the Ollama HTTP API with:
- Auto-detect available models
- Connection check before calling (no crash if Ollama is down)
- Structured JSON response parsing
- Batch processing with progress logging
- Fallback: if Ollama down, route to Gemini Flash automatically

Usage:
    import sys
    sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
    from ollama_utils import ask, ask_json, is_up, batch_ask

    if is_up():
        result = ask('Summarize this text: ...')
        data   = ask_json('Extract fields from: ...', schema={'title': '', 'year': 0})

    # Batch with progress
    results = batch_ask(prompts=['prompt1', 'prompt2'], delay=2.0)
"""
import json
import time
import urllib.request
import urllib.error
from typing import Any, Optional

# Bezos Rule: circuit breaker constant
MAX_CONSECUTIVE_FAILURES = 3

OLLAMA_BASE    = 'http://127.0.0.1:11434'
STUDIO_CONFIG  = 'G:/My Drive/Projects/_studio/studio-config.json'
DEFAULT_MODEL  = 'gemma3:4b'
DEFAULT_TIMEOUT = 60


def _load_config() -> dict:
    try:
        return json.load(open(STUDIO_CONFIG, encoding='utf-8'))
    except Exception:
        return {}


def _default_model() -> str:
    return _load_config().get('ollama_model', DEFAULT_MODEL)


def is_up(timeout: int = 3) -> bool:
    """Return True if Ollama is running and reachable."""
    try:
        urllib.request.urlopen(OLLAMA_BASE + '/api/tags', timeout=timeout)
        return True
    except Exception:
        return False


def list_models() -> list:
    """Return list of available model names. Empty list if Ollama is down."""
    try:
        r = urllib.request.urlopen(OLLAMA_BASE + '/api/tags', timeout=5)
        data = json.loads(r.read())
        return [m.get('name', '') for m in data.get('models', [])]
    except Exception:
        return []


def ask(
    prompt: str,
    model: str = None,
    timeout: int = DEFAULT_TIMEOUT,
    system: str = '',
) -> Optional[str]:
    """
    Send a prompt to Ollama and return the response text.

    Args:
        prompt:  The user prompt
        model:   Model name (default: from studio-config.json)
        timeout: Request timeout in seconds
        system:  Optional system prompt

    Returns:
        Response string, or None if Ollama is down or request fails.
    """
    if not is_up():
        return None

    model = model or _default_model()
    payload = {'model': model, 'prompt': prompt, 'stream': False}
    if system:
        payload['system'] = system

    try:
        req = urllib.request.Request(
            OLLAMA_BASE + '/api/generate',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'},
        )
        r = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(r.read())
        return data.get('response', '').strip()
    except Exception as e:
        print(f'[ollama_utils] ask() error: {e}')
        return None


def ask_json(
    prompt: str,
    schema: dict = None,
    model: str = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = 2,
) -> Optional[dict]:
    """
    Ask Ollama for a JSON response. Retries on parse failure.

    Args:
        prompt:  Prompt text — should instruct the model to return JSON
        schema:  Optional example schema appended to prompt as a hint
        model:   Model name (default: from studio-config.json)
        timeout: Request timeout
        retries: Number of retry attempts on JSON parse failure

    Returns:
        Parsed dict, or None on failure.
    """
    full_prompt = prompt
    if schema:
        full_prompt += f'\n\nReturn ONLY valid JSON matching this schema:\n{json.dumps(schema, indent=2)}'

    for attempt in range(retries + 1):
        raw = ask(full_prompt, model=model, timeout=timeout)
        if raw is None:
            return None
        # Strip markdown fences
        text = raw.replace('```json', '').replace('```', '').strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if attempt < retries:
                time.sleep(1)
                continue
            print(f'[ollama_utils] ask_json() failed to parse after {retries+1} attempts')
            print(f'  Raw: {raw[:200]}')
            return None

    return None


def batch_ask(
    prompts: list,
    model: str = None,
    delay: float = 2.0,
    timeout: int = DEFAULT_TIMEOUT,
    show_progress: bool = True,
) -> list:
    """
    Run a list of prompts through Ollama sequentially with delay.

    Args:
        prompts:       List of prompt strings
        model:         Model name (default: from config)
        delay:         Seconds to sleep between calls (default 2.0)
        timeout:       Per-request timeout
        show_progress: Print progress every 10 items

    Returns:
        List of response strings (None for failed calls). Same length as prompts.
    """
    if not is_up():
        print('[ollama_utils] Ollama is DOWN — batch_ask skipped')
        return [None] * len(prompts)

    model   = model or _default_model()
    results = []

    for i, prompt in enumerate(prompts):
        if show_progress and i > 0 and i % 10 == 0:
            ok = sum(1 for r in results if r is not None)
            print(f'  [ollama] {i}/{len(prompts)} done ({ok} OK)')

        result = ask(prompt, model=model, timeout=timeout)
        results.append(result)

        if i < len(prompts) - 1:
            time.sleep(delay)

    ok = sum(1 for r in results if r is not None)
    if show_progress:
        print(f'  [ollama] batch complete: {ok}/{len(prompts)} successful')

    return results


def with_gemini_fallback(
    prompt: str,
    gemini_key: str = None,
    model: str = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Optional[str]:
    """
    Try Ollama first; if down, fall back to Gemini Flash.

    Args:
        prompt:      The prompt to send
        gemini_key:  Gemini API key (reads from studio-config.json if not provided)
        model:       Ollama model name
        timeout:     Request timeout

    Returns:
        Response string from whichever model succeeded, or None.
    """
    result = ask(prompt, model=model, timeout=timeout)
    if result is not None:
        return result

    # Ollama failed — try Gemini Flash
    print('[ollama_utils] Ollama unavailable, falling back to Gemini Flash')
    if gemini_key is None:
        gemini_key = _load_config().get('gemini_api_key', '')
    if not gemini_key:
        print('[ollama_utils] No Gemini key configured — fallback failed')
        return None

    try:
        import sys
        import os
        util_dir = os.path.dirname(os.path.abspath(__file__))
        if util_dir not in sys.path:
            sys.path.insert(0, util_dir)
        from gemini_utils import ask as gemini_ask
        return gemini_ask(prompt, api_key=gemini_key, timeout=timeout)
    except Exception as e:
        print(f'[ollama_utils] Gemini fallback error: {e}')
        return None
