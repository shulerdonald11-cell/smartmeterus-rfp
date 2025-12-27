# Canonical Manifest — SmartMeterUS Scope Builder (WORK IN PROGRESS)

## Purpose
This file tracks the human-governed canonical scope content (questions + methodology + token intent).
Canonical artifacts may be split across folders and are NOT necessarily wired into the live Streamlit runtime yet.

## Current Canonical Status
- Water Core Sections A–D: LOCKED (12-25-2025 build snapshots)
- Water Core Section E: NOT YET INTERVIEWED / NOT YET LOCKED
- Water Inside Sets: legacy baseline exists; canonical-format migration NOT YET COMPLETE
- Other domains (commercial/large meters, etc.): NOT YET INTERVIEWED

## Canonical Locked Snapshots (12-25-2025 Build)
These folders are treated as LOCKED reference snapshots for Core A–D:

- /12-25-2025 Build/LOCKED_WATER_CORE_A1_B2A_v1.0/
- /12-25-2025 Build/LOCKED_WATER_CORE_B1_B9_v1.0/
- /12-25-2025 Build/LOCKED_WATER_CORE_C1_C9_v1.0/
- /12-25-2025 Build/LOCKED_WATER_CORE_D1_D6_v1.0/

## Canonical Baselines / Reference Inputs (Legacy)
- /BUILD_ARTIFACTS/Schemas/QuestionsBundle-Water-PIT-Inside.json (legacy baseline reference; also currently used by runtime)
- Any DOCX “Scope Artifact” documents under /BUILD_ARTIFACTS or /ARCHIVE are reference unless explicitly promoted to canonical.

## Rules
- Do not rewrite LOCKED canonical snapshots.
- Do not auto-merge legacy bundles into canonical format.
- Canonical truth is human-governed; runtime truth is what Streamlit runs (see RUNTIME_MANIFEST.md).

## Next Canonical Targets
1) Reconciliation: legacy PIT+Inside baseline vs Core A–D coverage audit
2) Interview + author Core Section E (canonical format)
3) Interview + author Inside Sets (canonical format)
