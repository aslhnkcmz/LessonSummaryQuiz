import os
from PyPDF2 import PdfReader
from docx import Document

class FileService:
    def extract_text(self, file):
        filename = file.filename.lower()
        text = ""

        try:
            # 1. PDF Dosyası
            if filename.endswith('.pdf'):
                reader = PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            # 2. Word Dosyası (.docx)
            elif filename.endswith('.docx'):
                doc = Document(file)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            
            # 3. Metin Dosyası (.txt)
            elif filename.endswith('.txt'):
                text = file.read().decode('utf-8')
                
        except Exception as e:
            print(f"Error reading file: {e}")
            return None

        return text.strip() if text else None