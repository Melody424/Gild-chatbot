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
        model="gemini-2.0-flash-lite",
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


from typing import List
import pandas as pd
from autogen import ConversableAgent, UserProxyAgent, LLMConfig
import os

def extract_hard_skills_from_text(keywords: str, description: str) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing")

    llm_config = LLMConfig(
        api_type="google",
        model="gemini-2.0-flash-lite",
        api_key=GEMINI_API_KEY,
    )

    prompt_template = """
你是一位協助學生解析實習職缺的 AI 助理，請根據輸入的職缺資訊，幫助學生萃取出「重要的硬技能（hard skills）」，這些技能應該是學生應該學會或具備的，通常是工具、語言、技術、平台或數據分析能力，例如：Python、Excel、SQL、Tableau、Canva、A/B testing 等。

請依據以下規則處理：
1. 統整 job keywords 與 job description 中出現的技能
2. 僅保留硬技能，排除軟技能（如溝通能力、團隊合作）
3. 以英文逗號分隔，例如：Python, Excel, SQL, Tableau
4. 移除重複項目，並盡可能標準化技能名稱（例如 Excel 表格處理 ➝ Excel）
5. 如果是Microsoft Office系列，Word, PowerPoint, Excel都有的話，請幫我以Microsoft Office表示，如果Word, PowerPoint, Excel沒有同時出現還次可以顯示單一項目
6. 回傳最多四個你覺得最相關的
7. 全部用英文回應
8. 最多兩個英文字，Social Media Platform或Social Media Marketing都保留Social Media就好

以下是職缺資訊：
---
Job Keywords:
{keywords}

Job Description:
{description}
---
請回傳這些職缺所需的硬技能清單（以英文逗號分隔）：
"""

    final_prompt = prompt_template.format(keywords=keywords, description=description)

    gemini_agent = ConversableAgent(
        name="Gemini",
        llm_config=llm_config,
        system_message="你是負責萃取實習硬技能的助手"
    )

    user = UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0
    )

    chat_result = user.initiate_chat(
        recipient=gemini_agent,
        message=final_prompt
    )

    for msg in chat_result.chat_history:
        if msg["role"] == "user":
            return msg["content"]

    return ""

def extract_all_hard_skills_as_text(csv_path: str) -> str:
    df = pd.read_csv(csv_path)
    all_keywords = " ".join(df["Job Keywords"].dropna().astype(str).tolist())
    all_descriptions = " ".join(df["Job Description"].dropna().astype(str).tolist())
    return extract_hard_skills_from_text(all_keywords, all_descriptions)

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

def persona_hardskill(img: Image.Image, hard_skills: str) -> Image.Image:
    draw = ImageDraw.Draw(img)

    # 字型設定（可和名字不同大小）
    font_path = "pages/Montserrat-Bold.ttf"
    font_size = 20
    font = ImageFont.truetype(font_path, font_size)

    skills_list = [skill.strip() for skill in hard_skills.split(",") if skill.strip()]
    bullet = u"\u2022"  # 黑圓點

     # 起始位置（你可以自己微調）
    start_x = 535
    start_y = 260
    line_spacing = 30

#    for i in skills_list:
    for i, skill in enumerate(skills_list):
        y = start_y + i * line_spacing
        draw.text((start_x, y), f"{bullet} {skill}", fill="#2c606d", font=font)

    return img


def extract_soft_skills_from_text(keywords: str, description: str) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing")

    llm_config = LLMConfig(
        api_type="google",
        model="gemini-2.0-flash-lite",
        api_key=GEMINI_API_KEY,
    )

    prompt_template = """
你是一位協助學生解析實習職缺的 AI 助理，請根據輸入的職缺資訊，幫助學生萃取出「重要的軟技能（soft skills）」，這些技能通常是個人特質、工作態度、人際互動與職場通用能力，例如：Communication, Teamwork, Problem Solving, Adaptability, Time Management 等。
請依據以下規則處理：
1. 統整 job keywords 與 job description 中出現的軟技能
2. 僅保留軟技能，排除工具、程式語言、技術平台等硬技能（如：Python、Excel、SQL 不要包含）
3. 以英文逗號分隔，例如：Communication, Teamwork, Problem Solving
4. 移除重複項目，並儘可能標準化技能名稱（例如：Good communication skills ➝ Communication）
5. 如果有多種描述方式，請保留最常見、最代表性的表述方式（例如：Team collaboration、Team player ➝ Teamwork）
6. 保留你覺得最相關的四個
7. 全部用英文回應

以下是職缺資訊：
---
Job Keywords:
{keywords}

Job Description:
{description}
---
請回傳這些職缺所需的軟技能清單（以英文逗號分隔）：
"""

    final_prompt = prompt_template.format(keywords=keywords, description=description)

    gemini_agent = ConversableAgent(
        name="Gemini",
        llm_config=llm_config,
        system_message="你是負責萃取實習硬技能的助手"
    )

    user = UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0
    )

    chat_result = user.initiate_chat(
        recipient=gemini_agent,
        message=final_prompt
    )

    for msg in chat_result.chat_history:
        if msg["role"] == "user":
            return msg["content"]

    return ""

def extract_all_soft_skills_as_text(csv_path: str) -> str:
    df = pd.read_csv(csv_path)
    all_keywords = " ".join(df["Job Keywords"].dropna().astype(str).tolist())
    all_descriptions = " ".join(df["Job Description"].dropna().astype(str).tolist())
    return extract_soft_skills_from_text(all_keywords, all_descriptions)


def persona_softskill(img: Image.Image, soft_skills: str) -> Image.Image:
    draw = ImageDraw.Draw(img)

    # 字型設定（可和名字不同大小）
    font_path = "pages/Montserrat-Bold.ttf"
    font_size = 20
    font = ImageFont.truetype(font_path, font_size)

    skills_list = [skill.strip() for skill in soft_skills.split(",") if skill.strip()]
    bullet = u"\u2022"  # 黑圓點

     # 起始位置（你可以自己微調）
    start_x = 795
    start_y = 315
    line_spacing = 28

#    for i in skills_list:
    for i, skill in enumerate(skills_list):
        y = start_y + i * line_spacing
        draw.text((start_x, y), f"{bullet} {skill}", fill="#d7f8ff", font=font)

    return img


