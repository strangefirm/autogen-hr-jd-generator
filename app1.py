import asyncio
import os

import streamlit as st
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import ModelClientStreamingChunkEvent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()

HR_SYSTEM_MESSAGE = """You are an experienced HR recruiter at a technology company.
You write clear, inclusive and attractive job descriptions (JDs).
Always format the JD in Markdown with these sections:
1. Job Title
2. About the Company
3. Role Overview
4. Key Responsibilities
5. Required Skills & Qualifications
6. Nice-to-Have Skills
7. What We Offer
8. How to Apply
Keep it realistic for the experience level requested and avoid biased language.
Write the Markdown directly. Do not wrap it in a code block."""


def build_hr_agent() -> AssistantAgent:
    model_client = OpenAIChatCompletionClient(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    return AssistantAgent(
        name="hr_agent",
        model_client=model_client,
        system_message=HR_SYSTEM_MESSAGE,
        model_client_stream=True,  # emit tokens as they are generated
    )


def build_task(job_role, company, location, experience, employment_type, skills):
    return (
        f"Prepare a job description for a {job_role}.\n"
        f"Company: {company}\n"
        f"Location: {location}\n"
        f"Experience: {experience}\n"
        f"Employment type: {employment_type}\n"
        f"Key skills: {skills}"
    )


async def stream_jd(task: str, placeholder) -> str:
    agent = build_hr_agent()
    jd = ""
    async for event in agent.run_stream(task=task):
        if isinstance(event, ModelClientStreamingChunkEvent):
            jd += event.content
            placeholder.markdown(jd + "▌")
    placeholder.markdown(jd)
    return jd


# Minimal 3D look: soft shadows, small hover lift and vibrant colors
CSS_3D = """
<style>
.stApp {
    background: linear-gradient(135deg, #fdf2ff 0%, #eef4ff 50%, #e8fff6 100%);
}
.st-key-hero > div, .st-key-jd_card > div {
    background: #ffffff;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.12);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.st-key-hero > div:hover, .st-key-jd_card > div:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 28px rgba(124, 58, 237, 0.18);
}
.st-key-hero h1 {
    background: linear-gradient(90deg, #7c3aed, #ec4899, #f97316);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.st-key-generate button, .st-key-download button {
    background: linear-gradient(90deg, #7c3aed, #ec4899);
    color: #ffffff;
    border: none;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(236, 72, 153, 0.3);
}
.st-key-generate button:hover, .st-key-download button:hover {
    color: #ffffff;
    box-shadow: 0 6px 16px rgba(236, 72, 153, 0.4);
}
</style>
"""

st.set_page_config(page_title="HR Agent - JD Generator", page_icon="📝")
st.html(CSS_3D)

with st.container(key="hero"):
    st.title("📝 HR Agent: Job Description Generator")
    st.caption("Built with AutoGen AgentChat + Streamlit")

with st.sidebar:
    st.header("Job details")
    job_role = st.text_input("Job role", "Junior Python Developer")
    company = st.text_input("Company name", "TechNova Solutions")
    location = st.text_input("Location", "Chennai, India (Hybrid)")
    experience = st.selectbox("Experience", ["0-1 years", "1-3 years", "3-5 years", "5-8 years", "8+ years"])
    employment_type = st.selectbox("Employment type", ["Full-time", "Internship", "Contract"])
    skills = st.text_area(
        "Key skills",
        "Python, OOP, Git, SQL, REST APIs, Flask/Django basics, unit testing",
    )
    generate = st.button("Generate JD", type="primary", use_container_width=True, key="generate")

if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY is not set. Add it to a .env file next to app.py.")
    st.stop()

if generate or "jd" in st.session_state:
    with st.container(key="jd_card"):
        if generate:
            output = st.empty()
            with st.spinner("HR agent is writing the JD..."):
                jd = asyncio.run(
                    stream_jd(build_task(job_role, company, location, experience, employment_type, skills), output)
                )
            st.session_state["jd"] = jd
            st.session_state["job_role"] = job_role
        else:
            st.markdown(st.session_state["jd"])

        st.download_button(
            "Download JD (.md)",
            st.session_state["jd"],
            file_name=f"{st.session_state['job_role'].lower().replace(' ', '_')}_jd.md",
            mime="text/markdown",
            key="download",
        )
