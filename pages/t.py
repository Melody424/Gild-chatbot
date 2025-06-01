import ast
import pandas as pd

job_df = pd.read_csv("pages/jobsthousands.csv")
job_df.fillna("", inplace=True)

def unified_search(df, keyword):
    keyword = keyword.lower().strip()

    def in_tags(tag_string):
        try:
            tags = ast.literal_eval(tag_string)
            tags = [t.lower().strip() for t in tags if isinstance(t, str)]
            return any(keyword in t for t in tags)
        except:
            return False

    mask_title = df['job_title'].str.lower().str.contains(keyword, na=False)
    mask_desc = df['job_desc'].str.lower().str.contains(keyword, na=False)
    mask_tags = df['job_tags'].apply(in_tags)

    result_df = df[mask_title | mask_desc | mask_tags]
    return result_df[['comp', 'job_title', 'job_desc', 'job_tags']].reset_index(drop=True)

user_input = "excel"  # 使用者輸入的關鍵字
matched_df = unified_search(job_df, user_input)

print(matched_df)
# matched_df 即為你要的表格格式



import ast
import streamlit as st
from coding.utils import paging


import time
import json
from dotenv import load_dotenv
import os
import pandas as pd

# 載入職缺資料
job_df = pd.read_csv("pages/jobsthousands.csv")
job_df.fillna("", inplace=True)

# 關鍵字搜尋函數
def unified_search(df, keyword):
    keyword = keyword.lower().strip()

    def in_tags(tag_string):
        try:
            tags = ast.literal_eval(tag_string)
            tags = [t.lower().strip() for t in tags if isinstance(t, str)]
            return any(keyword in t for t in tags)
        except:
            return False

    mask_title = df['job_title'].str.lower().str.contains(keyword, na=False)
    mask_desc = df['job_desc'].str.lower().str.contains(keyword, na=False)
    mask_tags = df['job_tags'].apply(in_tags)

    result_df = df[mask_title | mask_desc | mask_tags]
    return result_df[['comp', 'job_title', 'job_desc', 'job_tags']].reset_index(drop=True)

# generate_response 函數：接收使用者輸入並回傳搜尋結果
def generate_response(prompt):
    matched_df = unified_search(job_df, prompt)
    return matched_df

# Streamlit 主程式
def main():
    st.set_page_config(page_title="📋 Internship Finder", layout="wide")
    st.title("🔍 Internship Navigator")

    user_input = st.chat_input("請輸入關鍵字來搜尋實習職缺...", key="chat_input")

    if user_input:
        st.chat_message("user").write(user_input)
        result_df = generate_response(user_input)

        with st.chat_message("assistant"):
            if result_df.empty:
                st.write("找不到符合的職缺，請試試其他關鍵字！")
            else:
                st.write("以下是為你找到的相關實習職缺：")
                st.dataframe(result_df, use_container_width=True)

    with st.sidebar:
        paging()

if __name__ == "__main__":
    main()


###表格的


import ast
import streamlit as st
import pandas as pd
from coding.utils import paging

# 載入職缺資料
job_df = pd.read_csv("pages/jobsthousands.csv")
job_df.fillna("", inplace=True)

# 計算某字串出現次數（忽略大小寫）
def count_keyword_occurrences(text, keyword):
    if not isinstance(text, str):
        return 0
    return text.lower().count(keyword)

# 將 job_tags 字串轉成用頓號連結的字串
def format_job_tags(tag_string):
    try:
        tags = ast.literal_eval(tag_string)
        tags = [t.strip() for t in tags if isinstance(t, str) and t.strip()]
        return '、'.join(tags)
    except:
        return ""

# 加權搜尋與排序
def unified_search(df, keyword):
    keyword = keyword.lower().strip()

    scores = []
    for _, row in df.iterrows():
        score = 0
        title_count = count_keyword_occurrences(row['job_title'], keyword)
        desc_count = count_keyword_occurrences(row['job_desc'], keyword)
        try:
            tags = ast.literal_eval(row['job_tags'])
            tags_lower = [t.lower().strip() for t in tags if isinstance(t, str)]
            tags_count = sum(keyword in t for t in tags_lower)
        except:
            tags_count = 0

        # 權重設定（可依需求調整）
        score += title_count * 10
        score += desc_count * 2
        score += tags_count * 6

        scores.append(score)

    df['score'] = scores
    filtered_df = df[df['score'] > 0].copy()
    filtered_df.sort_values(by='score', ascending=False, inplace=True)

    # 格式化 job_tags
    filtered_df['job_tags'] = filtered_df['job_tags'].apply(format_job_tags)
    
    # 只取前6筆
    return filtered_df.head(6)[['comp', 'job_title', 'job_desc', 'job_tags', 'job_url']].reset_index(drop=True)

