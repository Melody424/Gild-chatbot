import streamlit as st
from openai import OpenAI
from coding.utils import paging
import time
import re
from dotenv import load_dotenv
import os
import unicodedata
import pandas as pd

# AUTOGEN IMPORTS
import autogen
from autogen import ConversableAgent, LLMConfig, Agent
from autogen import AssistantAgent, UserProxyAgent, LLMConfig
from autogen.code_utils import content_str
from coding.constant import JOB_DEFINITION, RESPONSE_FORMAT

# Load environment variables from .env file
load_dotenv(override=True)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', None)
OPEN_API_KEY = os.getenv('OPEN_API_KEY', None)

# Clean UTF-8 unsafe characters
def clean_text(text):
    if text is None:
        return ""
    try:
        return unicodedata.normalize("NFKD", text).encode("utf-8", "ignore").decode("utf-8", "ignore")
    except:
        return str(text).encode("utf-8", "ignore").decode("utf-8", "ignore")

# UI 設定
placeholderstr = "請輸入你會的技能（例如 Python）"
user_name = "王妍榛"
user_image = "https://www.w3schools.com/howto/img_avatar.png"

# 設定 LLM config
llm_config_gemini = LLMConfig(
    api_type = "google", 
    model="gemini-2.0-flash-lite",
    api_key=GEMINI_API_KEY,
)

llm_config_openai = LLMConfig(
    api_type = "openai", 
    model="gpt-4o-mini",
    api_key=OPEN_API_KEY,
)

# Agent 初始化
with llm_config_gemini:
    student_agent = ConversableAgent(
        name="Student_Agent",
        system_message="你是一位學生，想找適合你的實習職缺，請提供技能來獲得建議。",
    )
    teacher_agent = ConversableAgent(
        name="Teacher_Agent",
        system_message=(
            "你是一位實習職缺推薦老師。當學生提供技能（例如 Python），你需要從提供的職缺清單中找出相關職缺，並推薦給學生。"
        )
    )

# 讀入資料
df = pd.read_csv('pages/jobsthousands.csv')

def get_jobs_by_skill(skill):
    matched = df[df["job_tags"].str.contains(skill, case=False, na=False)]
    if matched.empty:
        return "目前沒有符合該技能的職缺，請嘗試其他技能。"
    return "\n".join([f"{row['comp']} - {row['job_title']}，技能需求：{row['job_tags']}" for _, row in matched.iterrows()])

def generate_response(prompt):
    job_info = get_jobs_by_skill(prompt)
    message = f"以下是和 {prompt} 有關的實習職缺：\n{job_info}"
    chat_result = student_agent.initiate_chat(
        teacher_agent,
        message = message,
        summary_method="reflection_with_llm",
        max_turns=2,
    )
    return chat_result.chat_history

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
            'About': 'About your application: **Hello world**'
        },
        page_icon="img/favicon.ico"
    )

    st.title(f"💬 {user_name}'s Chatbot")

    with st.sidebar:
        paging()
        selected_lang = st.selectbox("Language", ["English", "繁體中文"], index=1, on_change=save_lang, key="language_select")

        lang_setting = st.session_state.get('lang_setting', selected_lang)
        st.session_state['lang_setting'] = lang_setting

        st_c_1 = st.container(border=True)
        with st_c_1:
            st.image(user_image)

    st_c_chat = st.container(border=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    else:
        for msg in st.session_state.messages:
            role = msg["role"]
            content = clean_text(msg["content"])
            if role == "user":
                st_c_chat.chat_message(role, avatar=user_image).markdown(content)
            elif role == "assistant":
                st_c_chat.chat_message(role).markdown(content)
            else:
                image_tmp = msg.get("image")
                if image_tmp:
                    st_c_chat.chat_message(role, avatar=image_tmp).markdown(content)
                else:
                    st_c_chat.chat_message(role).markdown(content)

    def show_chat_history(chat_history):
        for entry in chat_history:
            role = entry.get('role')
            content = clean_text(entry.get('content'))
            st.session_state.messages.append({"role": role, "content": content})
            if len(content.strip()) != 0: 
                if 'ALL DONE' in content:
                    return 
                if role != 'assistant':
                    st_c_chat.chat_message(role).write(content)
                else:
                    st_c_chat.chat_message("user", avatar=user_image).write(content)

    def chat(prompt: str):
        response = generate_response(prompt)
        show_chat_history(response)

    if prompt := st.chat_input(placeholder=placeholderstr, key="chat_bot"):
        chat(prompt)

if __name__ == "__main__":
    main()


