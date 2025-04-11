import gradio as gr
import PyPDF2
from docx import Document
import json
import google.generativeai as genai
import re
import pandas as pd
import os

# 🔑 Your Gemini API Key here
GENAI_API_KEY = "AIzaSyAVN_-mzCpydnDzIrsnDT31zL8bSg1ezzc"  

if not GENAI_API_KEY:
    raise ValueError("❌ Gemini API key not found. Please add it to the script.")

# ✅ Correct Gemini client configuration
genai.configure(api_key=GENAI_API_KEY)

# Extract text from PDF
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text.strip()

# Extract text from DOCX
def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs]).strip()

# Clean and parse JSON response
def safe_parse_json(response_text):
    try:
        clean_text = re.sub(r"^```(?:json)?|```$", "", response_text.strip(), flags=re.MULTILINE)
        return json.loads(clean_text)
    except:
        return {
            "summary": response_text,
            "highlights": None,
            "glossary": None
        }

# Call Gemini to analyze the document
def call_gemini(document_text):
    prompt = (
        f"Analyze the following legal document:\n\n{document_text}\n\n"
        "Instructions:\n"
        "- Summarize the key points of the document.\n"
        "- Highlight obligations, rights, and critical clauses (as a list of objects with 'clause' and 'description').\n"
        "- Provide simplified explanations of complex legal terms (as a dictionary).\n"
        "Return the result as JSON with keys: 'summary', 'highlights', 'glossary'."
    )
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return safe_parse_json(response.text)

# Main processing logic
def summarize_document(file):
    if file is None:
        return "No file uploaded.", None, None

    ext = os.path.splitext(file.name)[-1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(file)
    elif ext == ".docx":
        text = extract_text_from_docx(file)
    else:
        return "Unsupported file format.", None, None

    if not text.strip():
        return "No text could be extracted from the document.", None, None

    result = call_gemini(text)

    highlights_df = pd.DataFrame(result["highlights"]) if isinstance(result["highlights"], list) else None
    glossary_df = pd.DataFrame([{"Term": k, "Explanation": v} for k, v in result["glossary"].items()]) if isinstance(result["glossary"], dict) else None

    return result["summary"], highlights_df, glossary_df

# Gradio Interface
demo = gr.Interface(
    fn=summarize_document,
    inputs=gr.File(label="Upload PDF or DOCX", file_types=[".pdf", ".docx"]),
    outputs=[
        gr.Textbox(label="📝 Summary"),
        gr.Dataframe(label="📌 Highlights"),
        gr.Dataframe(label="📘 Glossary")
    ],
    title="📄 Legal Document Summarizer",
    description="Upload a legal document to receive a summary, important highlights, and a glossary of legal terms using Gemini AI."
)

demo.launch()
