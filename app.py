import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
from fpdf import FPDF
import base64

from flow_engine import FlowEngine


load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://api.x.ai/v1"
)

# Page config & styling
st.set_page_config(page_title="AMI Validate Solutions", page_icon="💧", layout="centered")
# ---------------------------
# Guided Scope Builder Engine
# ---------------------------
if "flow_engine" not in st.session_state:
    st.session_state.flow_engine = FlowEngine(
        base_path="BUILD_ARTIFACTS/Schemas"
    )

if "flow_session" not in st.session_state:
    st.session_state.flow_session = None


st.markdown("""
<style>
    .main {background-color: #f0f7fa;}
    .header {font-size: 42px; color: #006699; text-align: center; padding: 20px;}
    .subheader {font-size: 24px; color: #0088cc; text-align: center;}
    .info-box {background-color: #e6f5ff; padding: 20px; border-radius: 10px; border-left: 6px solid #006699;}
    .bullet {margin-left: 20px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='header'>💧 AMI Validate Solutions</div>", unsafe_allow_html=True)
st.markdown("<div class='subheader'>Professional Water AMI RFP Generator</div>", unsafe_allow_html=True)
st.markdown("**20+ Years of Utility Expertise • Free Customized RFP in Minutes**")
guided_mode = st.toggle(
    "🧭 Guided Scope Builder (Beta)",
    value=True,
    help="Uses a structured question flow instead of free-form chat."
)
if guided_mode and st.session_state.flow_session is None:
    st.session_state.flow_session = (
        st.session_state.flow_engine.start_session()
    )


# Landing page state
if "started" not in st.session_state:
    st.session_state.started = False

if not st.session_state.started:
    st.markdown("""
    <div class='info-box'>
    <h3>Welcome! Let's Build Your AMI RFP</h3>
    <p>I'll guide you step-by-step to create a professional, bid-ready RFP tailored to your utility.</p>
    <p><strong>Best Practice Tip:</strong> For the strongest project outcome, we recommend a pre-deployment field survey (even a small sample) to identify risks like buried pits, traffic hazards, or compatibility issues. This reduces change orders and failed installations by up to 50%. We offer paid validation services starting at $10k if you'd like expert help.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### To get the most accurate RFP, have this information ready:")
    st.markdown("""
    <ul class='bullet'>
    <li>Utility name and location</li>
    <li>Number of meters and sizes (e.g., 2,000 × 5/8"x3/4", 100 × 1")</li>
    <li>Current reading system (manual, drive-by AMR, partial AMI?)</li>
    <li>Project goals: Full AMI? Meter replacement only? Turnkey or install-only?</li>
    <li>Preferred start date and bid due date</li>
    <li>Expected deployment duration (e.g., 3–6 months)</li>
    <li>Known site risks (buried pits, downtown traffic, flood-prone areas?)</li>
    <li>Any large meters (>2") or special requirements</li>
    <li>Need for training, WOMS integration, or post-install support?</li>
    </ul>
    """, unsafe_allow_html=True)

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
        if st.button("🚀 Get Started – Begin Chat Now", type="primary", use_container_width=True):
            st.session_state.started = True
            st.rerun()

    st.markdown("---")
    st.caption("Ready when you are. Click 'Get Started' to begin your custom RFP.")

else:
    st.markdown("### 💬 Chat with Your AMI Expert")
    st.info("Paste answers from the questionnaire or just describe your project — I'll ask clarifying questions as needed.")
    # ---------------------------
    # Guided Scope Builder UI
    # ---------------------------
    if guided_mode and st.session_state.flow_session:

        engine = st.session_state.flow_engine
        session = st.session_state.flow_session

        current_question = engine.get_current_question(session)

        if current_question:
            st.subheader("🧭 Guided Scope Questions")
            st.markdown(current_question["prompt"])

            answer = None

            if current_question["answerType"] == "single":
                answer = st.radio(
                    "Select one:",
                    current_question.get("options", []),
                    key=f"guided_{current_question['questionId']}"
                )

            if st.button("Next"):
                st.session_state.flow_session = engine.submit_answer(
                    session=session,
                    answer_value=answer,
                    value_type="single"
                )
                st.rerun()

        else:
            st.success("✅ Scope questions complete.")
            st.json(st.session_state.flow_session)

    
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
- Ask about WOMS (contractor provide their own or use existing? Integration needs?)
- Ask about billing CIS update process and field data collection management for meter exchanges.
- Probe for more details if prompt is basic.

Only generate the full RFP when the user has provided sufficient detail or says "generate the RFP".

Use real-world U.S. water utility RFP language and structure.
"""

        st.session_state.messages.append({
            "role": "system",
            "content": system_prompt
        })


st.session_state.messages.append({
    "role": "system",
    "content": system_prompt
})



    # Display chat history
    for msg in st.session_state.messages[1:]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

    # User input
    if prompt := st.chat_input("Tell me about your utility and AMI project..."):
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
                if chunk.choices[0].delta.content:
                    response += chunk.choices[0].delta.content
                    placeholder.markdown(response + "▌")
            placeholder.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.last_response = response

    # PDF Download
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




