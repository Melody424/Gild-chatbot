from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from coding.utils import paging
from io import BytesIO
import os
from coding.persona_tools import persona_name, persona_title, get_clean_titles, format_titles_centered
import pandas as pd




def make_persona(image_path, output_path = "pages/persona_{name}.png"):
    job_titles = df["Job Title"].dropna().tolist()
    cleaned_raw = get_clean_titles(job_titles)
    print(format_titles_centered(cleaned_raw))

    img, name = persona_name(image_path)
    img = persona_title(img, cleaned_raw)


    if img is None:
        return  # 尚未輸入名字，提早結束


    # 將 PIL 圖片轉成 BytesIO
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # 顯示圖片
    st.image(img_bytes, caption="你的個人化 Persona", use_container_width=True)

    # 提供下載按鈕（從記憶體中下載）
    st.download_button(
        label="⬇️ Download Your Persona",
        data=img_bytes,
        file_name=f"persona_{name}.png",
        mime="image/png"
    )

def save_lang():
    st.session_state["lang_setting"] = st.session_state.get("language_select")

user_image = "https://www.w3schools.com/howto/img_avatar.png"


def main():
    st.title("🧑‍💼 Test")        
    
    with st.sidebar:
        paging()
        selected_lang = st.selectbox(
            "Language",
            ["English", "繁體中文"],
            index=0,
        )
        st.write("Selected language:", selected_lang)
        st.image(user_image)
        st.write("sidebar loaded")


    # 讀取職缺清單並清洗
    df = pd.read_csv("pages/saved_jobs.csv")
    job_titles = df["Job Title"].dropna().tolist()
    cleaned_raw = get_clean_titles(job_titles)
    print(format_titles_centered(cleaned_raw))  # debug用

    # 取得輸入名字與生成底圖
    img, name = persona_name("pages/template.png")
    if img is None:
        return

    # 疊加職稱
    img = persona_title(img, cleaned_raw)

    # 圖片轉 BytesIO 用於顯示與下載
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    st.image(img_bytes, caption="你的個人化 Persona", use_container_width=True)
    st.download_button(
        label="⬇️ Download Your Persona",
        data=img_bytes,
        file_name=f"persona_{name}.png",
        mime="image/png"
    )



if __name__ == "__main__":
    main()