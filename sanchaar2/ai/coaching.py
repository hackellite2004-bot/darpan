from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from secrets import choice
from typing import Any

# Ensure sanchaar2 directory is in path for imports
_SANCHAAR2_DIR = Path(__file__).parent.parent
if str(_SANCHAAR2_DIR) not in sys.path:
    sys.path.insert(0, str(_SANCHAAR2_DIR))

from config import GEMINI_MODEL

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover
    genai = None
    types = None

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None


def _extract_json_array(text: str) -> list[str]:
    try:
        payload = json.loads(text)
        if isinstance(payload, list):
            return [str(item) for item in payload]
    except Exception:
        pass

    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        return []
    try:
        payload = json.loads(match.group(0))
        if isinstance(payload, list):
            return [str(item) for item in payload]
    except Exception:
        return []
    return []


def _gemini_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or genai is None:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def _fallback_tips(session_metrics: dict[str, Any], user_name: str, age_group: str) -> list[str]:
    score = float(session_metrics.get("confidence_score") or 0.0)
    eye = float(session_metrics.get("eye_center_pct") or 0.0)
    posture = float(session_metrics.get("posture_score") or 0.0)
    wpm = float(session_metrics.get("wpm") or 0.0)
    fillers = int(session_metrics.get("total_fillers") or 0)
    tips = [
        f"Strong effort, {user_name}. You scored {score:.0f}/100, so you already have a base that can improve quickly with practice.",
        f"Your eye contact is {eye:.0f}%. In real interviews, hold camera contact for one full sentence before glancing away to think.",
        f"Your posture score is {posture:.0f}%. Stand like you are introducing yourself on stage: shoulders relaxed, chest open, chin level.",
        f"You spoke at {wpm:.0f} WPM with {fillers} fillers. Use a silent 1-second pause after key points, like presenters do in team meetings.",
    ]
    return tips[:4]


def generate_coaching_tips(session_metrics: dict[str, Any], user_name: str, age_group: str) -> list[str]:
    model = _gemini_model()
    if model is None:
        return _fallback_tips(session_metrics, user_name, age_group)

    try:
        coaching_angles = [
            "presentation in a classroom",
            "answering a job interview question",
            "speaking up in a team meeting",
            "introducing yourself to a new person",
            "explaining an idea to a parent or teacher",
        ]
        angle = choice(coaching_angles)
        prompt = f"""
You are a warm, encouraging communication coach working with a {age_group} student named {user_name}.
Write feedback as if you were coaching them after a real-life {angle}.

Here are their session metrics:
- Confidence score: {session_metrics['confidence_score']:.0f}/100
- Dominant emotion: {session_metrics['dominant_emotion']}
- Eye contact (center): {session_metrics['eye_center_pct']:.0f}%
- Posture good: {session_metrics['posture_score']:.0f}%
- Speaking speed: {session_metrics['wpm']:.0f} WPM
- Filler words used: {session_metrics['total_fillers']} times
- Most used filler: {session_metrics.get('top_filler', 'none')}
- Long pauses: {session_metrics['pause_count']}
- Voice monotone: {session_metrics['is_monotone']}
- Gesture style: {session_metrics['gesture_type']}

Give exactly 4 coaching tips.
Rules:
1. Be specific and mention their actual numbers.
2. Be encouraging and start with what they did well.
3. Use simple language appropriate for {age_group}.
4. Each tip must be 1-2 sentences only.
5. Each tip must include one practical real-life example.
6. Avoid generic phrases like "keep it up" or "do better".
7. Return ONLY a JSON array of 4 strings, nothing else.
"""
        config = types.GenerateContentConfig(temperature=0.9, top_p=0.95, top_k=40, max_output_tokens=500) if types is not None else None
        response = model.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=config)
        text = getattr(response, "text", "") or ""
        tips = _extract_json_array(text)
        if isinstance(tips, list):
            cleaned = [str(tip).strip() for tip in tips if str(tip).strip()]
            if len(cleaned) >= 4:
                return cleaned[:4]
        return _fallback_tips(session_metrics, user_name, age_group)
    except Exception:
        return _fallback_tips(session_metrics, user_name, age_group)


