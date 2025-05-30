import requests
import re
import os
import math
from dotenv import load_dotenv


API_URL = os.getenv("API_URL")

# Load environment variables from .env
load_dotenv()

# Access the token
HF_TOKEN = os.getenv("HF_TOKEN")
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def generate_summary(text):
    total_words = len(text.split())
    print(f"\n📊 Total Word Count: {total_words}\n")

    sections = split_into_sections(text)
    summarized_sections = {}
    references_text = ""
    chunk_count = 0

    for section_title, section_text in sections.items():
        if section_title.lower() == "references":
            references_text = section_text
            continue

        chunks = [section_text[i:i+3000] for i in range(0, len(section_text), 3000)]
        chunk_count += len(chunks)

        section_summaries = []
        for chunk in chunks:
            summary = summarize_chunk(chunk)
            section_summaries.append(summary)

        summarized_sections[section_title] = " ".join(section_summaries)

    estimated_time = chunk_count * 5  # Assuming ~5 seconds per chunk
    return {
        "total_words": total_words,
        "summarized_sections": summarized_sections,
        "references_text": references_text,
        "estimated_time": estimated_time,
        "chunk_count": chunk_count
    }

def summarize_chunk(text):
    payload = {
        "inputs": text.strip(),
        "parameters": {
            "max_new_tokens": 300,
            "do_sample": False
        }
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    try:
        result = response.json()
        if isinstance(result, list) and "summary_text" in result[0]:
            return result[0]["summary_text"]
        else:
            return str(result)
    except Exception as e:
        return f"❌ Error summarizing chunk: {e}\nRaw: {response.text}"

def split_into_sections(text):
    section_headers = [
        "abstract", "introduction", "background", "related work",
        "methodology", "methods", "approach", "experiments",
        "results", "discussion", "conclusion", "references"
    ]

    pattern = r"(?:^|\n)(\d{0,2}\.?\d*\s*)?(" + "|".join(section_headers) + r")\s*(?:\n|$)"
    matches = list(re.finditer(pattern, text.lower()))
    if not matches:
        print("⚠️ No section headers found. Using full text.")
        return {"Full Text": text}

    sections = {}
    for i, match in enumerate(matches):
        section_name = match.group(2).title()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_content = text[start:end].strip()
        sections[section_name] = section_content

    return sections
