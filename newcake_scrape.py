import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

headers = {
    "User-Agent": "Mozilla/5.0"
}

# 爬內頁取得完整描述
def get_full_desc(job_url):
    try:
        res = requests.get(job_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        content_div = soup.find("div", class_="ContentSection_content__e3ios")
        return content_div.get_text(separator="\n", strip=True) if content_div else "N/A"
    except:
        return "N/A"

# 表層爬資料
def parsing_job(job):
    try:
        a_tag = job.find('a', {'data-algolia-event-name': 'click_job'})
        job_name = a_tag.text.strip()
        job_url = "https://www.cake.me" + a_tag['href']
    except:
        job_name = 'N/A'
        job_url = ''

    try:
        comp_name = job.find('a', {'data-algolia-event-name': 'click_page'}).text.strip()
    except:
        comp_name = 'N/A'

    try:
        job_desc = job.find('div', class_='JobSearchItem_description__si5zg').text.strip()
    except:
        job_desc = 'N/A'

    job_tags = [t.text.strip() for t in job.select('div.Tags_wrapper__UQ34T > div')]

    # 補 full_desc
    full_desc = get_full_desc(job_url) if job_url else 'N/A'

    return [comp_name, job_name, full_desc, job_tags, job_url]

# 主爬蟲流程
def crawl_jobs():
    if not os.path.exists('pages'):
        os.makedirs('pages')

    data = []
    for p in range(1, 63):  # 測試建議先從前兩頁試爬
        url = f'https://www.cake.me/jobs/%E5%AF%A6%E7%BF%92?locale=zh-TW&page={p}'
        print(f"爬第 {p} 頁：{url}")
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        jobs = soup.select('div.JobSearchHits_list__3UtHp > div')

        for job in jobs:
            row = parsing_job(job)
            print(f"抓到職缺：{row[1]}")
            data.append(row)
            time.sleep(1)  # 避免過快被封鎖

        time.sleep(2)

    df = pd.DataFrame(data, columns=['公司名稱', '職缺名稱', '完整描述', '技能關鍵字', '職缺網址'])
    df.to_csv('pages/jobsthousands.csv', index=False, encoding='utf-8-sig')
    print("✅ 已儲存至 pages/jobsthousands.csv")

if __name__ == "__main__":
    crawl_jobs()
