import json
import html

def safe_json(s: str | dict | None) -> dict | None:
    if s is None:
        return None
    if isinstance(s, dict):
        return s
    try:
        return json.loads(s)
    except Exception:
        return None

def badge(text: str, color: str = "#2E86C1") -> str:
    text = html.escape(text)
    return f"""<span style="
        display:inline-block;
        padding:2px 8px;
        border-radius:999px;
        background:{color};
        color:#fff;
        font-size:0.8rem;
        margin-right:6px;
    ">{text}</span>"""

def severity_color(sev: str) -> str:
    s = (sev or "").lower()
    if s in ("high", "critical"):
        return "#C0392B"
    if s in ("med", "medium"):
        return "#D68910"
    return "#1E8449"

def make_markdown_report(data: dict) -> str:
    lines = []
    lines.append(f"# ATS Report\n")
    lines.append(f"**Overall ATS Score:** {round(data.get('ats_score_overall', 0))}/100\n")
    role = data.get("role_title_inferred", "")
    if role:
        lines.append(f"**Target Role (inferred):** {role}\n")

    lines.append("## Section Scores")
    for k, v in (data.get("section_scores", {}) or {}).items():
        lines.append(f"- **{k}:** {v}")

    lines.append("\n## Hard Requirements")
    hr = data.get("hard_requirements", {})
    lines.append(f"- Met: {'Yes' if hr.get('met') else 'No'}")
    for d in hr.get("details", []):
        lines.append(f"  - {d}")

    lines.append("\n## Keywords")
    lines.append(f"- **Matched:** {', '.join(data.get('matched_keywords', [])) or '—'}")
    lines.append(f"- **Missing (Critical):** {', '.join(data.get('missing_critical_keywords', [])) or '—'}")
    lines.append(f"- **Missing (Nice):** {', '.join(data.get('missing_nice_to_have_keywords', [])) or '—'}")

    kd = data.get("keyword_density", [])
    if kd:
        lines.append("\n### Keyword Density (Resume vs JD)")
        lines.append("| Keyword | Resume Freq | JD Freq |")
        lines.append("|---|---:|---:|")
        for row in kd:
            lines.append(f"| {row.get('keyword','')} | {row.get('resume_freq',0)} | {row.get('jd_freq',0)} |")

    if data.get("red_flags"):
        lines.append("\n## Red Flags")
        for r in data["red_flags"]:
            lines.append(f"- {r}")

    if data.get("recommendations"):
        lines.append("\n## Recommendations")
        for r in data["recommendations"]:
            lines.append(f"### {r.get('area','General')} ({r.get('severity','med').upper()})")
            lines.append(r.get("suggestion",""))
            if r.get("example_rewrite"):
                lines.append("\n**Example rewrite**\n")
                lines.append(r["example_rewrite"])

    if data.get("tailored_summary"):
        lines.append("\n## Tailored Professional Summary\n")
        lines.append(data["tailored_summary"])

    if data.get("tailored_bullets"):
        lines.append("\n## High-impact Bullet Suggestions")
        for i, b in enumerate(data["tailored_bullets"], 1):
            lines.append(f"{i}. {b}")

    return "\n".join(lines)
