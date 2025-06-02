from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from coding.utils import paging
from io import BytesIO
import os
from coding.persona_tools import persona_name, persona_title, get_clean_titles, format_titles_centered
from coding.persona_tools import extract_all_hard_skills_as_text, persona_hardskill, persona_softskill, extract_all_soft_skills_as_text
import pandas as pd
from coding.persona_tools import parse_ai_text_to_resources, get_ai_resources

df = pd.read_csv("pages/saved_jobs.csv")
job_titles = df["Job Title"].dropna().tolist()
cleaned_raw = get_clean_titles(job_titles)

hard_skills = extract_all_hard_skills_as_text("pages/saved_jobs.csv")


resources = parse_ai_text_to_resources(get_ai_resources(cleaned_raw, hard_skills))
print(resources)