#!/usr/bin/env python3
"""
FormMind AI – Intelligent Form Processing Agent Demo
Run: python demo.py
"""

from pathlib import Path
import time
from src.parser import extract_text
from src.anonymizer import mask_pii
from src.rag import build_index
from src.qa_engine import answer_question

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# === Ensure demo folder exists ===
DEMO_DATA = Path("data/sample_forms")
DEMO_DATA.mkdir(parents=True, exist_ok=True)

# === Helper: Create simple PDFs ===
def create_pdf(filename: Path, content: str):
    styles = getSampleStyleSheet()
    story = []
    for line in content.split("\n"):
        story.append(Paragraph(line, styles["Normal"]))
        story.append(Spacer(1, 12))
    # ✅ FIX: Convert Path → str so ReportLab works on Windows
    doc = SimpleDocTemplate(str(filename), pagesize=letter)
    doc.build(story)

# === Auto-generate demo PDFs if missing ===
if not (DEMO_DATA / "employee_w2_2024.pdf").exists():
    create_pdf(DEMO_DATA / "employee_w2_2024.pdf", """
    W-2 Wage and Tax Statement 2024

    Employee: John Smith
    Employer: ABC Corporation

    Box 1 Wages: $85,000.00
    Box 2 Federal income tax withheld: $12,450.75
    """)

if not (DEMO_DATA / "employee_w2_2023.pdf").exists():
    create_pdf(DEMO_DATA / "employee_w2_2023.pdf", """
    W-2 Wage and Tax Statement 2023

    Employee: John Smith
    Employer: ABC Corporation

    Box 1 Wages: $70,000.00
    Box 2 Federal income tax withheld: $11,200.00
    """)

if not (DEMO_DATA / "employee_w2_2025.pdf").exists():
    create_pdf(DEMO_DATA / "employee_w2_2025.pdf", """
    W-2 Wage and Tax Statement 2025

    Employee: John Smith
    Employer: ABC Corporation

    Box 1 Wages: $95,000.00
    Box 2 Federal income tax withheld: $13,600.00
    """)

if not (DEMO_DATA / "confidential_letter.pdf").exists():
    create_pdf(DEMO_DATA / "confidential_letter.pdf", """
    Confidential HR Letter

    Employee: Jane Doe
    Phone: 9876543210
    Email: jane.doe@example.com
    Address: New York City, USA
    """)

# === Safe wrapper for parser ===
def normalize_doc(raw):
    if isinstance(raw, dict):
        if "text" in raw: return {"text": raw["text"]}
        elif "full_text" in raw: return {"text": raw["full_text"]}
    elif isinstance(raw, str):
        return {"text": raw}
    return {"text": str(raw)}

# === DEMO 1: Single Form Q&A ===
def demo_single_qa():
    file_path = DEMO_DATA / "employee_w2_2024.pdf"
    question = "What is the Box 2 federal income tax withheld in 2024?"
    print("\n=== 📝 Demo 1: Single Form Q&A ===")

    raw = extract_text(open(file_path, "rb").read())
    doc = normalize_doc(raw)
    text = doc["text"]

    index = build_index([doc])
    answer = answer_question(question, index)

    print(f"❓ Question: {question}")
    print("📄 Text Preview:", text[:120])
    print("✅ Answer:", answer.get("answer") if isinstance(answer, dict) else answer)

# === DEMO 2: Entity Masking / PII Redaction ===
def demo_entity_masking():
    file_path = DEMO_DATA / "confidential_letter.pdf"
    print("\n=== 🛡️ Demo 2: Entity Extraction & Masking ===")

    raw = extract_text(open(file_path, "rb").read())
    doc = normalize_doc(raw)
    text = doc["text"]

    masked_text, entity_count = mask_pii(text)

    print("📄 Original Text Preview:", text[:120])
    print("🔒 Masked Text Preview:", masked_text[:120])
    print(f"✅ Entities Masked: {entity_count}")

# === DEMO 3: Multi-Form Analysis ===
def demo_multi_form():
    files = [DEMO_DATA / f"employee_w2_{y}.pdf" for y in (2023, 2024, 2025)]
    docs = [normalize_doc(extract_text(open(f, "rb").read())) for f in files]

    index = build_index(docs)

    # Ask wages
    q1 = "What were John Smith’s Box 1 wages in 2023, 2024, and 2025?"
    a1 = answer_question(q1, index)

    # Ask tax withheld
    q2 = "What was the Box 2 federal income tax withheld in 2023, 2024, and 2025?"
    a2 = answer_question(q2, index)

    print("\n=== 📊 Demo 3: Multi-Form Holistic Analysis ===")
    print("❓ Question 1:", q1)
    print("✅ Answer:", a1.get("answer") if isinstance(a1, dict) else a1)
    print("❓ Question 2:", q2)
    print("✅ Answer:", a2.get("answer") if isinstance(a2, dict) else a2)

# === MAIN RUN ===
if __name__ == "__main__":
    start = time.time()
    print("🚀 Running FormMind AI Demo...")
    demo_single_qa()
    demo_entity_masking()
    demo_multi_form()
    print("\n⏱️ Total demo time: %.2f seconds" % (time.time() - start))
    print("🎉 Demo complete.")
