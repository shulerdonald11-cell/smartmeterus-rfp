import streamlit as st
from xai_sdk import Client
from xai_sdk.chat import user, assistant
from xai_sdk.tools import collections_search
import os
from dotenv import load_dotenv
from fpdf import FPDF
import base64
import json

load_dotenv()

client = Client(api_key=os.getenv("GROK_API_KEY"))
collection_id = os.getenv("GROK_COLLECTION_ID")

# Page config & styling
st.set_page_config(page_title="AMI Validate Solutions", page_icon="💧", layout="centered")

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

    # Initialize chat with RAG tool
    if "chat" not in st.session_state:
        tools = []
        if collection_id:
            tools = [collections_search(collection_ids=[collection_id])]
        chat = client.chat.create(
            model="grok-4-latest",
            tools=tools
        )
        chat.append(assistant("""
You are an expert water AMI consultant with 20+ years experience helping small to mid-sized utilities create professional RFPs.

Use the collections_search tool to retrieve real RFP language from the uploaded samples.

Guide the user step-by-step:
- Start with basics: meter count, sizes, utility name/location, current system.
- Ask about project goals: turnkey, install-only, product-only, AMI features.
- Probe details: retrofits, large meters, pit conditions, risks, WOMS.
- When ready, generate a complete RFP pulling and synthesizing from collection samples.

Use these sections:
- Project Overview / Background
- Scope of Work (include WOMS if turnkey)
- Technical Specifications
- Implementation Plan & Training
- Pricing Schedule & Evaluation Criteria
- Attachments / Appendices

Remain brand-neutral unless specified. Include timelines and evaluation focus on experience if provided.

At the end, offer: "Need on-site field validation or custom consulting? We offer tiers starting at $10k or $250/hr."
"""))
        st.session_state.chat = chat

    chat = st.session_state.chat

    # Display chat history
    for msg in chat.messages[1:]:  # skip system
        role = "human" if msg.role == "user" else "ai"
        with st.chat_message(role):
            st.markdown(msg.content)

    # User input
    if prompt := st.chat_input("Tell me about your utility and AMI project..."):
        chat.append(user(prompt))
        with st.chat_message("human"):
            st.markdown(prompt)

        with st.chat_message("ai"):
            response = ""
            placeholder = st.empty()
            for chunk in chat.stream():
                content = ""
                if hasattr(chunk, 'content'):
                    content = chunk.content or ""
                elif hasattr(chunk, 'delta') and chunk.delta and hasattr(chunk.delta, 'content'):
                    content = chunk.delta.content or ""
                if content:
                    response += content
                    placeholder.markdown(response + "▌")
            placeholder.markdown(response)

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
