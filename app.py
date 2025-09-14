import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))


import json
from pathlib import Path
import streamlit as st
import pandas as pd

from src.config import get_settings, init_openai_client
from src.parsing import extract_text_from_upload
from src.analyzer import analyze_resume_against_jd, ask_followup
from src.rewrite import generate_rewrites
from src.utils import badge, severity_color, safe_json, make_markdown_report

st.set_page_config(
    page_title="ATS ChatGPT — Smart Resume vs JD",
    page_icon="🧠",
    layout="wide"
)

# --------------------------- Header / Intro ---------------------------
st.markdown("""
<h1 style="margin-bottom:0">🧠 ATS ChatGPT — Resume vs Job Description</h1>
<p style="margin-top:0.5rem; font-size:1.05rem;">
Upload your resume (PDF/DOCX/TXT), paste or upload a job description, and get an ATS-style score with specific, actionable improvements —
plus AI-tailored bullets & summary. Designed to be brighter, stricter, and more helpful than typical ATS checkers.
</p>
""", unsafe_allow_html=True)

settings = get_settings()

with st.sidebar:
    st.header("⚙️ Settings")
    st.caption("Configure model/temperature and (optionally) override API key.")
    model = st.selectbox(
        "OpenAI Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
        index=0
    )
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
    api_key_override = st.text_input("OPENAI_API_KEY (optional)", type="password")

    st.write("---")
    st.write("**Tips**")
    st.caption("• Keep resume to 1–2 pages. • Paste the full JD. • Use ‘Follow-up Q&A’ to iterate.")

