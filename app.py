import streamlit as st
import tempfile
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Load secrets if running on Streamlit Cloud, otherwise use .env
try:
    secrets = st.secrets._secrets
    if secrets:
        for key in ["ANTHROPIC_API_KEY", "TAVILY_API_KEY", "OPENAI_API_KEY"]:
            if key in secrets:
                os.environ[key] = secrets[key]
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/mount/src/gtm-campaign-agent')
from gtm_campaign_agent import read_brief_from_doc, run_campaign_agent

st.set_page_config(page_title="GTM Campaign Agent", page_icon="🚀", layout="wide")

st.title("GTM Campaign Launch Agent")
st.markdown("Upload a campaign brief and the AI will generate a complete GTM campaign package — email copy, audience variations, channel strategy, and market research.")

uploaded_file = st.file_uploader("Upload your campaign brief (.docx)", type=["docx"])

if uploaded_file:
    st.success("Brief uploaded successfully!")

    if st.button("Generate Campaign Package", type="primary"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        with st.spinner("AI agents are working on your campaign..."):
            try:
                brief = read_brief_from_doc(tmp_path)
                result = run_campaign_agent(brief)

                st.success("Campaign package complete!")
                st.divider()

                st.subheader("Email Copy")
                st.markdown("**Subject Line**")
                st.info(result["subject"])
                st.markdown("**Email Body**")
                st.write(result["body"])

                if result.get("versions") and len(result.get("audiences", [])) > 1:
                    st.divider()
                    st.subheader("Audience Variations")
                    st.markdown("*These opening lines replace the first sentence of the email for each audience.*")
                    for audience, version in result["versions"].items():
                        if version:
                            st.markdown(f"**{audience}**")
                            st.write(version)

                st.divider()
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Strategy")
                    st.markdown("**Target Audience**")
                    st.write(result["audience"])
                    st.markdown("**Key Message**")
                    st.write(result["message"])

                with col2:
                    st.subheader("Channel Angles")
                    st.markdown("**Email**")
                    st.write(result["email_angle"])
                    st.markdown("**Paid Social**")
                    st.write(result["social_angle"])
                    st.markdown("**Content**")
                    st.write(result["content_angle"])
                    st.markdown("**SDR Sequence**")
                    st.write(result["sdr_angle"])

                st.divider()
                st.subheader("Market Research")
                col3, col4 = st.columns(2)

                with col3:
                    st.markdown("**Market Conditions**")
                    st.write(result["market"])
                    st.markdown("**Competitive Landscape**")
                    st.write(result["competitive"])

                with col4:
                    st.markdown("**Risk Flags**")
                    st.write(result["risks"])
                    st.markdown("**Buyer Sentiment**")
                    st.write(result["sentiment"])

                st.divider()
                st.subheader("Critic Review")
                score_col, rest_col = st.columns([1, 3])

                with score_col:
                    st.metric("Score", result["score"])

                with rest_col:
                    st.markdown("**Strengths**")
                    st.write(result["strengths"])
                    st.markdown("**Improvements**")
                    st.write(result["improvements"])

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

            finally:
                os.unlink(tmp_path)
