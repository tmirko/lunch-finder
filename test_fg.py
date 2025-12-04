#!/usr/bin/env python3
"""Test Food Garden PDF parsing."""
import requests
import io
from PyPDF2 import PdfReader

url = 'https://foodgarden.wien/wp-content/uploads/Foodgarden-Aloha-Bowl-Menu.pdf'
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    response = requests.get(url, timeout=15, headers=headers)
    print(f'Status: {response.status_code}')
    print(f'Content length: {len(response.content)}')
    
    pdf_file = io.BytesIO(response.content)
    reader = PdfReader(pdf_file)
    print(f'Pages: {len(reader.pages)}')
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        print(f'\n--- Page {i+1} ---')
        print(text[:2000] if text else 'No text')
        
except Exception as e:
    print(f'Error: {e}')