# --------------------------- Inputs ---------------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 Resume")
    resume_file = st.file_uploader("Upload resume (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])
    resume_text = ""
    if resume_file:
        with st.spinner("Extracting text from resume..."):
            resume_text = extract_text_from_upload(resume_file)
        if not resume_text.strip():
            st.error("Could not extract text from the uploaded resume. Please check the file.")
        else:
            st.success(f"Extracted ~{len(resume_text)} characters from resume.")

with col2:
    st.subheader("🧾 Job Description")
    jd_mode = st.radio("Provide JD", ["Paste text", "Upload .txt"], horizontal=True)
    jd_text = ""
    if jd_mode == "Paste text":
        jd_text = st.text_area("Paste job description", height=280, placeholder="Paste full job description here...")
    else:
        jd_file = st.file_uploader("Upload JD (.txt)", type=["txt"], key="jd_upload")
        if jd_file:
            jd_text = jd_file.read().decode("utf-8", errors="ignore")
            st.success(f"Loaded ~{len(jd_text)} characters from JD.")

analyze_clicked = st.button("🚀 Analyze Resume vs JD", type="primary", use_container_width=True)

# --------------------------- Run Analysis ---------------------------
if analyze_clicked:
    if not resume_text.strip() or not jd_text.strip():
        st.error("Please provide both a resume and a job description.")
    else:
        client = init_openai_client(api_key_override or settings.OPENAI_API_KEY)
        with st.spinner("Calling ATS brain..."):
            result = analyze_resume_against_jd(
                client=client,
                model=model,
                temperature=temperature,
                resume_text=resume_text,
                jd_text=jd_text
            )

        data = safe_json(result)
        if not data:
            st.error("The analyzer returned an unexpected format. Please try again.")
        else:
            # --------------------------- Overview ---------------------------
            st.success("Analysis complete!")
            st.subheader("📊 ATS Overview")

            score = data.get("ats_score_overall", 0)
            colA, colB, colC = st.columns([1, 2, 2])
            with colA:
                st.metric("ATS Score", f"{round(score)} / 100")
                st.progress(min(max(score / 100, 0), 1))

            with colB:
                role = data.get("role_title_inferred", "")
                hard_req = data.get("hard_requirements", {})
                met = hard_req.get("met", False)
                details = hard_req.get("details", [])
                st.markdown(f"**Target role inferred:** `{role or '—'}`")
                st.markdown(f"**Hard requirements met?** {'✅ Yes' if met else '❌ No'}")
                if details:
                    st.caption("Hard requirement checks:")
                    for d in details:
                        st.write(f"- {d}")

            with colC:
                red_flags = data.get("red_flags", [])
                if red_flags:
                    st.markdown("**⚠️ Potential red flags**")
                    for rf in red_flags:
                        st.write(f"- {rf}")
                else:
                    st.markdown("**No major red flags detected.**")

            # --------------------------- Section Scores ---------------------------
            st.write("---")
            st.subheader("🧩 Section Scores")
            sec = data.get("section_scores", {})
            if sec:
                df_scores = pd.DataFrame(
                    [{"Section": k, "Score": v} for k, v in sec.items()]
                ).sort_values("Score", ascending=False)
                st.dataframe(df_scores, use_container_width=True)

            # --------------------------- Keyword Analysis ---------------------------
            st.write("---")
            st.subheader("🔑 Keywords & Alignment")

            colk1, colk2 = st.columns(2)
            matched = data.get("matched_keywords", [])
            missing_critical = data.get("missing_critical_keywords", [])
            missing_nice = data.get("missing_nice_to_have_keywords", [])
            density = data.get("keyword_density", [])

            with colk1:
                st.markdown("**Matched (Resume ∩ JD)**")
                if matched:
                    st.write(", ".join(matched))
                else:
                    st.caption("No explicit matches found (may be phrased differently).")

                st.markdown("**Missing — Critical**")
                if missing_critical:
                    st.error(", ".join(missing_critical))
                else:
                    st.success("No critical keywords missing.")

                st.markdown("**Missing — Nice to have**")
                if missing_nice:
                    st.warning(", ".join(missing_nice))
                else:
                    st.success("All nice-to-have keywords present.")

            with colk2:
                st.markdown("**Keyword Density (Resume vs JD)**")
                if density:
                    df_kd = pd.DataFrame(density)
                    df_kd = df_kd.rename(columns={
                        "keyword": "Keyword",
                        "resume_freq": "Resume Freq",
                        "jd_freq": "JD Freq"
                    })
                    st.dataframe(df_kd, use_container_width=True)
                else:
                    st.caption("No density table produced.")

            # --------------------------- Recommendations ---------------------------
            st.write("---")
            st.subheader("🛠️ Recommendations & Example Rewrites")

            recs = data.get("recommendations", [])
            if recs:
                for r in recs:
                    area = r.get("area", "General")
                    sev = r.get("severity", "med")
                    sug = r.get("suggestion", "")
                    exr = r.get("example_rewrite", "")
                    st.markdown(
                        f"{badge(area)}  {badge(sev.upper(), color=severity_color(sev))}  \n\n{sug}"
                        , unsafe_allow_html=True
                    )
                    if exr:
                        with st.expander("Example rewrite"):
                            st.write(exr)
            else:
                st.caption("No recommendations produced.")

            # --------------------------- Tailored Summary & Bullets ---------------------------
            st.write("---")
            st.subheader("✨ Tailored Summary & Bullet Suggestions")
            ts = data.get("tailored_summary", "")
            tb = data.get("tailored_bullets", [])
            verbs = data.get("top_action_verbs", [])

            if ts:
                st.markdown("**Tailored Professional Summary**")
                st.write(ts)

            if tb:
                st.markdown("**High-impact Bullet Suggestions**")
                for i, bullet in enumerate(tb, 1):
                    st.write(f"{i}. {bullet}")

            if verbs:
                st.caption("Suggested action verbs to diversify your bullets:")
                st.write(", ".join(verbs))

            # --------------------------- Generate + Download Report ---------------------------
            st.write("---")
            st.subheader("📥 Export")

            md_report = make_markdown_report(data)
            st.download_button(
                "Download Full Report (Markdown)",
                data=md_report.encode("utf-8"),
                file_name="ats_report.md",
                mime="text/markdown",
                use_container_width=True
            )
            st.download_button(
                "Download Raw JSON",
                data=json.dumps(data, indent=2).encode("utf-8"),
                file_name="ats_report.json",
                mime="application/json",
                use_container_width=True
            )

            # --------------------------- Extra: On-demand rewrites ---------------------------
            st.write("---")
            st.subheader("🧩 On-Demand Rewrites (optional)")
            rewrite_goal = st.text_area(
                "Describe what you want rewritten (e.g., “Rewrite my summary to emphasize Generative AI and Azure MLOps”):",
                placeholder="What should the rewrite emphasize or change?"
            )
            if st.button("Generate Rewrites", use_container_width=True):
                if not rewrite_goal.strip():
                    st.warning("Please describe your rewrite goal.")
                else:
                    with st.spinner("Generating tailored rewrites..."):
                        rewrites = generate_rewrites(
                            client=client, model=model, temperature=temperature,
                            resume_text=resume_text, jd_text=jd_text, rewrite_goal=rewrite_goal
                        )
                    st.markdown("**Suggested rewrites**")
                    st.write(rewrites or "No rewrite generated.")

            # --------------------------- Follow-up Q&A ---------------------------
            st.write("---")
            st.subheader("💬 Follow-up Q&A — Ask ATS ChatGPT")
            q = st.text_input("Ask a question about your resume fit, gaps, or how to improve further:")
            if st.button("Ask", use_container_width=True):
                if not q.strip():
                    st.warning("Please type a question.")
                else:
                    with st.spinner("Thinking..."):
                        answer = ask_followup(
                            client=client,
                            model=model,
                            temperature=temperature,
                            resume_text=resume_text,
                            jd_text=jd_text,
                            analysis_json=data,
                            user_question=q
                        )
                    st.write(answer or "No answer generated.")