def generate_interview_question(context: str, question_number: int, age_group: str) -> str:
    model = _gemini_model()
    if model is None:
        fallback_questions = [
            f"Tell me about yourself for a {context.lower()} setting.",
            "Describe a time you worked well with others.",
            "How do you stay calm when something goes wrong?",
            "What would you do if a deadline changed at the last minute?",
            "Why are you interested in this opportunity?",
        ]
        return fallback_questions[(question_number - 1) % len(fallback_questions)]

    try:
        scenario_map = {
            1: "opening self-introduction",
            2: "handling pressure or deadlines",
            3: "working with a teammate or classmate",
            4: "solving a conflict or disagreement",
            5: "showing motivation or future goals",
        }
        prompt = f"""
Generate interview question #{question_number} of 5 for a {age_group} student practicing for: {context}.
The scenario focus is: {scenario_map.get(question_number, 'a realistic interview situation')}.
Rules:
- Situational or behavioral question
- Appropriate for {age_group}
- Clear and specific
- Should feel like a real interview or real conversation scenario
- Do not repeat the common template phrasing used in earlier questions.
- Return ONLY the question text, nothing else.
"""
        config = types.GenerateContentConfig(temperature=1.0, top_p=0.95, top_k=40, max_output_tokens=120) if types is not None else None
        response = model.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=config)
        text = (getattr(response, "text", "") or "").strip()
        return text if text else f"Describe a time you handled a challenge in a {context.lower()} setting."
    except Exception:
        return f"Describe a time you handled a challenge in a {context.lower()} setting."


def generate_face_impression(session_metrics: dict[str, Any], user_name: str, age_group: str, face_frame=None) -> dict[str, Any]:
    model = _gemini_model()
    if model is None or face_frame is None or Image is None:
        emotion = str(session_metrics.get("emotion_dominant") or "neutral")
        return {
            "summary": f"Your face looks {emotion} overall.",
            "confidence": float(session_metrics.get("emotion_neutral") or 0.5),
            "what_it_says": "The expression looks steady enough for a normal conversation.",
            "real_life_example": "This is close to how you might look when listening to a teacher explain homework.",
        }

    try:
        image = Image.fromarray(face_frame)
        prompt = f"""
Analyze this face for a communication-skills app.
The person is a {age_group} learner named {user_name}.

Return a JSON object with these keys:
- summary: 1 short sentence describing the overall facial impression.
- confidence: a number from 0 to 1.
- what_it_says: what the expression suggests in a real-life speaking situation.
- real_life_example: a simple real-life example where this facial impression would fit.

Rules:
1. Be practical and human, not robotic.
2. Avoid saying the person is "bad" or "wrong".
3. If the face looks neutral, say it looks calm, attentive, or thoughtful.
4. Return ONLY valid JSON.
"""
        config = types.GenerateContentConfig(temperature=0.7, top_p=0.9, top_k=32, max_output_tokens=220) if types is not None else None
        response = model.models.generate_content(model=GEMINI_MODEL, contents=[prompt, image], config=config)
        text = getattr(response, "text", "") or ""
        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                return payload
        except Exception:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                payload = json.loads(match.group(0))
                if isinstance(payload, dict):
                    return payload
        return {
            "summary": "Your face looks calm and attentive.",
            "confidence": 0.6,
            "what_it_says": "It suggests you are listening and thinking before you speak.",
            "real_life_example": "This is the kind of expression people use during a serious classroom discussion.",
        }
    except Exception:
        return {
            "summary": "Your face looks calm and attentive.",
            "confidence": 0.6,
            "what_it_says": "It suggests you are listening and thinking before you speak.",
            "real_life_example": "This is the kind of expression people use during a serious classroom discussion.",
        }


def _fallback_session_assessment(session_metrics: dict[str, Any], user_name: str, age_group: str) -> dict[str, Any]:
    score = float(session_metrics.get("confidence_score") or 0.0)
    quality = float(session_metrics.get("analysis_quality_score") or 0.0)
    dominant_emotion = str(session_metrics.get("emotion_dominant") or "neutral")
    confidence_label = "uncertain" if quality < 45 or score < 55 else "moderate"
    if score >= 80 and quality >= 70:
        confidence_label = "confident"
    if score >= 80:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 55:
        grade = "C"
    else:
        grade = "D"
    return {
        "final_score": round(score, 2),
        "grade": grade,
        "confidence_label": confidence_label,
        "quality_score": round(quality, 2),
        "dominant_emotion": dominant_emotion,
        "overall_summary": f"The session looks {dominant_emotion} overall, with the strongest signals coming from the local video and speech analyzers.",
        "strengths": [
            f"{user_name} showed a measurable communication baseline for a {age_group} learner.",
            f"Eye contact, posture, and speech timing produced a usable signal for analysis.",
            f"The current recording is good enough to give practical coaching feedback.",
        ],
        "improvements": [
            "Record in brighter light and keep the face centered for clearer vision results.",
            "Hold one sentence at a time so the app can read expression changes more reliably.",
            "Use a short calibration clip first to give the model a better personal baseline.",
        ],
        "evidence_used": [
            f"Confidence score estimate: {score:.0f}/100.",
            f"Analysis quality estimate: {quality:.0f}/100.",
            f"Dominant emotion estimate: {dominant_emotion}.",
        ],
        "face_summary": "Face impression was approximated from the available frame and local emotion signals.",
        "eye_contact_summary": f"Eye contact was about {float(session_metrics.get('eye_center_pct') or 0.0):.0f}% center.",
        "posture_summary": f"Posture score was {float(session_metrics.get('posture_score') or 0.0) * 100.0:.0f}%.",
        "speech_summary": f"Speech speed was {float(session_metrics.get('wpm') or 0.0):.0f} WPM with {int(session_metrics.get('total_fillers') or session_metrics.get('filler_count') or 0)} fillers.",
        "gesture_summary": f"Gesture style was {str(session_metrics.get('gesture_type') or 'neutral')}.",
        "uncertainty_reason": "The model service was unavailable, so this summary falls back to local signals.",
        "public_ready_tip": "For a public demo, run one short calibration recording first so the next analysis is more personal and less generic.",
    }


