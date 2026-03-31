import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

import google.generativeai as genai

from ..auth.auth_routes import get_current_user
from ..db.mongo import get_mongo_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai"])

load_dotenv()

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
_gemini_ready = False
_model = None
_active_model_name = None


def _unique_keep_order(values: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for value in values:
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _discover_generation_models() -> List[str]:
    discovered: List[str] = []
    try:
        for m in genai.list_models():
            methods = getattr(m, "supported_generation_methods", []) or []
            if "generateContent" not in methods:
                continue
            name = getattr(m, "name", "")
            if not name:
                continue
            discovered.append(name)
            if name.startswith("models/"):
                discovered.append(name.split("models/", 1)[1])
    except Exception as exc:
        logger.warning("Could not discover Gemini models via API: %s", exc)
    return _unique_keep_order(discovered)


def _candidate_models() -> List[str]:
    common = [
        _GEMINI_MODEL,
        "gemini-pro",
        "models/gemini-pro",
        "gemini-1.5-flash",
        "models/gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "models/gemini-1.5-flash-latest",
        "gemini-2.0-flash",
        "models/gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "models/gemini-2.0-flash-lite",
    ]
    discovered = _discover_generation_models()
    return _unique_keep_order(common + discovered)

if _GEMINI_API_KEY:
    try:
        genai.configure(api_key=_GEMINI_API_KEY)
        _gemini_ready = True
        _active_model_name = _GEMINI_MODEL
    except Exception as exc:
        logger.error("Gemini initialization failed: %s", exc)
else:
    logger.warning("Gemini API key missing. Set GEMINI_API_KEY or GOOGLE_GEMINI_API_KEY")


def generate_insight(data: Dict[str, Any]) -> str:
    """Generate a short safety insight from latest environmental data."""
    if not _gemini_ready or _model is None:
        return "AI temporarily unavailable: Gemini key not configured"

    try:
        prompt = f"""
Analyze this environmental data:

Temperature: {data.get('temperature')}
Humidity: {data.get('humidity')}
Gas: {data.get('gas_ppm')}
Risk: {data.get('risk_level') or data.get('risk_local')}

Provide a short safety insight.
"""
        response = _generate_with_fallback(prompt)
        return (response.text or "No insight available").strip()
    except Exception as exc:
        return f"AI temporarily unavailable: {str(exc)}"


def _generate_with_fallback(prompt: str):
    """Generate content and transparently retry with compatible account models."""
    global _model, _active_model_name

    if not _gemini_ready:
        raise RuntimeError("Gemini is not configured")

    candidates = _candidate_models()
    if _active_model_name:
        candidates = _unique_keep_order([_active_model_name] + candidates)

    last_error: Optional[Exception] = None
    tried: List[str] = []
    for candidate in candidates:
        tried.append(candidate)
        try:
            trial = genai.GenerativeModel(candidate)
            response = trial.generate_content(prompt)
            _model = trial
            _active_model_name = candidate
            if len(tried) > 1:
                logger.warning("Gemini model switched to compatible model: %s", candidate)
            return response
        except Exception as exc:
            last_error = exc
            continue

    if last_error is None:
        raise RuntimeError("No compatible Gemini model found.")

    raise RuntimeError(
        "No compatible Gemini model found for this API key/project. "
        f"Tried: {', '.join(tried[:8])}. Last error: {last_error}"
    )

class ChatRequest(BaseModel):
    query: Optional[str] = None
    message: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)

class ChatResponse(BaseModel):
    response: str


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_query(request: ChatRequest) -> str:
    return (request.query or request.message or "").strip()


def _trend_from_readings(readings: List[Dict[str, Any]], field: str) -> str:
    if len(readings) < 2:
        return "insufficient data"
    values: List[float] = []
    for row in readings:
        v = _as_float(row.get(field))
        if v is not None:
            values.append(v)
    if len(values) < 2:
        return "insufficient data"
    delta = values[0] - values[-1]
    if abs(delta) < 0.3:
        return "stable"
    if delta > 0:
        return f"rising ({delta:.1f})"
    return f"falling ({abs(delta):.1f})"


def _assess_severity(latest: Dict[str, Any], active_alerts: List[Dict[str, Any]]) -> str:
    temperature = _as_float(latest.get("temperature"))
    humidity = _as_float(latest.get("humidity"))
    gas_ppm = _as_float(latest.get("gas_ppm") or latest.get("gas"))

    has_danger_alert = any((a.get("severity") == "danger") and not a.get("is_resolved") for a in active_alerts)
    has_warning_alert = any((a.get("severity") == "warning") and not a.get("is_resolved") for a in active_alerts)

    if has_danger_alert or (temperature is not None and temperature > 45) or (gas_ppm is not None and gas_ppm > 250):
        return "CRITICAL"
    if has_warning_alert or (temperature is not None and temperature > 38) or (gas_ppm is not None and gas_ppm > 180) or (humidity is not None and humidity > 85):
        return "CAUTION"
    return "SAFE"


def _build_safety_recommendations(latest: Dict[str, Any], active_alerts: List[Dict[str, Any]]) -> List[str]:
    recommendations: List[str] = []

    temperature = _as_float(latest.get("temperature"))
    humidity = _as_float(latest.get("humidity"))
    gas_ppm = _as_float(latest.get("gas_ppm") or latest.get("gas"))

    if temperature is not None and temperature > 45:
        recommendations.append("Temperature is high. Move to shade, hydrate, and reduce exposure time.")
    if gas_ppm is not None and gas_ppm > 250:
        recommendations.append("Gas concentration is elevated. Ventilate immediately and keep ignition sources away.")
    if humidity is not None and humidity > 85:
        recommendations.append("High humidity detected. Use ventilation/dehumidification to prevent condensation risks.")

    if active_alerts:
        recommendations.append(
            f"There are {len(active_alerts)} active alerts. Prioritize unresolved danger-level alerts first."
        )

    if not recommendations:
        recommendations.append("Conditions look stable. Continue monitoring and keep regular sensor checks.")

    return recommendations[:4]


