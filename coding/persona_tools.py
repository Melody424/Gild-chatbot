from PIL import Image, ImageDraw, ImageFont
import streamlit as st
import autogen
from autogen import ConversableAgent, LLMConfig, Agent
from autogen import AssistantAgent, UserProxyAgent, LLMConfig
from autogen.code_utils import content_str
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import os




def persona_name(image_path):
    # Step 1: 使用者輸入名字
    name = st.text_input("Please enter your name in English", value="")

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
9. 第二點非常重要，千萬不要有任何敘述性的文字，只要用英文逗號隔開就好

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
6. 保留你覺得最相關的四個，且不是非常常見的例如Communication之類的，但如果Communication很重要的話還是可以
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


# Resource的部分

def get_ai_resources(role: str, skills: str) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing")

    llm_config = LLMConfig(
        api_type="google",
        model="gemini-2.0-flash-lite",
        api_key=GEMINI_API_KEY,
    )

    prompt_template = """
你是一位職涯輔導專家。根據學生輸入的想從事的職位和已具備或想加強的技能，請推薦1～2 個高度相關的學習資源（包含文章、影片、教學、指南等），幫助學生培養進入該職位所需的能力。
請依照以下規則回覆：
1. 每則推薦需包含：
    資源名稱title（標題）
    資源類型type（文章／YouTube／課程／書籍）
    資源連結url（一定要是真的連結)格式：http://.....不要有其他括號或重複兩次
    Do not respond Role
2. 資源必須與職位和技能高度相關，避免過於通用。
3. 全文請以英文回覆。
4. 不需要有資源詳細的解說，以及其他敘述的語句，直接給資源的三個項目就好
5. 開頭用• 開始

角色（Role）: {role}
技能（Skills）: {skills}

請開始推薦：
"""

    prompt = prompt_template.format(role=role, skills=skills)

    gemini_agent = ConversableAgent(
        name="GeminiResourceRecommender",
        llm_config=llm_config,
        system_message="你是職涯學習資源推薦專家。"
    )

    user = UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1
    )

    chat_result = user.initiate_chat(
        recipient=gemini_agent,
        message=prompt
    )

    for msg in chat_result.chat_history:
        if msg["role"] == "user":
            return msg["content"]

    return "No AI resources found."


import re

def parse_ai_text_to_resources(text: str) -> list:
    resources = []
    blocks = text.strip().split("•")
    
    for block in blocks:
        if not block.strip():
            continue

        resource = {}
        lines = block.strip().split("\n")
        for line in lines:
            line = line.strip()

            # 處理 Markdown 格式的 URL
            md_url_match = re.search(r"\[(.*?)\]\((https?://.*?)\)", line)
            if md_url_match:
                resource["title"] = md_url_match.group(1)
                resource["url"] = md_url_match.group(2)
                continue

            # 容錯：英文冒號或中文冒號
            if ":" in line or "：" in line:
                parts = re.split(r"[:：]", line, 1)
                key = parts[0].strip().lower()
                val = parts[1].strip()

                # 關鍵字容錯（type/title/url）
                if "title" in key:
                    resource["title"] = val
                elif "type" in key:
                    resource["type"] = val
                elif "url" in key and "http" in val:
                    resource["url"] = val

        # 只要有 title 和 url，我們就收下
        if "title" in resource and "url" in resource:
            if "type" not in resource:
                resource["type"] = "Unknown"
            resources.append(resource)

    return resources



import os
import json

def get_local_resources(role: str, skills: str, json_path="local_resources.json") -> list:
    if not os.path.exists(json_path):
        return []

    with open(json_path, "r", encoding="utf-8") as f:
        resource_data = json.load(f)

    role = role.strip().lower()
    matched_key = None

    # 模糊匹配 role 關鍵字
    for key in resource_data:
        if key.lower() in role:
            matched_key = key
            break

    if not matched_key:
        return []

    return resource_data[matched_key]  # 回傳 list of dict


import json

def get_combined_resources(role: str, skills: list) -> str:
    local_results = get_local_resources(role, skills)

    if local_results:
        resource_lines = []
        for item in local_results:
            category = item.get("type", "Resource")
            title = item.get("title", "Untitled")
            url = item.get("url", "")
            line = f"[{category}] {title} 👉 {url}"
            resource_lines.append(line)

        return "\n".join(resource_lines)

    # 若本地找不到 → 呼叫 AI
    ai_text = get_ai_resources(role, skills)
    if ai_text:
        return f"{ai_text.strip()}"
    else:
        return "⚠️ No resources found for the given role and skills."




from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def save_resources_pdf(resources: list, pdf_path: str):
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    x = 1 * inch
    y = height - 1 * inch
    line_height = 18

    for res in resources:
        text = f"[{res['type']}] {res['title']}"
        c.drawString(x, y, text)
        # 加超連結（範圍可依文字長度調整）
        link_width = c.stringWidth(text)
        c.linkURL(res['url'], (x, y - 2, x + link_width, y + 12), relative=0)
        y -= line_height

        # 預防頁面過長
        if y < 1 * inch:
            c.showPage()
            y = height - 1 * inch

    c.save()


from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from reportlab.lib.colors import blue
from PIL import Image

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from PIL import Image

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

pdfmetrics.registerFont(TTFont("Montserrat", "/workspaces/Gild-chatbot/pages/Montserrat-Bold.ttf"))


def create_pdf_with_resources_on_image(
    image_path: str,
    resources: list,
    output_buffer: BytesIO,
    start_y: int = 500
):
    c = canvas.Canvas(output_buffer, pagesize=(1080, 720))
    image_reader = ImageReader(image_path)
    c.drawImage(image_reader, 0, 0, width=1080, height=720)

    x = 575
    y = start_y
    line_height = 30

    for res in resources:
        title = res.get("title", "")
        res_type = res.get("type", "")
        url = res.get("url", "")
        c.setFont("Helvetica", 12)
        c.setFillColor(HexColor("#2c606d"))
        link_text = f"[{res_type}] {title}"
        c.drawString(x, y, link_text)
        c.linkURL(url, (x, y - 2, x + 400, y + 15), relative=0)
        y -= line_height

    c.showPage()
    c.save()
    output_buffer.seek(0)




df = pd.read_csv("pages/saved_jobs.csv")
job_titles = df["Job Title"].dropna().tolist()
cleaned_raw = get_clean_titles(job_titles)

hard_skills = extract_all_hard_skills_as_text("pages/saved_jobs.csv")


resources = parse_ai_text_to_resources(get_ai_resources(cleaned_raw, hard_skills))
print(resources)

#ai_text = get_ai_resources(cleaned_raw, hard_skills)
#print(ai_text)