def generate_session_assessment(
    session_metrics: dict[str, Any],
    user_name: str,
    age_group: str,
    face_frames: list[Any] | None = None,
    transcript: str = "",
    analysis_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = _gemini_model()
    frames = [frame for frame in (face_frames or []) if frame is not None]
    if model is None:
        return _fallback_session_assessment(session_metrics, user_name, age_group)

    try:
        images = [Image.fromarray(frame) for frame in frames[:3]] if Image is not None else []
        profile = analysis_profile or {}
        prompt = f"""
You are a strict but fair communication-analysis judge for a public hackathon demo.
Assess the recording using ONLY the evidence in the provided metrics, transcript, and images.

Rules:
1. Do not guess beyond the visible evidence.
2. If the image quality or signals are weak, use confidence_label = "uncertain".
3. Treat sad, neutral, and calm expressions as valid human expressions, not failures.
4. Be specific, practical, and concise.
5. Return ONLY valid JSON.

User: {user_name}
Age group: {age_group}

Metrics:
- confidence_score_guess: {float(session_metrics.get('confidence_score') or 0.0):.2f}
- quality_guess: {float(session_metrics.get('analysis_quality_score') or 0.0):.2f}
- reliability_profile: {json.dumps(profile, default=str)}
- eye_center_pct: {float(session_metrics.get('eye_center_pct') or 0.0):.2f}
- eye_away_pct: {float(session_metrics.get('eye_away_pct') or 0.0):.2f}
- blink_count: {int(session_metrics.get('blink_count') or 0)}
- posture_score: {float(session_metrics.get('posture_score') or 0.0):.2f}
- slouch_pct: {float(session_metrics.get('slouch_pct') or 0.0):.2f}
- gesture_positive_pct: {float(session_metrics.get('gesture_positive_pct') or 0.0):.2f}
- gesture_nervous_pct: {float(session_metrics.get('gesture_nervous_pct') or 0.0):.2f}
- wpm: {float(session_metrics.get('wpm') or 0.0):.2f}
- filler_count: {int(session_metrics.get('filler_count') or session_metrics.get('total_fillers') or 0)}
- pause_count: {int(session_metrics.get('pause_count') or 0)}
- emotion_happy: {float(session_metrics.get('emotion_happy') or 0.0):.2f}
- emotion_neutral: {float(session_metrics.get('emotion_neutral') or 0.0):.2f}
- emotion_sad: {float(session_metrics.get('emotion_sad') or 0.0):.2f}
- emotion_anxious: {float(session_metrics.get('emotion_anxious') or 0.0):.2f}
- emotion_surprised: {float(session_metrics.get('emotion_surprised') or 0.0):.2f}
- dominant_emotion_guess: {session_metrics.get('emotion_dominant')}

Transcript excerpt:
{transcript[:1200] if transcript else 'No transcript available.'}

Return a JSON object with these keys:
- final_score: number from 0 to 100
- grade: A, B, C, or D
- confidence_label: uncertain, moderate, or confident
- quality_score: number from 0 to 100
- dominant_emotion: one word label
- overall_summary: one short paragraph
- strengths: array of 3 short strings
- improvements: array of 3 short strings
- evidence_used: array of 3 to 5 short strings
- face_summary: one short sentence
- eye_contact_summary: one short sentence
- posture_summary: one short sentence
- speech_summary: one short sentence
- gesture_summary: one short sentence
- uncertainty_reason: short string explaining uncertainty if any
- public_ready_tip: one short practical tip for the user
"""
        config = types.GenerateContentConfig(temperature=0.4, top_p=0.85, top_k=32, max_output_tokens=650) if types is not None else None
        contents = [prompt, *images] if images else prompt
        response = model.models.generate_content(model=GEMINI_MODEL, contents=contents, config=config)
        text = getattr(response, "text", "") or ""
        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                return payload
        except Exception:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                payload = json.loads(match.group(0))
                if isinstance(payload, dict):
                    return payload
        return _fallback_session_assessment(session_metrics, user_name, age_group)
    except Exception:
        return _fallback_session_assessment(session_metrics, user_name, age_group)


def build_json_message(items: list[str]) -> str:
    return json.dumps(items)
