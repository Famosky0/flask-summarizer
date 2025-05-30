import requests
import re
import os
from dotenv import load_dotenv

API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

# Load environment variables from .env
load_dotenv()

# Access the token
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
headers = {"Authorization": f"Bearer {HF_TOKEN}"}


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
            return result[0]["summary_text"].strip()
        else:
            print(f"❌ Unexpected API output: {result}")
            return ""
    except Exception as e:
        print(f"❌ Error summarizing chunk: {e}\nRaw: {response.text}")
        return ""


def split_into_sections(text):
    section_headers = [
        "recommendations and conclusion", "abstract", "introduction", "background", "related work",
        "methodology", "methods", "approach", "experiments",
        "results", "discussion", "conclusion", "references","background to the study","problem statement "
    ]

    # Improved pattern
    pattern = r"(?i)(?:^|\n)\s*(\d{0,2}\.?\d*\s*)?(" + "|".join([h.replace(" ", r"\s+") for h in section_headers]) + r")\s*:?\s*(?=\n|$)"
    matches = list(re.finditer(pattern, text.lower()))

    if len(matches) < 2:
        print("⚠️ Not enough headers found, fallback to ALL CAPS...")
        caps_matches = list(re.finditer(r"\n([A-Z][A-Z\s\d\-:]{4,})\n", text))
        if not caps_matches:
            print("❌ No clear section headers. Returning full text.")
            return {"Full Text": text}

        sections = {}
        for i, match in enumerate(caps_matches):
            section_name = match.group(1).strip().title()
            start = match.end()
            end = caps_matches[i + 1].start() if i + 1 < len(caps_matches) else len(text)
            sections[section_name] = text[start:end].strip()
        return sections

    sections = {}
    for i, match in enumerate(matches):
        section_name = match.group(2).title()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_content = text[start:end].strip()
        sections[section_name] = section_content

    print(f"✅ Detected Sections: {list(sections.keys())}")
    return sections


def generate_summary(text):
    total_words = len(text.split())
    print(f"\n📊 Total Word Count: {total_words}\n")

    sections = split_into_sections(text)
    summarized_sections = {}
    references_text = ""
    chunk_count = 0

    for section_title, section_text in sections.items():
        if section_title.lower().startswith("references"):
            references_text += section_text + "\n"
            continue

        print(f"📘 Processing Section: {section_title}...")
        chunks = [section_text[i:i+3000] for i in range(0, len(section_text), 3000)]
        section_summaries = []

        for idx, chunk in enumerate(chunks, 1):
            print(f"   🔹 Chunk {idx} Summary...", end=" ")
            summary = summarize_chunk(chunk)
            if summary.strip():
                section_summaries.append(summary)
                print("✅ Done.")
            else:
                print("❌ Skipped.")

        summarized_sections[section_title] = " ".join(section_summaries)
        chunk_count += len(chunks)

    estimated_time = chunk_count * 5

    return {
        "total_words": total_words,
        "summarized_sections": summarized_sections,
        "references_text": references_text.strip(),
        "estimated_time": estimated_time,
        "chunk_count": chunk_count
    }
