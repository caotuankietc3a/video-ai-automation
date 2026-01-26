from __future__ import annotations

import os
import random
import urllib.request

import speech_recognition
from playwright.async_api import Page

try:
    import pydub
except ImportError:
    pydub = None

TEMP_DIR = os.getenv("TEMP") if os.name == "nt" else "/tmp"
TIMEOUT_MS = 7000
TIMEOUT_DETECTION_MS = 50


async def solve_recaptcha(page: Page) -> None:
    checkbox_frame = page.frame_locator('iframe[title="reCAPTCHA"]')
    await checkbox_frame.locator(".rc-anchor-content").first.wait_for(state="visible", timeout=TIMEOUT_MS)
    await page.wait_for_timeout(100)
    await checkbox_frame.locator(".rc-anchor-content").first.click()
    await page.wait_for_timeout(300)

    if await _is_solved(page):
        return

    challenge_frame = page.frame_locator('iframe[src*="bframe"]')
    await challenge_frame.locator("#recaptcha-audio-button").wait_for(state="visible", timeout=TIMEOUT_MS)
    await challenge_frame.locator("#recaptcha-audio-button").click()
    await page.wait_for_timeout(300)

    if await _is_detected(page):
        raise RuntimeError("reCAPTCHA phát hiện bot")

    await challenge_frame.locator("#audio-source").wait_for(state="visible", timeout=TIMEOUT_MS)
    src = await challenge_frame.locator("#audio-source").get_attribute("src")
    if not src:
        raise RuntimeError("Không lấy được URL audio reCAPTCHA")

    text_response = _process_audio_challenge(src)
    await challenge_frame.locator("#audio-response").fill(text_response.lower())
    await challenge_frame.locator("#recaptcha-verify-button").click()
    await page.wait_for_timeout(400)

    if not await _is_solved(page):
        raise RuntimeError("Giải reCAPTCHA audio thất bại")


async def _is_solved(page: Page) -> bool:
    try:
        checkbox_frame = page.frame_locator('iframe[title="reCAPTCHA"]')
        style = await checkbox_frame.locator(".recaptcha-checkbox-checkmark").get_attribute("style")
        return style is not None and len(style) > 0
    except Exception:
        return False


async def _is_detected(page: Page) -> bool:
    try:
        loc = page.get_by_text("Try again later", exact=False)
        await loc.wait_for(state="visible", timeout=TIMEOUT_DETECTION_MS)
        return True
    except Exception:
        return False


def _process_audio_challenge(audio_url: str) -> str:
    if pydub is None:
        raise RuntimeError("Cần cài pydub để giải reCAPTCHA audio: pip install pydub")
    mp3_path = os.path.join(TEMP_DIR, f"{random.randrange(1, 100000)}.mp3")
    wav_path = os.path.join(TEMP_DIR, f"{random.randrange(1, 100000)}.wav")
    try:
        urllib.request.urlretrieve(audio_url, mp3_path)
        sound = pydub.AudioSegment.from_mp3(mp3_path)
        sound.export(wav_path, format="wav")
        recognizer = speech_recognition.Recognizer()
        with speech_recognition.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio)
        except Exception:
            try:
                return recognizer.recognize_sphinx(audio)
            except Exception as e2:
                raise RuntimeError(
                    "Nhận dạng audio thất bại (Google và Sphinx). "
                    "Cài fallback offline: pip install pocketsphinx"
                ) from e2
    finally:
        for path in (mp3_path, wav_path):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


async def recaptcha_visible(page: Page) -> bool:
    try:
        await page.frame_locator('iframe[title="reCAPTCHA"]').locator(".rc-anchor-content").first.wait_for(
            state="visible", timeout=500
        )
        return True
    except Exception:
        return False
