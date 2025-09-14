import json
from typing import Any, Dict
from .prompts import ANALYSIS_SYSTEM, ANALYSIS_USER_TEMPLATE, ANALYSIS_JSON_SCHEMA, FOLLOWUP_SYSTEM

def _truncate(s: str, max_chars: int = 60000) -> str:
    if len(s) <= max_chars:
        return s
    head = s[: max_chars // 2]
    tail = s[-max_chars // 2 :]
    return head + "\n...\n" + tail

def analyze_resume_against_jd(
    client,
    model: str,
    temperature: float,
    resume_text: str,
    jd_text: str,
    max_chars: int = 60000
) -> str:
    resume_text = _truncate(resume_text, max_chars)
    jd_text = _truncate(jd_text, max_chars)

    user_msg = ANALYSIS_USER_TEMPLATE.format(
        resume=resume_text,
        jd=jd_text,
        schema=ANALYSIS_JSON_SCHEMA
    )

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    )
    return resp.choices[0].message.content

def ask_followup(
    client,
    model: str,
    temperature: float,
    resume_text: str,
    jd_text: str,
    analysis_json: Dict[str, Any],
    user_question: str,
) -> str:
    context_blob = json.dumps(analysis_json, ensure_ascii=False)
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": FOLLOWUP_SYSTEM},
            {"role": "user", "content": f"User question: {user_question}"},
            {"role": "user", "content": f"Analysis JSON: {context_blob}"},
            {"role": "user", "content": f"Resume snippet:\n{resume_text[:4000]}"},
            {"role": "user", "content": f"JD snippet:\n{jd_text[:4000]}"},
        ],
    )
    return resp.choices[0].message.content
