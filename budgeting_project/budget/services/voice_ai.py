"""Voice transaction analysis via Google Gemini (speech + extraction)."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from django.conf import settings
from django.utils import timezone

from budget.data.categories import get_category_by_name, load_categories


class VoiceAIError(Exception):
    """Raised when voice AI processing fails."""


# Prefer models that work on free-tier keys; 2.0-flash often hits quota (429).
_GEMINI_MODEL_FALLBACKS = (
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-2.0-flash",
)


_CATEGORY_ALIASES: dict[str, str] = {
    "food": "Food & Dining",
    "dining": "Food & Dining",
    "mcdonalds": "Food & Dining",
    "mcdonald's": "Food & Dining",
    "macdonalds": "Food & Dining",
    "أكل": "Food & Dining",
    "اكل": "Food & Dining",
    "مطعم": "Food & Dining",
    "groceries": "Groceries",
    "بقالة": "Groceries",
    "transport": "Transportation",
    "transportation": "Transportation",
    "مواصلات": "Transportation",
    "أوبر": "Transportation",
    "اوبر": "Transportation",
    "taxi": "Transportation",
    "uber": "Transportation",
    "fuel": "Transportation",
    "benzine": "Transportation",
    "بنزين": "Transportation",
    "rent": "Housing & Rent",
    "housing": "Housing & Rent",
    "إيجار": "Housing & Rent",
    "bills": "Bills & Utilities",
    "utilities": "Bills & Utilities",
    "فاتورة": "Bills & Utilities",
    "health": "Healthcare",
    "healthcare": "Healthcare",
    "medical": "Healthcare",
    "صحة": "Healthcare",
    "shopping": "Shopping",
    "تسوق": "Shopping",
    "entertainment": "Entertainment",
    "ترفيه": "Entertainment",
    "education": "Education",
    "تعليم": "Education",
    "fitness": "Fitness",
    "gym": "Fitness",
    "subscriptions": "Subscriptions",
    "subscription": "Subscriptions",
    "اشتراك": "Subscriptions",
    "travel": "Travel",
    "سفر": "Travel",
    "salary": "Salary",
    "مرتب": "Salary",
    "راتب": "Salary",
    "freelance": "Freelance",
    "business": "Business Income",
    "investment": "Investments",
    "investments": "Investments",
    "bonus": "Bonuses",
    "bonuses": "Bonuses",
    "gift": "Gifts",
    "gifts": "Gifts",
    "side hustle": "Side Hustle",
}


def _category_lists() -> tuple[list[str], list[str]]:
    expense = [c["name"] for c in load_categories() if c["type"] == "expense"]
    income = [c["name"] for c in load_categories() if c["type"] == "income"]
    return expense, income


def _build_prompt(transcript: str | None = None) -> str:
    expense, income = _category_lists()
    today = timezone.localdate().isoformat()
    text_block = f'\nSpoken text:\n"{transcript}"\n' if transcript else ""
    return f"""You are a financial assistant for a personal budgeting app (SmartFinance).
Listen to the audio OR read the text and extract ONE financial transaction.

Return ONLY valid JSON (no markdown) with these fields:
- transcript: exact words the user spoke (Arabic or English)
- type: "expense" or "income"
- amount: number (EGP, no currency symbol)
- category: MUST be exactly one name from the allowed lists below
- description: short note in the same language as the user (merchant or purpose)
- date: ISO date YYYY-MM-DD (use {today} if user says today/النهارده; yesterday=امبارح)

Allowed expense categories:
{json.dumps(expense, ensure_ascii=False)}

Allowed income categories:
{json.dumps(income, ensure_ascii=False)}

