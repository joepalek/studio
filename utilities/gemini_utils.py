"""
gemini_utils.py -- Gemini Flash API client with rate limiting and JSON parsing.

Centralizes all Gemini API calls across the studio. Replaces the repeated
urllib boilerplate in every agent script.

Rate limits (free tier):
  - gemini-2.5-flash: 15 req/min, 1500 req/day
  - gemini-2.0-flash: 15 req/min, 1500 req/day

Usage:
    import sys
    sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
    from gemini_utils import ask, ask_json, batch_ask, load_key

    key    = load_key()
    result = ask('Summarize this: ...', api_key=key)
    data   = ask_json('Score this idea:', schema={'score': 0, 'reason': ''}, api_key=key)

    # Batch with auto rate limiting (4s between calls for free tier)
    results = batch_ask(prompts, api_key=key, delay=4.0)
"""
import json
import time
import urllib.request
import urllib.error
from typing import Any, Optional

# Bezos Rule: circuit breaker constant
MAX_CONSECUTIVE_FAILURES = 3

STUDIO_CONFIG   = 'G:/My Drive/Projects/_studio/studio-config.json'
DEFAULT_MODEL   = 'gemini-2.5-flash'
BASE_URL        = 'https://generativelanguage.googleapis.com/v1beta/models'
FREE_TIER_DELAY = 4.1   # seconds between calls to stay under 15 req/min


def load_key(config_path: str = STUDIO_CONFIG) -> str:
    """Load Gemini API key from studio-config.json."""
    try:
        config = json.load(open(config_path, encoding='utf-8'))
        return config.get('gemini_api_key', '')
    except Exception:
        return ''


def _build_url(model: str, api_key: str) -> str:
    return f'{BASE_URL}/{model}:generateContent?key={api_key}'


def _parse_response(data: dict) -> Optional[str]:
    """Extract text from Gemini API response."""
    try:
        return data['candidates'][0]['content']['parts'][0]['text'].strip()
    except (KeyError, IndexError, TypeError):
        return None


def ask(
    prompt: str,
    api_key: str = None,
    model: str = DEFAULT_MODEL,
    timeout: int = 20,
    system: str = '',
) -> Optional[str]:
    """
    Send a prompt to Gemini and return the response text.

    Args:
        prompt:  The user prompt
        api_key: Gemini API key (auto-loads from studio-config.json if not given)
        model:   Model ID (default: gemini-2.5-flash)
        timeout: Request timeout in seconds
        system:  Optional system instruction

    Returns:
        Response string, or None on error.
    """
    api_key = api_key or load_key()
    if not api_key:
        print('[gemini_utils] No API key — set gemini_api_key in studio-config.json')
        return None

    contents = []
    if system:
        contents.append({'role': 'user', 'parts': [{'text': system}]})
        contents.append({'role': 'model', 'parts': [{'text': 'Understood.'}]})
    contents.append({'role': 'user', 'parts': [{'text': prompt}]})

    payload = json.dumps({'contents': contents}).encode()

    try:
        req = urllib.request.Request(
            _build_url(model, api_key),
            data=payload,
            headers={'Content-Type': 'application/json'},
        )
        r   = urllib.request.urlopen(req, timeout=timeout)
        raw = json.loads(r.read())
        return _parse_response(raw)

    except urllib.error.HTTPError as e:
        body = ''
        try:
            body = e.read().decode('utf-8', errors='ignore')[:200]
        except Exception:
            pass
        if e.code == 429:
            print(f'[gemini_utils] Rate limit (429) — caller should add delay')
        else:
            print(f'[gemini_utils] HTTP {e.code}: {body}')
        return None
    except Exception as e:
        print(f'[gemini_utils] ask() error: {e}')
        return None


