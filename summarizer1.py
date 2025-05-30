import requests
import re
import os
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
    all_summaries = []

    for i, (section_title, section_text) in enumerate(sections.items(), start=1):
        print(f"📘 Processing Section {i}: {section_title}...")

        # Split section into chunks of ~3000 characters
        chunks = [section_text[i:i+3000] for i in range(0, len(section_text), 3000)]

        section_summaries = []
        for idx, chunk in enumerate(chunks, start=1):
            summary = summarize_chunk(chunk)
            section_summaries.append(summary)
            print(f"   🔹 Chunk {idx} Summary Done.")

        # Combine all chunk summaries into a single section summary
        full_section_summary = " ".join(section_summaries)
        word_count = len(full_section_summary.split())

        print(f"\n✅ Summary of '{section_title}' ({word_count} words):\n{full_section_summary}\n{'-'*70}")
        all_summaries.append(f"## {section_title}\n{full_section_summary}\n")

    return f"📊 Total Word Count: {total_words}\n\n" + "\n".join(all_summaries)

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

    print(f"✅ Detected Sections: {list(sections.keys())}")
    return sections