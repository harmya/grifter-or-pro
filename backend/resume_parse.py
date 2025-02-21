import PyPDF2
import docx
from typing import Dict, Optional
import os
from openai import OpenAI
from dotenv import load_dotenv
import io

load_dotenv()

class ResumeParser:
    def __init__(self, file_contents: bytes, filename: str, api_key: Optional[str] = None):
        self.file_contents = file_contents
        self.filename = filename
        self.content = self._read_file()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)

    def _read_file(self) -> str:
        """Read content from PDF or DOCX file."""
        file_extension = os.path.splitext(self.filename)[1].lower()
        
        if file_extension == '.pdf':
            return self._read_pdf()
        elif file_extension in ['.docx', '.doc']:
            return self._read_docx()
        else:
            raise ValueError("Unsupported file format. Please provide PDF or DOCX file.")

    def _read_pdf(self) -> str:
        """Extract text and embedded links from PDF file."""
        extracted_text = []
        pdf_file = io.BytesIO(self.file_contents)
        
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages:
            text = page.extract_text()
            links = []
            if "/Annots" in page:
                for annot in page["/Annots"]:
                    annot_obj = annot.get_object()
                    if annot_obj.get("/Subtype") == "/Link" and annot_obj.get("/A"):
                        uri = annot_obj["/A"].get("/URI")
                        if uri:
                            links.append(uri)
            page_content = text if text else ""
            if links:
                page_content += " \nLinks: " + ", ".join(links)
            extracted_text.append(page_content)
        return ' '.join(extracted_text)

    def _read_docx(self) -> str:
        """Extract text and embedded links from DOCX file."""
        docx_file = io.BytesIO(self.file_contents)
        doc = docx.Document(docx_file)
        
        extracted_text = []
        for paragraph in doc.paragraphs:
            text = paragraph.text
            links = []
            for rel in doc.part.rels.values():
                if "hyperlink" in rel.reltype:
                    links.append(rel.target_ref)
            if links:
                text += " \nLinks: " + ", ".join(links)
            extracted_text.append(text)
        return ' '.join(extracted_text)

    def analyze_resume(self) -> Dict:
        """Send resume content to OpenAI API for analysis."""
        messages = [
            {"role": "system", "content": """
                You are ResumeExtractor-Pro, a focused and efficient resume analyzer. Your primary mission is to extract and verify the following key information:
                
                Required Information:
                1. GitHub Presence:
                   - GitHub username
                   - GitHub profile URL
                   - Project repository links
                   - Project names
                   - Short description of the project as stated on the resume

                3. Ultra-Brief Experience Summary:
                   - Most recent/relevant position
                   - Company
                   - Short description of the work
                
                Output Format:
                GITHUB INFO
                Username: {if found}
                Profile: {if found}
                Projects: 
                - {project name} | {link} {if available} | {short description of the project as stated on the resume}
             
                EXPERIENCE
                {brief experience summary}
             
                Guidelines:
                - Extract ANY GitHub information found
                - Also, extract everything you can find about the user's projects
                - Keep summaries concise
                - Don't speculate or fill in missing information"""},
            {"role": "user", "content": f"""Please analyze this resume and extract the required information:
                
                {self.content}
            """}
        ]
        
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=1024
        )
        
        return {"analysis": completion.choices[0].message.content}

def parse_resume(file_contents: bytes, filename: str, api_key: Optional[str] = None) -> str:
    """Function to parse and analyze resume."""
    try:
        parser = ResumeParser(file_contents, filename, api_key)
        results = parser.analyze_resume()
        return results["analysis"]
    except Exception as e:
        print(f"Error processing resume: {str(e)}")