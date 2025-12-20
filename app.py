import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
from fpdf import FPDF
import base64

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://api.x.ai/v1"
)

# Page config with meter theme
st.set_page_config(page_title="AMI Validate Solutions", page_icon="💧", layout="centered")

# Custom CSS for cooler, meter/utility look
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

# Welcome / Landing Section
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
        # Downloadable Questionnaire PDF
        if st.button("📄 Download Questionnaire Template (PDF)", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "AMI RFP Preparation Questionnaire", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            questions = [
                "1. Utility Name & Location:",
                "2. Total Meters & Sizes (e.g., 5/8x3/4, 1, 2):",
                "3. Current Reading System:",
                "4. Project Type (turnkey / install-only / product-only):",
                "5. Desired Start Date & Bid Due Date:",
                "6. Expected Deployment Duration:",
                "7. Known Site Risks (buried pits, traffic, etc.):",
                "8. Need Field Survey for Risk Assessment? (Recommended)",
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
    # Chatbot Section (only shows after clicking Get Started)
    st.markdown("### 💬 Chat with Your AMI Expert")
    st.info("Paste answers from the questionnaire or just describe your project — I'll ask clarifying questions as needed.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    system_prompt = { "role": "system", "content": """[Your existing strong system prompt here — copy from previous version]""" }

    if not any(m["role"] == "system" for m in st.session_state.messages):
        st.session_state.messages.insert(0, system_prompt)

    for message in st.session_state.messages[1:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Tell me about your utility and AMI project..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            stream = client.chat.completions.create(
                model="grok-4-latest",
                messages=api_messages,
                stream=True
            )
            response = st.write_stream(chunk.choices[0].delta.content or "" for chunk in stream)

        st.session_state.messages.append({"role": "assistant", "content": response})

    # Optional: Add PDF download after RFP generated (from previous suggestion)

st.markdown("---")
st.caption("AMI Validate Solutions • Professional RFP + Optional Field Validation Services")