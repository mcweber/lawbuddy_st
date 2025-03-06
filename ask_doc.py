import pandas as pd
import PyPDF2 as pdf2
import io

def read_pdf_file(file_path: str = "") -> str:
    pdf_file = open(file_path, 'rb')
    pdf_reader = pdf2.PdfReader(pdf_file)
    pdf_text = ''
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        pdf_text += page.extract_text()
    return pdf_text

def read_pdf_streamlit(file_data: io.BytesIO) -> str:
    pdf_reader = pdf2.PdfReader(file_data)
    pdf_text = ''
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        pdf_text += page.extract_text()
    return pdf_text

def read_excel_file(file_path: str = "") -> str:
    df = pd.read_excel(file_path)
    return df.to_json(orient='records')

def read_excel_streamlit(file_data: io.BytesIO) -> str:
    df = pd.read_excel(file_data)
    # return = df.to_json(orient='records')
    return df.to_csv(index=False)

def read_txt_file(file_path: str = "") -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def read_txt_streamlit(file_data: io.BytesIO) -> str:
   return file_data.read()
