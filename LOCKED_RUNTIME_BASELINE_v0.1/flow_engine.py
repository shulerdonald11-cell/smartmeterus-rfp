"""
flow_engine.py
Deterministic scope flow engine for Water – PIT & Inside Set

AUTHORITATIVE INPUTS (LOCKED JSON FILES):
- QuestionsBundle-Water-PIT-Inside.json
- AnswerTokenRegistry-v2-LOCKED.json
- BranchEngineRules-v1-LOCKED.json

This module:
- Does NOT call any LLM
- Does NOT render UI
- Does NOT generate PDFs
- ONLY controls question order, token emission, and risk/escalation

Designed to be imported by Streamlit (app.py).
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


# -----------------------------
# Utilities
# -----------------------------

def _now() -> str:
    return datetime.utcnow().isoformat()


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _qid_sort_key(qid: str):
    # Supports P01, I14, I14a, etc.
    prefix = "".join([c for c in qid if c.isalpha()])
    num = "".join([c for c in qid if c.isdigit()])
    suffix = "".join([c for c in qid if c.isalpha() and c not in prefix])
    return (prefix, int(num) if num else 0, suffix)


# -----------------------------
# Flow Engine
# -----------------------------

class FlowEngine:
    def __init__(self, base_path: Optional[str] = None):
        """
        base_path: directory containing the locked JSON artifacts
        """
        base = Path(base_path) if base_path else Path(__file__).parent

        self.questions_bundle = _load_json(
            base / "QuestionsBundle-Water-PIT-Inside.json"
        )
        self.token_registry = _load_json(
            base / "AnswerTokenRegistry-v2-LOCKED.json"
        )
        self.branch_rules = _load_json(
            base / "BranchEngineRules-v1-LOCKED.json"
        )

        self.questions_index = {
            q["questionId"]: q
            for q in self.questions_bundle.get("questions", [])
        }

        self.ordered_question_ids = sorted(
            self.questions_index.keys(),
            key=_qid_sort_key
        )

    # -------------------------
    # Session Lifecycle
    # -------------------------

    def start_session(self) -> Dict[str, Any]:
        first_qid = self.ordered_question_ids[0]

        return {
            "startedAt": _now(),
            "currentQuestionId": first_qid,
            "answers": {},
            "tokens": [],
            "riskFlags": [],
            "escalations": [],
            "completed": False
        }

    # -------------------------
    # Core Step
    # -------------------------

    def submit_answer(
        self,
        session: Dict[str, Any],
        answer_value: Any,
        value_type: str = "single"
    ) -> Dict[str, Any]:
        """
        Apply an answer, emit tokens, update risk, and advance flow.
        """

        qid = session["currentQuestionId"]
        question = self.questions_index[qid]

        # Record answer
        session["answers"][qid] = {
            "value": answer_value,
            "valueType": value_type,
            "answeredAt": _now()
        }

        # Emit tokens
        emitted_tokens = self._emit_tokens(qid, answer_value)
        session["tokens"].extend(emitted_tokens)

        # Apply branch / risk rules
        self._apply_rules(session, qid, emitted_tokens, value_type)

        # Advance flow
        next_qid = self._next_question(qid)

        if next_qid:
            session["currentQuestionId"] = next_qid
        else:
            session["completed"] = True
            session["currentQuestionId"] = None

        return session

    # -------------------------
    # Token Logic
    # -------------------------

    def _emit_tokens(self, question_id: str, answer: Any) -> List[Dict[str, Any]]:
        emitted = []

        rules = self.token_registry.get("byQuestionId", {}).get(question_id, [])

        for rule in rules:
            token = rule.get("token")
            expected = rule.get("whenAnswerEquals")

            if expected is None or str(answer).lower() == str(expected).lower():
                emitted.append({
                    "token": token,
                    "questionId": question_id,
                    "emittedAt": _now(),
                    "value": answer
                })

        return emitted

    # -------------------------
    # Branch / Risk Logic
    # -------------------------

    def _apply_rules(
        self,
        session: Dict[str, Any],
        question_id: str,
        tokens: List[Dict[str, Any]],
        value_type: str
    ):
        token_names = {t["token"] for t in tokens}

        # Unknown handling
        if value_type == "unknown":
            session["riskFlags"].append({
                "code": "UNKNOWN_ANSWER",
                "severity": "unknown",
                "questionId": question_id
            })
            session["escalations"].append({
                "type": "field_validation",
                "severity": "unknown",
                "reason": "Unknown answer requires verification"
            })

        # Lead service line escalation (example)
        if question_id == "I14a" and (
            "LEAD_SERVICE_LINE_PRESENT" in token_names
            or "LEAD_SERVICE_LINE_SUSPECTED" in token_names
        ):
            session["riskFlags"].append({
                "code": "LEAD_RISK",
                "severity": "high",
                "questionId": question_id
            })
            session["escalations"].append({
                "type": "utility_review",
                "severity": "high",
                "reason": "Lead service line present or suspected"
            })

    # -------------------------
    # Flow Control
    # -------------------------

    def _next_question(self, current_qid: str) -> Optional[str]:
        try:
            idx = self.ordered_question_ids.index(current_qid)
            return self.ordered_question_ids[idx + 1]
        except (ValueError, IndexError):
            return None

    # -------------------------
    # Read-only Helpers
    # -------------------------

    def get_current_question(self, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        qid = session.get("currentQuestionId")
        if not qid:
            return None
        return self.questions_index.get(qid)
