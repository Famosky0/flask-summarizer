from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from utils import extract_text_from_pdf, export_summary_to_docx, export_references_to_docx
from summarizer import generate_summary

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/summarize', methods=['POST'])
def summarize():
    if 'pdf' not in request.files:
        flash("No file part in the request.")
        return redirect(url_for('index'))

    file = request.files['pdf']
    if file.filename == '':
        flash("No file selected.")
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    extracted_text = extract_text_from_pdf(file_path)
    result = generate_summary(extracted_text)

    # 🛡️ Defensive check
    if not result or "summarized_sections" not in result:
        flash("Summarization failed. Please check the PDF content or try again.")
        return redirect(url_for("index"))

    # 📄 Safe to continue now
    export_summary_to_docx(result["summarized_sections"], "summary.docx")
    export_references_to_docx(result["references_text"], "references.docx")

    return render_template(
        "summary.html",
        summaries=result["summarized_sections"],
        word_count=result["total_words"],
        estimated_time=result["estimated_time"],
        references_text=result["references_text"]
    )



@app.route("/download/summary.docx")
def download_summary():
    return send_file("summary.docx", as_attachment=True)

@app.route("/download/references.docx")
def download_references():
    return send_file("references.docx", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
