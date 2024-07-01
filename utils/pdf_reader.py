# This file contains util functions for parsing pdfs. 

import re
from  PyPDF2 import PdfReader


def read_pdf(file_path):
    # Initialize a variable to hold all the text
    all_text = ""
    
    # Open the PDF file
    with open(file_path, "rb") as file:
        # Initialize a PDF reader object
        pdf_reader = PdfReader(file)
        
        # Iterate through each page in the PDF
        for page in pdf_reader.pages:
            # Extract text from the page
            text = page.extract_text()
            if text:
                all_text += text  # Append the extracted text to all_text

    return all_text


def clean_text(text):
    # Replace all newline characters with a single space
    cleaned_text = re.sub(r'\n', '', text)
    # Replace two or more spaces with a single space
    cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)
    # Replace a space followed by a period with just a period
    cleaned_text = re.sub(r' \.', '.', cleaned_text)
    # Replace a space followed by a comma with just a comma
    cleaned_text = re.sub(r' ,', ',', cleaned_text)
    return cleaned_text