def ask_json(
    prompt: str,
    schema: dict = None,
    api_key: str = None,
    model: str = DEFAULT_MODEL,
    timeout: int = 20,
    retries: int = 2,
) -> Optional[dict]:
    """
    Ask Gemini for a JSON response. Retries on parse failure.

    Args:
        prompt:  Prompt text
        schema:  Optional example schema appended to prompt
        api_key: Gemini API key
        model:   Model ID
        timeout: Request timeout
        retries: Retry attempts on JSON parse failure

    Returns:
        Parsed dict, or None on failure.
    """
    full_prompt = prompt
    if schema:
        full_prompt += f'\n\nReturn ONLY valid JSON:\n{json.dumps(schema, indent=2)}'

    for attempt in range(retries + 1):
        raw = ask(full_prompt, api_key=api_key, model=model, timeout=timeout)
        if raw is None:
            if attempt < retries:
                time.sleep(2)
                continue
            return None

        text = raw.replace('```json', '').replace('```', '').strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if attempt < retries:
                time.sleep(2)
                continue
            print(f'[gemini_utils] ask_json() failed to parse after {retries+1} attempts')
            print(f'  Raw: {raw[:200]}')
            return None

    return None


def batch_ask(
    prompts: list,
    api_key: str = None,
    model: str = DEFAULT_MODEL,
    delay: float = FREE_TIER_DELAY,
    timeout: int = 20,
    show_progress: bool = True,
    on_rate_limit_pause: float = 30.0,
) -> list:
    """
    Run a list of prompts through Gemini with rate-limit-safe delays.

    Args:
        prompts:              List of prompt strings
        api_key:              Gemini API key
        model:                Model ID
        delay:                Seconds between calls (default 4.1 for free tier)
        timeout:              Per-request timeout
        show_progress:        Print progress every 10 items
        on_rate_limit_pause:  Extra pause on 429 response (seconds)

    Returns:
        List of response strings (None for failed). Same length as prompts.
    """
    api_key = api_key or load_key()
    results = []

    for i, prompt in enumerate(prompts):
        if show_progress and i > 0 and i % 10 == 0:
            ok = sum(1 for r in results if r is not None)
            print(f'  [gemini] {i}/{len(prompts)} ({ok} OK)')

        result = ask(prompt, api_key=api_key, model=model, timeout=timeout)

        if result is None:
            # Check if we got rate limited — if so, pause longer
            results.append(None)
            time.sleep(on_rate_limit_pause)
        else:
            results.append(result)
            if i < len(prompts) - 1:
                time.sleep(delay)

    ok = sum(1 for r in results if r is not None)
    if show_progress:
        print(f'  [gemini] batch complete: {ok}/{len(prompts)} successful')

    return results


def batch_ask_json(
    prompts: list,
    schema: dict = None,
    api_key: str = None,
    model: str = DEFAULT_MODEL,
    delay: float = FREE_TIER_DELAY,
    timeout: int = 20,
    show_progress: bool = True,
) -> list:
    """
    Batch JSON variant — each prompt gets a parsed-dict response.

    Returns list of dicts (None for failed). Same length as prompts.
    """
    api_key = api_key or load_key()
    results = []

    for i, prompt in enumerate(prompts):
        if show_progress and i > 0 and i % 10 == 0:
            ok = sum(1 for r in results if r is not None)
            print(f'  [gemini/json] {i}/{len(prompts)} ({ok} OK)')

        result = ask_json(prompt, schema=schema, api_key=api_key,
                          model=model, timeout=timeout)
        results.append(result)

        if i < len(prompts) - 1:
            time.sleep(delay)

    ok = sum(1 for r in results if r is not None)
    if show_progress:
        print(f'  [gemini/json] batch complete: {ok}/{len(prompts)} successful')

    return results


def is_available(api_key: str = None) -> bool:
    """Quick check that Gemini API key is set and models endpoint responds."""
    api_key = api_key or load_key()
    if not api_key:
        return False
    try:
        url = f'{BASE_URL}?key={api_key}'
        urllib.request.urlopen(url, timeout=5)
        return True
    except Exception:
        return False