def _compose_prompt(
    user_query: str,
    context: Dict[str, Any],
    latest: Dict[str, Any],
    recent_readings: List[Dict[str, Any]],
    active_alerts: List[Dict[str, Any]],
    recommendations: List[str],
    severity: str,
) -> str:
    trend_temperature = _trend_from_readings(recent_readings, "temperature")
    trend_humidity = _trend_from_readings(recent_readings, "humidity")
    trend_gas = _trend_from_readings(recent_readings, "gas_ppm")

    alerts_lines: List[str] = []
    for item in active_alerts:
        alerts_lines.append(
            f"- [{item.get('severity', 'warning')}] {item.get('alert_type', 'ALERT')}: {item.get('message', '')}"
        )
    alerts_text = "\n".join(alerts_lines) if alerts_lines else "- None"

    recs_text = "\n".join([f"- {r}" for r in recommendations]) if recommendations else "- Continue monitoring"

    context_text = "\n".join([f"- {k}: {v}" for k, v in (context or {}).items()]) or "- None"

    return f"""
You are an environmental safety AI.

IMPORTANT RULES:
- Prioritize CURRENT sensor data over old alerts
- If values are normal -> system is SAFE
- Alerts may be historical unless clearly active
- Do NOT exaggerate danger

CURRENT SENSOR DATA:
Temperature: {latest.get('temperature')}
Humidity: {latest.get('humidity')}
Gas: {latest.get('gas_ppm')}
Pressure: {latest.get('pressure')}
Risk Local: {latest.get('risk_local')}

ACTIVE ALERTS:
{alerts_text}

TREND (LAST 5 READINGS):
Temperature trend: {trend_temperature}
Humidity trend: {trend_humidity}
Gas trend: {trend_gas}

DERIVED SEVERITY:
{severity}

SAFETY RECOMMENDATIONS CONTEXT:
{recs_text}

DASHBOARD CONTEXT:
{context_text}

USER QUESTION:
{user_query}

TASK:
1. Determine current status (SAFE / WARNING / CRITICAL)
2. Explain briefly
3. Give only necessary actions (no panic unless critical)

Keep response realistic and not overly alarming.
"""


async def _get_runtime_context(current_user: dict, context: Dict[str, Any]):
    db = get_mongo_db()
    user_id = str(current_user.get("_id") or current_user.get("id"))

    latest_query = {"user_id": user_id}
    device_id = context.get("device_id") if isinstance(context, dict) else None
    if device_id:
        latest_query["device_id"] = device_id

    latest = await db.sensor_data.find_one(latest_query, sort=[("timestamp", -1)]) or {}

    recent_readings: List[Dict[str, Any]] = []
    recent_cursor = db.sensor_data.find(latest_query).sort("_id", -1).limit(5)
    async for row in recent_cursor:
        recent_readings.append(row)

    alert_query: Dict[str, Any] = {
        "user_id": user_id,
        "status": "active",
    }
    if device_id:
        alert_query["device_id"] = device_id

    active_alerts: List[Dict[str, Any]] = []
    cursor = db.alerts.find(alert_query).sort("timestamp", -1).limit(3)
    async for alert in cursor:
        active_alerts.append(alert)

    return latest, recent_readings, active_alerts


async def _handle_chat(request: ChatRequest, current_user: dict):
    user_query = _extract_query(request)
    if not user_query:
        friendly = "Please ask a question like: 'Is my environment safe right now?'"
        return {
            "response": friendly,
            "reply": friendly,
        }

    if not _gemini_ready:
        return {
            "response": "AI temporarily unavailable: Gemini is not configured.",
            "reply": "AI temporarily unavailable: Gemini is not configured.",
        }

    try:
        latest, recent_readings, active_alerts = await _get_runtime_context(current_user, request.context)
        severity = _assess_severity(latest, active_alerts)
        recommendations = _build_safety_recommendations(latest, active_alerts)
        prompt = _compose_prompt(
            user_query=user_query,
            context=request.context,
            latest=latest,
            recent_readings=recent_readings,
            active_alerts=active_alerts,
            recommendations=recommendations,
            severity=severity,
        )
        chat_response = _generate_with_fallback(prompt)
        text_response = (chat_response.text or "No response generated.").strip()

        db = get_mongo_db()
        chat_doc = {
            "user_id": str(current_user.get("_id") or current_user.get("id")),
            "query": user_query,
            "response": text_response,
            "context": request.context,
            "timestamp": datetime.utcnow(),
        }
        await db.chat_history.insert_one(chat_doc)

        return {
            "response": text_response,
            "reply": text_response,
        }
    except Exception as exc:
        logger.error("Chatbot error: %s", exc)
        safe_msg = f"AI temporarily unavailable: {str(exc)}"
        return {
            "response": safe_msg,
            "reply": safe_msg,
        }

@router.post("/api/ai/chat", response_model=ChatResponse)
async def ai_chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    payload = await _handle_chat(request, current_user)
    return ChatResponse(response=payload["response"])


@router.post("/api/chat")
async def api_chat_alias(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Compatibility route expected by some frontend clients."""
    payload = await _handle_chat(request, current_user)
    return {"reply": payload["reply"]}
