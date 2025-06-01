from PIL import Image, ImageDraw, ImageFont
import streamlit as st
import autogen
from autogen import ConversableAgent, LLMConfig, Agent
from autogen import AssistantAgent, UserProxyAgent, LLMConfig
from autogen.code_utils import content_str
import os
import google.generativeai as genai
from dotenv import load_dotenv




def persona_name(image_path):
    # Step 1: 使用者輸入名字
    name = st.text_input("Please enter your name", value="")

    if not name:
        return None, None  # 尚未輸入名字就不繼續

    # Step 2: 載入圖片與畫筆
    img = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Step 3: 字型設定
    font_path = "pages/Montserrat-Bold.ttf"
    font_size = 60
    font = ImageFont.truetype(font_path, font_size)

    # Step 4: 計算名字寬度
    bbox = font.getbbox(name)
    name_width = bbox[2] - bbox[0]

    # Step 5: 設定參考點
    reference_x = 410
    y = 90  # 高度固定

    # Step 6: 名字的起始點
    name_x = reference_x - name_width

    # Step 7: 寫上名字
    draw.text((name_x, y), name, font=font, fill="#46a7c1")

    return img, name




import pandas as pd
import re
from openai import OpenAI  # 或 Google Gemini 用你已有的 Client




from autogen import ConversableAgent, UserProxyAgent, LLMConfig
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv(override=True)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', None)

def get_clean_titles(job_titles: list[str]) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing")

    llm_config = LLMConfig(
        api_type="google",
        model="gemini-1.5-flash",
        api_key=GEMINI_API_KEY,
    )

    prompt_template = """
你是一位專門協助學生分析實習職缺的語言模型，請你根據輸入的職缺名稱，幫助學生萃取出「純粹的職位類型」，排除公司名稱、年份、地點、實習計畫等無關資訊，並回傳乾淨、統一格式的職位名稱（英文為主）。

請依據以下規則處理：
1. 移除公司名稱（例如：Google、台積電、KKBOX）
2. 移除時間資訊（例如：2025、暑期、Summer、秋季）
3. 移除描述性文字（例如：「實習計畫」、「預聘機會」、「專案實習」等）
4. 標準化職位名稱格式（例如：將 "Data Analyst Intern"、"Data Analysis Assistant" 都視為 "Data Analyst"）
5. 輸出為英文、每個職位類型以英文逗號分隔，如：Data Analyst, Product Manager
6. 如果顯示的職缺是單純以...Intern表達的話，請保留Intern這個字，例如：Marketing Intern，請不要把Intern拿掉，並回傳完整的Marketing Intern
7. 如果遇到一樣的請幫我同類合併，取你覺得最具代表性的，例如現在有四個：Digital Marketing, Marketing Intern, Social Media Marketing, Marketing Intern，請幫我保留Digital Marketing, Marketing Intern
8. 請儘量用兩個字表達完整，如果一定要三個字的請省略

請處理以下職缺：
{job_titles}
"""

    final_prompt = prompt_template.format(job_titles="\n".join(job_titles))

    gemini_agent = ConversableAgent(
        name="Gemini",
        llm_config=llm_config,
        system_message="你是負責萃取實習職位名稱的助理"
    )

    user = UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0  # 限制只來回一次
    )

    # 正確取得 ChatResult 再取 .chat_history
    chat_result = user.initiate_chat(
        recipient=gemini_agent,
        message=final_prompt
    )

    # 拿到 Gemini 的第一輪 assistant 回答
    for msg in chat_result.chat_history:
        if msg["role"] == "user":
            return msg["content"]

    return ""  # 若沒拿到回覆就回傳空字串

def format_titles_centered(raw_text: str, width: int = 30) -> str:
    titles = [t.strip() for t in raw_text.split(",") if t.strip()]
    centered = [title.center(width) for title in titles]
    return "\n".join(centered)


def persona_title(img, raw_titles_text, width=30):

    draw = ImageDraw.Draw(img)

    # 字型設定（可和名字不同大小）
    font_path = "pages/Montserrat-Bold.ttf"
    font_size = 23
    font = ImageFont.truetype(font_path, font_size)

    # 處理文字：中間對齊 + 拆行
    titles = [t.strip() for t in raw_titles_text.split(",") if t.strip()]
    centered_titles = [t.center(width) for t in titles]

    # 起始位置（你可以自己微調）
    start_x = 130
    start_y = 450
    line_spacing = 35

    # 每行畫上去
    for i, line in enumerate(centered_titles):
        y = start_y + i * line_spacing
        draw.text((start_x, y), line, font=font, fill="#2c606d")

    return img



# 範例用法
if __name__ == "__main__":
    df = pd.read_csv("pages/saved_jobs.csv")
    job_titles = df["Job Title"].dropna().tolist()
    cleaned_raw = get_clean_titles(job_titles)
    print(format_titles_centered(cleaned_raw))


