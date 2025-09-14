# ATS ChatGPT — Resume vs JD Analyzer

A Streamlit app that compares a resume to a job description, computes an ATS-like score, flags gaps, and generates tailored rewrites (summary & bullets). Built to be more actionable than typical “ATS checkers”.

## Features
- Upload **PDF/DOCX/TXT** resume
- Paste or upload **JD**
- Structured **JSON** analysis (robust UI)
- Scores by section + overall ATS score
- Missing vs matched keywords + density table
- Hard requirements pass/fail + red flags
- Concrete recommendations with example rewrites
- Tailored professional summary & bullet suggestions
- Follow-up **Q&A** (“ATS ChatGPT” mode)
- One-click **report downloads** (Markdown/JSON)
- Optional on-demand rewrite generator

## Install (macOS / PyCharm / Terminal)

```bash
git clone <your-repo> ats-chatgpt
cd ats-chatgpt
python3 -m venv .venv
source .venv/bin/activate   # on macOS
pip install -r requirements.txt

cp .env.example .env
# put your OPENAI_API_KEY in .env
