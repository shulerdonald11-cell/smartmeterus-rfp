import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
from fpdf import FPDF
import base64
import json

from flow_engine import FlowEngine

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://api.x.ai/v1"
)

st.set_page_config(page_title="AMI Validate Solutions", page_icon="💧", layout="centered")

# ---------------------------
# Guided Scope Builder Engine
# ---------------------------
if "flow_engine" not in st.session_state:
    st.session_state.flow_engine = FlowEngine(base_path="BUILD_ARTIFACTS/Schemas")

if "flow_session" not in st.session_state:
    st.session_state.flow_session = None

# ---------------------------
# Styling / Headers
# ---------------------------
st.markdown(
    """
<style>
    .main {background-color: #f0f7fa;}
    .header {font-size: 42px; color: #006699; text-align: center; padding: 20px;}
    .subheader {font-size: 24px; color: #0088cc; text-align: center;}
    .info-box {background-color: #e6f5ff; padding: 20px; border-radius: 10px; border-left: 6px solid #006699;}
    .bullet {margin-left: 20px;}
    .small {font-size: 12px; color: #666;}
</style>
""",
    unsafe_allow_html=True
)

st.markdown("<div class='header'>💧 AMI Validate Solutions</div>", unsafe_allow_html=True)
st.markdown("<div class='subheader'>Professional Water AMI RFP Generator</div>", unsafe_allow_html=True)
st.markdown("**20+ Years of Utility Expertise • Free Customized RFP in Minutes**")

guided_mode = st.toggle(
    "🧭 Guided Scope Builder (Beta)",
    value=True,
    help="Uses a structured question flow instead of free-form chat."
)

if guided_mode and st.session_state.flow_session is None:
    st.session_state.flow_session = st.session_state.flow_engine.start_session()

# ---------------------------
# Landing page gate
# ---------------------------
if "started" not in st.session_state:
    st.session_state.started = False

