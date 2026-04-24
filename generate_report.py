from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def create_report():
    doc = Document()

    # --- Title Page ---
    title = doc.add_heading('FraudShield: Technical Documentation', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    subtitle = doc.add_paragraph('AI-Powered Real-Time Digital Arrest & Fraud Detection System')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('\n')

    # --- Section 1: Executive Summary ---
    doc.add_heading('1. Executive Summary', level=1)
    doc.add_paragraph(
        'FraudShield is a comprehensive security infrastructure designed to combat the rising threat of "Digital Arrest" scams '
        'and financial fraud in India. It integrates Machine Learning, Natural Language Processing (NLP), and '
        'Big Data analytics to provide real-time threat assessments for incoming messages and financial transactions.'
    )

    # --- Section 2: System Architecture ---
    doc.add_heading('2. System Architecture', level=1)
    doc.add_paragraph('The system follows a modern decoupled architecture:')
    doc.add_paragraph('• Frontend: React.js PWA (Hosted on Vercel/GitHub Pages)', style='List Bullet')
    doc.add_paragraph('• Backend: Flask Python API (Hosted on Render)', style='List Bullet')
    doc.add_paragraph('• Database: Firebase Real-time Database (for fraud tracking)', style='List Bullet')
    doc.add_paragraph('• Data Engine: Optimized Parquet Storage for 100k+ records', style='List Bullet')

    # --- Section 3: Core Detection Modules ---
    doc.add_heading('3. Core Detection Modules', level=1)

    doc.add_heading('3.1 Spam & Scam Engine (spam_detection.py)', level=2)
    doc.add_paragraph(
        'Uses a hybrid approach combining an XGBoost Machine Learning model with an extensive '
        'synergy-based keyword matching engine. It detects:'
    )
    doc.add_paragraph('• Digital Arrest Patterns (CBI, Crime Branch, Police impersonation)', style='List Bullet')
    doc.add_paragraph('• Violence & Physical Threats (Direct threats in English & Hindi)', style='List Bullet')
    doc.add_paragraph('• Extortion & Blackmail (Urgent money demands, "warna dekh" logic)', style='List Bullet')

    doc.add_heading('3.2 Financial Investigation (account_lookup.py)', level=2)
    doc.add_paragraph(
        'Cross-references extracted account numbers against a massive 100k-row financial dataset '
        'to build a "Risk Profile" for the receiver.'
    )

    # --- Section 4: Performance Optimizations ---
    doc.add_heading('4. Performance Optimizations', level=1)
    doc.add_paragraph(
        'To ensure the system works on cloud free-tiers (Render/Vercel) without hitting RAM limits or timeouts:'
    )
    doc.add_paragraph('• Parquet Migration: Converted CSVs to binary Parquet, reducing load time from 45s to <1s.', style='List Bullet')
    doc.add_paragraph('• Background Threading: Data and ML models load in a background thread, allowing the API to respond instantly on startup.', style='List Bullet')
    doc.add_paragraph('• Type Downcasting: Optimized numeric types in memory to reduce RAM usage by 60%.', style='List Bullet')

    # --- Section 5: Multilingual Intelligence ---
    doc.add_heading('5. Multilingual Intelligence', level=1)
    doc.add_paragraph(
        'The system is specifically tuned for the Indian context, supporting Romanized Hindi (Hinglish) '
        'number words. Phrases like "ek lakh", "do lakh", or "paanch crore" are automatically '
        'recognized and factored into the final threat score.'
    )

    # Save the document
    doc.save('FraudShield_Technical_Report.docx')
    print("Report generated successfully: FraudShield_Technical_Report.docx")

if __name__ == "__main__":
    create_report()
