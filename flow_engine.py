"""
flow_engine.py
Deterministic scope flow engine for Water – PIT & Inside Set

AUTHORITATIVE INPUTS (JSON FILES):
- QuestionsBundle-Water-PIT-Inside.json
- AnswerTokenRegistry-v2-LOCKED.json
- BranchEngineRules-v1-LOCKED.json (loaded, but MVP uses internal gating/suppression)

This module:
- Does NOT call any LLM
- Does NOT render UI
- Does NOT generate PDFs
- Controls question order, token emission, suppression, and basic risk/escalation hooks

Designed to be imported by Streamlit (app.py).
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


# -----------------------------
# Utilities
# -----------------------------

def _now() -> str:
    return datetime.utcnow().isoformat()


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _as_int(val: Any, default: int = 10_000_000) -> int:
    try:
        return int(val)
    except Exception:
        return default


# -----------------------------
# Flow Engine
# -----------------------------

class FlowEngine:
    """
    MVP behavior:
    - Uses question.order (100, 110, 120...) for deterministic sequencing (insert-friendly)
    - Uses a scope selector question (questionId = 'SCOPE01') if present:
        answers: 'pit' | 'inside_set' | 'both'
      If absent, defaults to 'both'
    - Uses Inside gating question (questionId = 'I1') if present:
        If I1 answer is exactly "No" (case-insensitive match), suppress I2+ inside_set questions
    - Supports Back via history stack
    - Exposes progress (active list index / total)
    """

    def __init__(self, base_path: Optional[str] = None):
        base = Path(base_path) if base_path else Path(__file__).parent

        self.questions_bundle = _load_json(base / "QuestionsBundle-Water-PIT-Inside.json")
        self.token_registry = _load_json(base / "AnswerTokenRegistry-v2-LOCKED.json")
        self.branch_rules = _load_json(base / "BranchEngineRules-v1-LOCKED.json")

        questions = self.questions_bundle.get("questions", [])
        self.questions_index: Dict[str, Dict[str, Any]] = {q["questionId"]: q for q in questions}

        # Precompute an "all questions in order" list (independent of scope suppression)
        self.all_ordered_question_ids: List[str] = self._compute_ordered_ids(questions)

    # -------------------------
    # Ordering
    # -------------------------

    def _compute_ordered_ids(self, questions: List[Dict[str, Any]]) -> List[str]:
        """
        Primary: order field (int)
        Secondary: set grouping (stable)
        Tertiary: questionId (stable)
        """
        sortable: List[Tuple[int, str, str]] = []
        for q in questions:
            qid = q.get("questionId")
            order = _as_int(q.get("order"), default=10_000_000)
            qset = str(q.get("set", ""))
            sortable.append((order, qset, qid))
        sortable.sort(key=lambda t: (t[0], t[1], t[2]))
        return [qid for (_, _, qid) in sortable]

    # -------------------------
    # Session Lifecycle
    # -------------------------

    def start_session(self) -> Dict[str, Any]:
        """
        Initializes a session and sets the first current question
        from the active question list.
        """
        session = {
            "startedAt": _now(),
            "currentQuestionId": None,
            "answers": {},             # qid -> {value, valueType, answeredAt, answerType?}
            "tokens": [],              # emitted token events
            "riskFlags": [],
            "escalations": [],
            "completed": False,

            # NEW:
            "history": [],             # stack of visited qids (for Back)
            "activeQuestionIds": [],   # derived list based on scope & suppression
            "notes": {}                # optional per-question notes (qid -> str)
        }

        self._refresh_active_questions(session)
        first_qid = session["activeQuestionIds"][0] if session["activeQuestionIds"] else None
        session["currentQuestionId"] = first_qid
        return session

    # -------------------------
    # Public API
    # -------------------------

    def get_current_question(self, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        qid = session.get("currentQuestionId")
        if not qid:
            return None
        return self.questions_index.get(qid)

    def get_progress(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns progress info based on active question list.
        """
        active = session.get("activeQuestionIds", [])
        current = session.get("currentQuestionId")

        total = len(active)
        if total == 0:
            return {"currentIndex": 0, "total": 0, "pct": 1.0}

        try:
            idx = active.index(current) + 1 if current else total
        except ValueError:
            idx = 0

        pct = min(max(idx / total, 0.0), 1.0)
        return {"currentIndex": idx, "total": total, "pct": pct}

    def can_go_back(self, session: Dict[str, Any]) -> bool:
        return len(session.get("history", [])) > 0

    def go_back(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Moves to the previous question in history.
        Does NOT delete answers by default.
        """
        if not self.can_go_back(session):
            return session

        prev_qid = session["history"].pop()
        session["currentQuestionId"] = prev_qid
        session["completed"] = False
        return session

    def set_note(self, session: Dict[str, Any], question_id: str, note: str) -> Dict[str, Any]:
        """
        Stores optional per-question note in session.
        """
        if "notes" not in session:
            session["notes"] = {}
        session["notes"][question_id] = note
        return session

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
        Apply an answer, emit tokens, update risk, refresh suppression, and advance flow.
        """

        qid = session.get("currentQuestionId")
        if not qid:
            session["completed"] = True
            return session

        question = self.questions_index.get(qid, {})
        answer_type = question.get("answerType")

        # Record history for Back (only if not already last)
        if session.get("history") is None:
            session["history"] = []
        if session["history"] and session["history"][-1] == qid:
            # avoid duplicates
            pass
        else:
            session["history"].append(qid)

        # Record answer
        session["answers"][qid] = {
            "value": answer_value,
            "valueType": value_type,
            "answerType": answer_type,
            "answeredAt": _now()
        }

        # Emit tokens (registry-driven)
        emitted_tokens = self._emit_tokens(qid, answer_value)
        session["tokens"].extend(emitted_tokens)

        # Apply minimal risk rules (existing hooks)
        self._apply_rules(session, qid, emitted_tokens, value_type)

        # Recompute active questions because scope/suppression may have changed
        self._refresh_active_questions(session)

        # Advance to next unanswered in active list
        next_qid = self._next_unanswered_after(session, qid)

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
        emitted: List[Dict[str, Any]] = []

        rules = self.token_registry.get("byQuestionId", {}).get(question_id, [])

        # Support list answers for multi-select by emitting per selected value if registry expects strings
        if isinstance(answer, list):
            answers = answer
        else:
            answers = [answer]

        for rule in rules:
            token = rule.get("token")
            expected = rule.get("whenAnswerEquals")

            for a in answers:
                if expected is None:
                    emitted.append({
                        "token": token,
                        "questionId": question_id,
                        "emittedAt": _now(),
                        "value": a
                    })
                else:
                    if str(a).strip().lower() == str(expected).strip().lower():
                        emitted.append({
                            "token": token,
                            "questionId": question_id,
                            "emittedAt": _now(),
                            "value": a
                        })

        return emitted

    # -------------------------
    # Minimal Risk / Escalation Hooks
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
    # Suppression / Active List
    # -------------------------

    def _refresh_active_questions(self, session: Dict[str, Any]) -> None:
        """
        Builds the active question list based on:
        - scope selector (SCOPE01) if present
        - inside gating (I1 == "No") suppresses remaining inside questions
        """
        active: List[str] = []

        # Determine scope selection (default both)
        scope = self._get_scope_selection(session)

        # Determine inside inclusion gate based on I1 answer
        inside_allowed = True
        i1_ans = self._get_answer_value(session, "I1")
        if i1_ans is not None and str(i1_ans).strip().lower() == "no":
            inside_allowed = False

        for qid in self.all_ordered_question_ids:
            q = self.questions_index.get(qid, {})
            qset = q.get("set")

            # Scope filter
            if scope == "pit" and qset == "inside_set":
                continue
            if scope == "inside_set" and qset == "pit":
                continue

            # Inside suppression after I1 == No:
            # Keep I1 itself (so the user can flip it), suppress I2+.
            if qset == "inside_set" and not inside_allowed and qid != "I1":
                continue

            active.append(qid)

        session["activeQuestionIds"] = active

        # If current question is no longer active, move to next active unanswered (or first active)
        cur = session.get("currentQuestionId")
        if cur and cur not in active:
            session["currentQuestionId"] = self._first_unanswered(session) or (active[0] if active else None)

    def _get_scope_selection(self, session: Dict[str, Any]) -> str:
        """
        Returns one of: 'pit', 'inside_set', 'both'
        If SCOPE01 does not exist or unanswered, defaults to 'both'.
        """
        if "SCOPE01" not in self.questions_index:
            return "both"

        val = self._get_answer_value(session, "SCOPE01")
        if val is None:
            return "both"

        s = str(val).strip().lower()
        if "pit" in s and "both" not in s:
            return "pit"
        if "inside" in s and "both" not in s:
            return "inside_set"
        if "both" in s:
            return "both"

        # If user stores exact tokens like pit/inside_set/both:
        if s in ("pit", "inside_set", "both"):
            return s

        return "both"

    def _get_answer_value(self, session: Dict[str, Any], qid: str) -> Any:
        ans = session.get("answers", {}).get(qid)
        if not ans:
            return None
        return ans.get("value")

    def _first_unanswered(self, session: Dict[str, Any]) -> Optional[str]:
        for qid in session.get("activeQuestionIds", []):
            if qid not in session.get("answers", {}):
                return qid
        return None

    def _next_unanswered_after(self, session: Dict[str, Any], current_qid: str) -> Optional[str]:
        active = session.get("activeQuestionIds", [])
        answers = session.get("answers", {})

        try:
            idx = active.index(current_qid)
        except ValueError:
            return self._first_unanswered(session)

        for next_qid in active[idx + 1:]:
            if next_qid not in answers:
                return next_qid

        return None
