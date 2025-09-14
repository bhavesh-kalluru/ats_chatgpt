REWRITE_SYSTEM = """You are ATS-ChatGPT specialized in precise rewrites.
Return plain text with concise, high-impact bullets or summary paragraphs tailored to the JD and the user's rewrite goal.
Prioritize specificity, action verbs, outcomes, and (X/Y/Z) quantification placeholders if the resume lacks numbers."""

REWRITE_USER_TPL = """Rewrite goal:
{goal}

Resume (plain text):
--------------------
{resume}

Job Description:
----------------
{jd}

Output:
- 3 to 6 concise bullets OR a 2-3 line summary (depending on the goal).
- Avoid generic phrasing; emphasize tools, skills, and outcomes relevant to the JD.
"""

def generate_rewrites(client, model: str, temperature: float, resume_text: str, jd_text: str, rewrite_goal: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": REWRITE_SYSTEM},
            {"role": "user", "content": REWRITE_USER_TPL.format(
                goal=rewrite_goal,
                resume=resume_text[:12000],
                jd=jd_text[:12000]
            )},
        ],
    )
    return resp.choices[0].message.content
