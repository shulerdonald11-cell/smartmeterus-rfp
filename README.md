# SmartMeterUS AMI Scope & RFP Builder

This repository contains the live Streamlit application for Smart Meter Utility Solutions (SMUS), along with canonical scope artifacts used to design and govern the AMI Scope Builder.

---

## 🚀 What Is Live Right Now
- Hosting: Streamlit Cloud
- Entrypoint: `/app.py` (repo root)
- Flow engine: `/flow_engine.py` (repo root)
- Runtime inputs live in:
/BUILD_ARTIFACTS/Schemas/



Authoritative runtime details are documented in:
- `RUNTIME_MANIFEST.md`

⚠️ Files used by the live app should not be casually renamed or moved.

---

## 📚 Canonical Scope Content (Human-Governed)
Canonical scope questions, methodology, and design artifacts are developed separately from runtime execution.

Current canonical status is tracked in:
- `CANONICAL_MANIFEST.md`

Key canonical snapshots (12-25-2025 build):
- Water Core Sections A–D (LOCKED)
- Core Section E (not yet interviewed)
- Inside Sets (canonical-format work in progress)

Canonical artifacts are NOT automatically wired into runtime.

---

## 🧭 How to Navigate This Repo
- `/BUILD_ARTIFACTS/Schemas/`  
→ Runtime JSON files used by the FlowEngine

- `/12-25-2025 Build/`  
→ Canonical snapshots and locked scope artifacts

- `/LOCKED_RUNTIME_BASELINE_v0.1/`  
→ Archived runtime snapshot (not live unless explicitly referenced)

---

## 🔒 Governance Notes
- Runtime truth = what Streamlit runs
- Canonical truth = what humans author, review, and lock
- Do not merge canonical artifacts into runtime without an explicit compile step
- Chat history is not a source of truth; manifests are

---

## 📌 Project Intent
This project is designed to:
- Guide utilities through structured AMI scope discovery
- Produce procurement-ready RFP scope language
- Surface scope gaps, risks, and escalation points
- Position SMUS for paid audits, validation, and consulting