if not st.session_state.started:
    st.markdown(
        """
    <div class='info-box'>
    <h3>Welcome! Let's Build Your AMI RFP</h3>
    <p>I'll guide you step-by-step to create a professional, bid-ready RFP tailored to your utility.</p>
    <p><strong>Best Practice Tip:</strong> For the strongest project outcome, we recommend a pre-deployment field survey (even a small sample) to identify risks like buried pits, traffic hazards, or compatibility issues. This reduces change orders and failed installations by up to 50%. We offer paid validation services starting at $10k if you'd like expert help.</p>
    </div>
    """,
        unsafe_allow_html=True
    )

    st.markdown("### To get the most accurate RFP, have this information ready:")
    st.markdown(
        """
    <ul class='bullet'>
    <li>Utility name and location</li>
    <li>Number of meters and sizes (e.g., 2,000 × 5/8&quot;x3/4&quot;, 100 × 1&quot;)</li>
    <li>Current reading system (manual, drive-by AMR, partial AMI?)</li>
    <li>Project goals: Full AMI? Meter replacement only? Turnkey or install-only?</li>
    <li>Preferred start date and bid due date</li>
    <li>Expected deployment duration (e.g., 3–6 months)</li>
    <li>Known site risks (buried pits, downtown traffic, flood-prone areas?)</li>
    <li>Any large meters (&gt;2&quot;) or special requirements</li>
    <li>Need for training, WOMS integration, or post-install support?</li>
    </ul>
    """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 Download Questionnaire Template (PDF)", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "AMI RFP Preparation Questionnaire", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            questions = [
                "1. Utility Name & Location:",
                "2. Total Meters & Sizes:",
                "3. Current Reading System:",
                "4. Project Type (turnkey / install-only / product-only):",
                "5. Desired Start Date & Bid Due Date:",
                "6. Expected Deployment Duration:",
                "7. Known Site Risks:",
                "8. Need Field Survey? (Recommended)",
                "9. Additional Notes:"
            ]
            for q in questions:
                pdf.multi_cell(0, 10, q)
                pdf.ln(5)

            pdf_output = "AMI_RFP_Questionnaire.pdf"
            pdf.output(pdf_output)
            with open(pdf_output, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="{pdf_output}">Click here if download doesn’t start</a>'
                st.markdown(href, unsafe_allow_html=True)

    with col2:
        if st.button("🚀 Get Started – Begin Now", type="primary", use_container_width=True):
            st.session_state.started = True
            st.rerun()

    st.markdown("---")
    st.caption("Ready when you are. Click 'Get Started' to begin your custom RFP.")

else:
    st.markdown("### 💬 Chat with Your AMI Expert")
    st.info("Chat stays available as a helper. Guided Mode controls question order.")

    # ---------------------------
    # Guided Scope Builder UI
    # ---------------------------
    if guided_mode and st.session_state.flow_session:
        engine = st.session_state.flow_engine
        session = st.session_state.flow_session

        # Ensure active questions are computed (safe even if already set)
        # (Engine recomputes on submit; this is just defensive)
        current_question = engine.get_current_question(session)

        st.subheader("🧭 Guided Scope Questions")

        # Progress
        prog = engine.get_progress(session)
        if prog["total"] > 0:
            st.progress(prog["pct"])
            st.markdown(f"<div class='small'>Question {prog['currentIndex']} of {prog['total']}</div>", unsafe_allow_html=True)

        # If complete
        if not current_question:
            st.success("✅ Scope questions complete.")
        else:
            qid = current_question.get("questionId")
            st.markdown(current_question.get("prompt", ""))

            # Notes (stored per question)
            existing_note = session.get("notes", {}).get(qid, "")
            note_val = st.text_area(
                "Notes (optional)",
                value=existing_note,
                key=f"note_{qid}",
                placeholder="Add any context, constraints, or assumptions…"
            )
            if note_val != existing_note:
                st.session_state.flow_session = engine.set_note(session, qid, note_val)
                session = st.session_state.flow_session

            answer = None
            answer_type = current_question.get("answerType")
            options = current_question.get("options", [])

            # ---- Render inputs by answerType ----
            if answer_type == "single":
                answer = st.radio(
                    "Select one:",
                    options,
                    key=f"guided_{qid}"
                )

            elif answer_type == "multi":
                answer = st.multiselect(
                    "Select all that apply:",
                    options,
                    key=f"guided_{qid}"
                )

            elif answer_type == "matrix_single_per_item":
                items = current_question.get("items", [])
                if not items:
                    st.warning("This question is missing 'items' in the question bundle.")
                    answer = {}
                else:
                    st.caption("Select one option per row.")
                    matrix_answers = {}
                    for idx, item in enumerate(items):
                        matrix_answers[item] = st.radio(
                            item,
                            options,
                            key=f"guided_{qid}_row_{idx}",
                            horizontal=True
                        )
                    answer = matrix_answers

            else:
                # Fallback: free text
                answer = st.text_input(
                    "Answer:",
                    key=f"guided_{qid}"
                )

            # Buttons
            c1, c2, c3 = st.columns([1, 1, 2])

            with c1:
                back_disabled = not engine.can_go_back(session)
                if st.button("⬅️ Back", disabled=back_disabled, use_container_width=True):
                    st.session_state.flow_session = engine.go_back(session)
                    st.rerun()

            with c2:
                if st.button("Next ➡️", use_container_width=True):
                    st.session_state.flow_session = engine.submit_answer(
                        session=session,
                        answer_value=answer,
                        value_type=answer_type if answer_type else "single"
                    )
                    st.rerun()

            with c3:
                if st.button("🔄 Restart", use_container_width=True):
                    st.session_state.flow_session = engine.start_session()
                    st.rerun()

    # Completion / review
    tokens_count = len(st.session_state.flow_session.get("tokens", [])) if st.session_state.flow_session else 0
    escalations_count = len(st.session_state.flow_session.get("escalations", [])) if st.session_state.flow_session else 0
    st.write(f"**Tokens captured:** {tokens_count}")
    st.write(f"**Escalations flagged:** {escalations_count}")

    with st.expander("Review captured answers"):
        if st.session_state.flow_session:
            st.json(st.session_state.flow_session.get("answers", {}))

    with st.expander("Review notes (optional)"):
        if st.session_state.flow_session:
            st.json(st.session_state.flow_session.get("notes", {}))

    st.download_button(
        "⬇️ Download session JSON (internal)",
        data=json.dumps(st.session_state.flow_session, indent=2) if st.session_state.flow_session else "{}",
        file_name="scope_session_output.json",
        mime="application/json"
    )

    # ---------------------------
    # Chat initialization (helper-only when guided_mode is ON)
    # ---------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = []

        if guided_mode:
            system_prompt = (
                "You are a helper assistant. "
                "You may explain questions or terminology, "
                "but you may NOT choose questions or change their order."
            )
        else:
            system_prompt = """
You are an expert water AMI consultant with 20+ years experience helping small to mid-sized utilities create professional RFPs.

Always guide step-by-step to flush out details:
- Ask about meter types and AMI system (e.g., compatibility if they have meters, endpoint types).
- Ask about WOMS (contractor provide their own or use existing? Integration needs?).
- Ask about billing CIS update process and field data collection management for meter exchanges.
- Probe for more details if prompt is basic.

Only generate the full RFP when the user has provided sufficient detail or says "generate the RFP".

Use real-world U.S. water utility RFP language and structure.
"""
        st.session_state.messages.append({"role": "system", "content": system_prompt})

    for msg in st.session_state.messages[1:]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask for clarification, or describe your project..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = ""
            placeholder = st.empty()
            stream = client.chat.completions.create(
                model="grok-4-latest",
                messages=st.session_state.messages,
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    response += chunk.choices[0].delta.content
                    placeholder.markdown(response + "▌")
            placeholder.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.last_response = response

    # PDF Download (kept as-is)
    if "last_response" in st.session_state and "Request for Proposals" in st.session_state.last_response:
        if st.button("📄 Download RFP as PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, st.session_state.last_response)
            pdf_output = "Custom_AMI_RFP.pdf"
            pdf.output(pdf_output)
            with open(pdf_output, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="{pdf_output}">Click to download your RFP</a>'
                st.markdown(href, unsafe_allow_html=True)

st.markdown("---")
st.caption("AMI Validate Solutions • Professional RFP + Optional Field Validation Services")
