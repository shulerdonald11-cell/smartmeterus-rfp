# Runtime Manifest — SmartMeterUS RFP Builder (LIVE)

## What is live right now
- Hosting: Streamlit Cloud
- Repo: shulerdonald11-cell/smartmeterus-rfp
- Branch: main
- Entrypoint: /app.py (repo root)
- Engine module: /flow_engine.py (repo root)

## Runtime inputs (files the engine loads)
- Base path: /BUILD_ARTIFACTS/Schemas
- Questions bundle: QuestionsBundle-Water-PIT-Inside.json
- Token registry: AnswerTokenRegistry-v2-LOCKED.json
- Branch rules: BranchEngineRules-v1-LOCKED.json

## Notes
- LOCKED_RUNTIME_BASELINE_v0.1 is a snapshot/archive unless Streamlit is pointed to it.
- 12-25-2025 Build (LOCKED_WATER_CORE_*) is canonical work-in-progress and is NOT wired into runtime yet.