# generate_response 函數：接收使用者輸入並回傳搜尋結果
def generate_response(prompt):
    matched_df = unified_search(job_df, prompt)
    return matched_df

# Streamlit 主程式
def main():
    st.set_page_config(page_title="📋 Internship Finder", layout="wide")
    st.title("🔍 Internship Navigator")

    user_input = st.chat_input("請輸入關鍵字來搜尋實習職缺...", key="chat_input")

    if user_input:
        st.chat_message("user").write(user_input)
        result_df = generate_response(user_input)

        with st.chat_message("assistant"):
            if result_df.empty:
                st.write("找不到符合的職缺，請試試其他關鍵字！")
            else:
                st.write("以下是為你找到的相關實習職缺：")

                # 重命名欄位顯示名稱
                result_df_display = result_df.rename(columns={
                    'comp': 'Company',
                    'job_title': 'Job Title',
                    'job_desc': 'Job Description',
                    'job_tags': 'Job Keywords',
                    'job_url': 'Job URL'
                })

                st.dataframe(result_df_display, use_container_width=True)

    # 側邊欄paging() 保留
    with st.sidebar:
        paging()

if __name__ == "__main__":
    main()





## HTML的！！！！！


import ast
import streamlit as st
import pandas as pd
from coding.utils import paging

# 載入職缺資料
job_df = pd.read_csv("pages/jobsthousands.csv")
job_df.fillna("", inplace=True)

# 計算某字串出現次數（忽略大小寫）
def count_keyword_occurrences(text, keyword):
    if not isinstance(text, str):
        return 0
    return text.lower().count(keyword)

# 將 job_tags 字串轉成用頓號連結的字串
def format_job_tags(tag_string):
    try:
        tags = ast.literal_eval(tag_string)
        tags = [t.strip() for t in tags if isinstance(t, str) and t.strip()]
        return '、'.join(tags)
    except:
        return ""

# 加權搜尋與排序
def unified_search(df, keyword):
    keyword = keyword.lower().strip()

    scores = []
    for _, row in df.iterrows():
        score = 0
        title_count = count_keyword_occurrences(row['job_title'], keyword)
        desc_count = count_keyword_occurrences(row['job_desc'], keyword)
        try:
            tags = ast.literal_eval(row['job_tags'])
            tags_lower = [t.lower().strip() for t in tags if isinstance(t, str)]
            tags_count = sum(keyword in t for t in tags_lower)
        except:
            tags_count = 0

        # 權重設定（可依需求調整）
        score += title_count * 10
        score += desc_count * 2
        score += tags_count * 6

        scores.append(score)

    df['score'] = scores
    filtered_df = df[df['score'] > 0].copy()
    filtered_df.sort_values(by='score', ascending=False, inplace=True)

    # 格式化 job_tags
    filtered_df['job_tags'] = filtered_df['job_tags'].apply(format_job_tags)
    
    return filtered_df[['comp', 'job_title', 'job_desc', 'job_tags', 'job_url']].reset_index(drop=True)

# generate_response 函數：接收使用者輸入並回傳搜尋結果
def generate_response(prompt):
    matched_df = unified_search(job_df, prompt)
    return matched_df

# Streamlit 主程式
def main():
    st.set_page_config(page_title="📋 Internship Finder", layout="wide")
    st.title("🔍 Internship Navigator")

    if 'display_count' not in st.session_state:
        st.session_state.display_count = 6
    if 'keyword' not in st.session_state:
        st.session_state.keyword = ""
    if 'result_df' not in st.session_state:
        st.session_state.result_df = pd.DataFrame()

    user_input = st.chat_input("請輸入關鍵字來搜尋實習職缺...", key="chat_input")

    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.keyword = user_input
        st.session_state.result_df = generate_response(user_input)
        st.session_state.display_count = 6

    if not st.session_state.result_df.empty:
        with st.chat_message("assistant"):
            st.write(f"以下是為你找到的相關實習職缺（顯示前 {min(st.session_state.display_count, len(st.session_state.result_df))} 筆）：")

        display_df = st.session_state.result_df.head(st.session_state.display_count)
        for idx, row in display_df.iterrows():
            st.write(f"**Company:** {row['comp']}")
            st.write(f"**Job Title:** {row['job_title']}")
            st.write(f"**Job Description:** {row['job_desc']}")
            st.write(f"**Job Keywords:** {row['job_tags']}")
            st.markdown(f"[🔗 Apply Here]({row['job_url']})", unsafe_allow_html=True)
            st.markdown("---")

        # 只要還有更多職缺，就顯示按鈕
        if len(st.session_state.result_df) > st.session_state.display_count:
            if st.button("查看更多職缺"):
                st.session_state.display_count += 6

    with st.sidebar:
        paging()

