# pages/job_cleaner.py
# -*- coding: utf-8 -*-
"""
🧹Job Cleaner - 讀入職缺CSV，從職缺描述擷取出「工作內容」，匯出
"""
import os
import re
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from autogen import AssistantAgent, LLMConfig
from tqdm import tqdm
from coding.utils import paging

def save_lang():
    st.session_state['lang_setting'] = st.session_state.get("language_select")

user_image = "https://www.w3schools.com/howto/img_avatar.png"
# ----------------------------- 基本設定 --------------------------------------
PAGE_TITLE = "🧹Job Cleaner"
st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon="🧹")
st.title(PAGE_TITLE)

with st.sidebar:
        paging()
        selected_lang = st.selectbox("Language", ["English", "繁體中文"], index=1, on_change=save_lang, key="language_select")

        lang_setting = st.session_state.get('lang_setting', selected_lang)
        st.session_state['lang_setting'] = lang_setting

        st_c_1 = st.container(border=True)
        with st_c_1:
            st.image(user_image)
            
load_dotenv(override=True)
API_KEY = os.getenv("GEMINI_API_KEY")

# ----------------------------- 建立 LLM Agent --------------------------------
llm_cfg = LLMConfig(
    api_type="google",
    model="gemini-2.0-pro",
    api_key=API_KEY,
    temperature=0,
    max_tokens=256
)

extractor = AssistantAgent(
    name="extractor",
    llm_config=llm_cfg,
    system_message=(
        "你是一位人力資源資料清理助手。\n"
        "輸入是一段職缺簡介，請：\n"
        "1. 找出『工作內容/見習內容/Responsibilities』段落並保留條列。\n"
        "2. 移除資格條件、期間說明、證明、注意事項等。\n"
        "3. 直接輸出純文字，不要附加其他說明。"
    ),
    max_consecutive_auto_reply=1
)

@st.cache_data(show_spinner=False)
def extract_content(desc: str) -> str:
    """
    呼叫 LLM 抽取工作內容；如果回空字串就用 regex 備援。
    """
    if not isinstance(desc, str) or desc.strip() == "":
        return ""

    # ⬇️ 用 generate_reply 取得回答
    reply_msg = extractor.generate_reply(
        messages=[{"role": "user", "content": desc}],
        sender="user"                    # 說明這是 user 發話
    )
    reply = reply_msg["content"].strip() if reply_msg else ""

    if reply:
        return reply

    # ---------- fallback: regex ------------------------------------------------
    m = re.search(r"([(（]?\s*1[.)）]\s*.*?)(?:\n\s*\n|$)", desc, flags=re.S)
    return m.group(1).strip() if m else ""

# ----------------------------- UI 介面 ---------------------------------------
uploaded = st.file_uploader("⬆️ 上傳含 jobName, description 欄位的 CSV", type="csv")

if uploaded:
    df = pd.read_csv(uploaded)
    if {"jobName", "description"}.issubset(df.columns):
        st.success(f"載入 {len(df)} 筆職缺，開始清理…")
        progress = st.progress(0, text="LLM 抽取中…")
        contents = [""] * len(df)

        # 並行呼叫，提高速度
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(extract_content, desc): idx
                for idx, desc in enumerate(df["description"])
            }
            for n, future in enumerate(as_completed(futures), start=1):
                idx = futures[future]
                try:
                    contents[idx] = future.result()
                except Exception as e:
                    contents[idx] = ""
                    st.warning(f"第 {idx} 筆失敗：{e}")
                progress.progress(n / len(futures))

        df["jobContent"] = contents
        st.success("✅ 抽取完成！")

        # 顯示前 5 筆預覽
        st.subheader("預覽 (前 5 筆)")
        st.dataframe(df[["jobName", "jobContent"]].head(), use_container_width=True)

        # 下載按鈕
        cleaned_csv = df[["jobName", "jobContent"]].to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "💾 下載清理後 CSV",
            cleaned_csv,
            file_name="jobs_cleaned.csv",
            mime="text/csv"
        )
    else:
        st.error("CSV 必須包含 'jobName' 與 'description' 欄位！")
else:
    st.info("請先上傳 CSV 檔")