Examples:
- "I paid 250 EGP for food at McDonald's today" -> expense, 250, Food & Dining, McDonald's
- "I received 5000 EGP salary" -> income, 5000, Salary
{text_block}"""


def _parse_json_response(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise VoiceAIError("AI returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise VoiceAIError("AI response must be a JSON object.")
    return data


def _normalize_category(raw: str, txn_type: str) -> str:
    if not raw:
        default = "Other Expense" if txn_type == "expense" else "Other Income"
        return default

    name = raw.strip()
    if get_category_by_name(name):
        return name

    key = name.lower()
    if key in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[key]

    for alias, canonical in _CATEGORY_ALIASES.items():
        if alias in key or key in alias:
            return canonical

    expense, income = _category_lists()
    pool = expense if txn_type == "expense" else income
    for candidate in pool:
        if candidate.lower() in key or key in candidate.lower():
            return candidate

    return "Other Expense" if txn_type == "expense" else "Other Income"


def _normalize_transaction(data: dict[str, Any]) -> dict[str, Any]:
    txn_type = str(data.get("type", "expense")).lower().strip()
    if txn_type not in ("expense", "income"):
        txn_type = "expense"

    amount_raw = data.get("amount")
    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            raise VoiceAIError("Amount must be greater than zero.")
    except (InvalidOperation, TypeError) as exc:
        raise VoiceAIError("Could not parse transaction amount.") from exc

    category = _normalize_category(str(data.get("category", "")), txn_type)
    description = str(data.get("description", "") or "").strip()[:500]

    date_str = str(data.get("date", "") or "").strip()
    try:
        txn_date = date.fromisoformat(date_str) if date_str else timezone.localdate()
    except ValueError:
        txn_date = timezone.localdate()

    return {
        "type": txn_type,
        "amount": float(amount),
        "category": category,
        "description": description,
        "date": txn_date.isoformat(),
    }


def _model_candidates() -> list[str]:
    preferred = getattr(settings, "GEMINI_MODEL", "") or ""
    names: list[str] = []
    if preferred:
        names.append(preferred.strip())
    for name in _GEMINI_MODEL_FALLBACKS:
        if name not in names:
            names.append(name)
    return names


def _extract_response_text(response: Any) -> str:
    try:
        text = (response.text or "").strip()
        if text:
            return text
    except Exception:
        pass

    try:
        candidates = response.candidates or []
        if candidates:
            parts = candidates[0].content.parts or []
            chunks = [getattr(p, "text", "") for p in parts if getattr(p, "text", "")]
            joined = "".join(chunks).strip()
            if joined:
                return joined
    except Exception:
        pass

    raise VoiceAIError("Gemini returned an empty response. Try speaking more clearly.")


def _gemini_error_message(exc: Exception) -> str:
    msg = str(exc)
    if "429" in msg or "quota" in msg.lower() or "ResourceExhausted" in type(exc).__name__:
        return (
            "Gemini API quota exceeded. Wait a minute and try again, "
            "or use a different API key / billing plan."
        )
    if "404" in msg or "not found" in msg.lower():
        return "Gemini model not available. Check GEMINI_MODEL in your .env file."
    if "API key" in msg or "API_KEY" in msg:
        return "Invalid Gemini API key. Update GEMINI_API_KEY in your .env file."
    return f"Gemini error: {msg[:200]}"


def _generate_with_fallback(contents: Any, max_tokens: int = 768) -> str:
    api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
    if not api_key:
        raise VoiceAIError("GEMINI_API_KEY is not configured. Add it to your .env file.")

    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise VoiceAIError("google-generativeai package is not installed.") from exc

    genai.configure(api_key=api_key)
    last_error: Exception | None = None

    for model_name in _model_candidates():
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                contents,
                generation_config={"temperature": 0.1, "max_output_tokens": max_tokens},
            )
            return _extract_response_text(response)
        except VoiceAIError:
            raise
        except Exception as exc:
            last_error = exc
            continue

    if last_error:
        raise VoiceAIError(_gemini_error_message(last_error)) from last_error
    raise VoiceAIError("No Gemini model could process this request.")


def _call_gemini_text(prompt: str) -> dict[str, Any]:
    raw = _generate_with_fallback(prompt, max_tokens=512)
    return _normalize_transaction(_parse_json_response(raw))


def _call_gemini_audio_raw(audio_bytes: bytes, mime_type: str) -> dict[str, Any]:
    prompt = _build_prompt()
    audio_part = {"mime_type": mime_type or "audio/webm", "data": audio_bytes}
    raw = _generate_with_fallback([prompt, audio_part], max_tokens=768)
    return _parse_json_response(raw)


def analyze_audio(audio_bytes: bytes, mime_type: str = "audio/webm") -> dict[str, Any]:
    """Transcribe + extract transaction from audio via Gemini."""
    if not audio_bytes:
        raise VoiceAIError("Audio file is empty.")
    if len(audio_bytes) > 10 * 1024 * 1024:
        raise VoiceAIError("Audio file is too large (max 10 MB).")

    allowed = {
        "audio/webm",
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/mp4",
        "audio/ogg",
    }
    mime = mime_type.split(";")[0].strip().lower() if mime_type else "audio/webm"
    if mime not in allowed:
        mime = "audio/webm"

    raw = _call_gemini_audio_raw(audio_bytes, mime)
    transcript = str(raw.get("transcript", "")).strip()
    txn = _normalize_transaction(raw)
    return {
        "transcript": transcript or txn.get("description", ""),
        "transaction": txn,
    }


def analyze_text(text: str) -> dict[str, Any]:
    """Extract transaction from plain text (fallback)."""
    text = text.strip()
    if not text:
        raise VoiceAIError("Text is empty.")
    prompt = _build_prompt(text)
    txn = _call_gemini_text(prompt)
    return {"transcript": text, "transaction": txn}