if __name__ == "__main__":
    main()



###可以勾選的表格！！！！

import ast
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from coding.utils import paging

# 載入職缺資料
job_df = pd.read_csv("pages/jobsthousands.csv")
job_df.fillna("", inplace=True)

# 計算某字串出現次數（忽略大小寫）
def count_keyword_occurrences(text, keyword):
    if not isinstance(text, str):
        return 0
    return text.lower().count(keyword)

# 將 job_tags 字串轉成用頓號連結的字串
def format_job_tags(tag_string):
    try:
        tags = ast.literal_eval(tag_string)
        tags = [t.strip() for t in tags if isinstance(t, str) and t.strip()]
        return '、'.join(tags)
    except:
        return ""

# 加權搜尋與排序
def unified_search(df, keyword):
    keyword = keyword.lower().strip()

    scores = []
    for _, row in df.iterrows():
        score = 0
        title_count = count_keyword_occurrences(row['job_title'], keyword)
        desc_count = count_keyword_occurrences(row['job_desc'], keyword)
        try:
            tags = ast.literal_eval(row['job_tags'])
            tags_lower = [t.lower().strip() for t in tags if isinstance(t, str)]
            tags_count = sum(keyword in t for t in tags_lower)
        except:
            tags_count = 0

        # 權重設定（可依需求調整）
        score += title_count * 10
        score += desc_count * 2
        score += tags_count * 6

        scores.append(score)

    df['score'] = scores
    filtered_df = df[df['score'] > 0].copy()
    filtered_df.sort_values(by='score', ascending=False, inplace=True)

    # 格式化 job_tags
    filtered_df['job_tags'] = filtered_df['job_tags'].apply(format_job_tags)
    
    # 只取前20筆，方便勾選多筆
    return filtered_df.head(20)[['comp', 'job_title', 'job_desc']].reset_index(drop=True)

def generate_response(prompt):
    matched_df = unified_search(job_df, prompt)
    return matched_df

def main():
    st.set_page_config(page_title="📋 Internship Finder", layout="wide")
    st.title("🔍 Internship Navigator")

    user_input = st.chat_input("請輸入關鍵字來搜尋實習職缺...", key="chat_input")

    if "result_df" not in st.session_state:
        st.session_state.result_df = pd.DataFrame()
    if "selected_jobs" not in st.session_state:
        st.session_state.selected_jobs = []

    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.result_df = generate_response(user_input)
        st.session_state.selected_jobs = []  # 新搜尋清空之前選擇

    if not st.session_state.result_df.empty:
        df = st.session_state.result_df.rename(columns={
            'comp': 'Company',
            'job_title': 'Job Title',
            'job_desc': 'Job Description',
            'job_tags': 'Job Keywords',
            'job_url': 'Job URL'
        })

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection(selection_mode="multiple", use_checkbox=True)
        gb.configure_column("Job Description", wrapText=True, autoHeight=True)
        gb.configure_grid_options(domLayout='autoHeight')
        grid_options = gb.build()

        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            enable_enterprise_modules=False,
            fit_columns_on_grid_load=True,
            height=400,
        )

        selected_rows = grid_response['selected_rows']
        st.session_state.selected_jobs = selected_rows

        if selected_rows is not None and len(selected_rows) > 0:
            st.markdown("### ✅ 你選擇的職缺：")

            for i, job in enumerate(selected_rows, start=1):
                # 防錯：確保 job 是字典
                if isinstance(job, str):
                    import ast
                    job = ast.literal_eval(job)

                # 組成 HTML 區塊
                job_html = f"""
                <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin:10px 0; background-color:#f9f9f9;">
                    <h4>{i}. {job['Job Title']} <span style='font-size:14px; color:#666;'>({job['Company']})</span></h4>
                    <p><strong>Description:</strong> {job['Job Description']}</p>
                    <p><strong>Keywords:</strong> {job.get('Job Keywords', 'N/A')}</p>
                    <p><a href="{job.get('Job URL', '#')}" target="_blank">👉 點我看更多</a></p>
                </div>
                """
                st.markdown(job_html, unsafe_allow_html=True)


            if st.button("Show Personal Persona"):
                st.info("接下來可以在這裡用選取的職缺來生成個人Persona圖（待開發）")

    # 側邊欄保留
    with st.sidebar:
        paging()

if __name__ == "__main__":
    main()
