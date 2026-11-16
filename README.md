---
title: Zafika — Mkushi Boarding Secondary School Results Portal
emoji: 🎓
colorFrom: green
colorTo: yellow
sdk: docker
pinned: false
---

# Zafika — Mkushi Boarding Secondary School Results Portal

Mobile-first Zambian School Results Portal ("Zafika - Results Zafika") built specifically for **Mkushi Boarding Secondary School**.

## Initial Setup
1. Sign in as System Admin (`MKBSS` / `MKBSS/100`).
2. Create Teacher accounts and assign their grades.
3. Add or bulk-import pupil class lists by grade.
4. Teachers sign in, pick a grade, enter scores/comments, and click **Publish & Send SMS**.

## Local Run (Flask)
```bash
pip install -r requirements.txt
python app.py
```

## Hugging Face Spaces Deployment
Push the contents of `flask_deploy/` to a Docker Space on Hugging Face. Port `7860` is exposed automatically.
