import streamlit as st
from coding.utils import paging

import time
import json
from dotenv import load_dotenv
import os
import pandas as pd

# Import ConversableAgent class
import autogen
from autogen import ConversableAgent, LLMConfig, Agent
from autogen import AssistantAgent, UserProxyAgent, LLMConfig, register_function
from autogen.code_utils import content_str
from coding.constant import JOB_DEFINITION, RESPONSE_FORMAT
from coding.utils import show_chat_history, display_session_msg, save_messages_to_json, paging
from coding.agenttools import AG_search_expert, AG_search_news, AG_search_textbook, get_time

# Load environment variables from .env file
load_dotenv(override=True)

# https://ai.google.dev/gemini-api/docs/pricing
# URL configurations
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', None)
OPEN_API_KEY = os.getenv('GEMINI_API_KEY', None)

placeholderstr = "Please input your command"
user_name = "王妍榛"
user_image = "https://www.w3schools.com/howto/img_avatar.png"

seed = 42

# Load CSV
job_df = pd.read_csv("pages/jobsthousands.csv")
job_df.fillna("", inplace=True)

def search_jobs_by_interest(query: str):
    results = job_df[job_df['job_title'].str.contains(query, case=False)]
    if results.empty:
        return "找不到相關職缺。"
    return "\n".join(
        f"{row['company']}｜{row['job_title']}｜{row['job_tags']}"
        for _, row in results.head(5).iterrows()
    )

def search_jobs_by_skill(skills: str):
    matched_rows = job_df[job_df['job_tags'].str.contains(skills, case=False)]
    if matched_rows.empty:
        return "根據你輸入的技能，暫時找不到符合的職缺。"
    return "\n".join(
        f"{row['company']}｜{row['job_title']}｜{row['job_tags']}"
        for _, row in matched_rows.head(5).iterrows()
    )

llm_config_gemini = LLMConfig(
    api_type = "google", 
    model="gemini-2.0-flash", # The specific model
    api_key=GEMINI_API_KEY,   # Authentication
)

llm_config_openai = LLMConfig(
    api_type = "openai", 
    model="gpt-3.5-turbo",    # The specific model
    api_key=OPEN_API_KEY,   # Authentication
)

def stream_data(stream_str):
    for word in stream_str.split(" "):
        yield word + " "
        time.sleep(0.05)

def save_lang():
    st.session_state['lang_setting'] = st.session_state.get("language_select")

def main():
    st.set_page_config(
        page_title='K-Assistant - The Residemy Agent',
        layout='wide',
        initial_sidebar_state='auto',
        menu_items={
            'Get Help': 'https://streamlit.io/',
            'Report a bug': 'https://github.com',
            'About': 'About your application: **0.20.3.9**'
            },
        page_icon="img/favicon.ico"
    )   

    # Show title and description.
    st.title(f"💬 {user_name}'s Chatbot")

    with st.sidebar:
        paging()
        selected_lang = st.selectbox("Language", ["English", "繁體中文"], index=0, on_change=save_lang, key="language_select")
        
        if 'lang_setting' in st.session_state:
            lang_setting = st.session_state['lang_setting']
        else:
            lang_setting = selected_lang
            st.session_state['lang_setting'] = lang_setting

        st_c_1 = st.container(border=True)
        with st_c_1:
            st.image("https://www.w3schools.com/howto/img_avatar.png")

    st_c_chat = st.container(border=True)

    input_type = st.radio(
        "你想輸入的是？",
        ("感興趣的職缺", "你的技能"),
        horizontal=True,
        key="input_type"
    )

    display_session_msg(st_c_chat, user_image)

    job_agent_persona = f"""你是一位實習職缺推薦老師。當學生提供感興趣的職缺時，你需要從提供的職缺清單中找出相關職缺，
    並簡要地推薦給學生。請簡潔地介紹職位名稱和可能需要的技能。如果找不到相關職缺，請告知學生。請使用 {lang_setting} 回答。
    在完成職缺推薦後，請說 'JOB_RECOMMENDATION_DONE'。"""

    skill_agent_persona = f"""你是一位技能分析專家。當學生提供他們的技能時，你需要分析這些技能，並根據提供的職缺清單，
    建議可能適合他們的實習職位，或者建議他們可以加強哪些技能以符合某些職位要求。
    請使用 {lang_setting} 回答。在完成技能分析後，請說 'SKILL_ANALYSIS_DONE'。"""

    with llm_config_gemini:
        job_advisor_agent = ConversableAgent(
            name="Student_Agent",
            system_message=job_agent_persona,
        )

        skill_analyzer_agent = ConversableAgent(
            name="Skill_Analyzer_Agent",
            system_message=skill_agent_persona,
        )

    user_proxy = UserProxyAgent(
        "user_proxy",
        human_input_mode="NEVER",
        code_execution_config=False,
        is_termination_msg=lambda x: content_str(x.get("content")).find("##ALL DONE##") >= 0,
    )

    def register_agent_methods(agent, proxy, methods):
        for name, description, func in methods:
            agent.register_for_llm(name=name, description=description)(func)
            proxy.register_for_execution(name=name)(func)

    methods_to_register = [
        ("search_jobs_by_interest", "根據學生提供的職缺關鍵字，找出相關實習機會", search_jobs_by_interest),
        ("search_jobs_by_skill", "根據學生提供的技能，推薦相關實習機會", search_jobs_by_skill),
    ]

    register_agent_methods(job_advisor_agent, user_proxy, methods_to_register)
    register_agent_methods(skill_analyzer_agent, user_proxy, methods_to_register)

    def generate_response(prompt, selected_input_type):
        if selected_input_type == "感興趣的職缺":
            chat_result = user_proxy.initiate_chat(
                job_advisor_agent,
                message = prompt,
                max_turns=2,
            )
        elif selected_input_type == "你的技能":
            chat_result = user_proxy.initiate_chat(
                skill_analyzer_agent,
                message = prompt,
                max_turns=2,
            )

        response = chat_result.chat_history
        return response

    def chat(prompt: str):
        response = generate_response(prompt, st.session_state.get("input_type"))
        conv_res = show_chat_history(st_c_chat, response, user_image)

    if prompt := st.chat_input(placeholder=placeholderstr, key="chat_bot"):
        chat(prompt)

if __name__ == "__main__":
    main()
