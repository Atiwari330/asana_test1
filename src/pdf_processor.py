"""
PDF Processing Module
Handles extraction of text from PDF transcripts
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Process PDF files and extract text content"""
    
    def __init__(self, max_file_size_mb: int = 50):
        self.max_file_size_mb = max_file_size_mb
    
    def validate_file(self, file_content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded PDF file
        
        Args:
            file_content: Raw file bytes
            filename: Name of the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        if not filename.lower().endswith('.pdf'):
            return False, "File must be a PDF"
        
        # Check file size
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            return False, f"File too large: {file_size_mb:.1f}MB (max: {self.max_file_size_mb}MB)"
        
        # Check if it's a valid PDF
        try:
            # Try to read first few bytes to verify PDF header
            if not file_content[:4] == b'%PDF':
                return False, "Invalid PDF file format"
        except Exception:
            return False, "Could not validate PDF format"
        
        return True, None
    
    def extract_text(self, file_content: bytes, method: str = "auto") -> Tuple[str, str]:
        """
        Extract text from PDF using the specified or best available method
        
        Args:
            file_content: PDF file content as bytes
            method: Extraction method ("pymupdf", "pdfplumber", "pypdf2", or "auto")
            
        Returns:
            Tuple of (extracted_text, method_used)
        """
        if method == "auto":
            # Try methods in order of preference
            methods = [
                ("pymupdf", self._extract_with_pymupdf),
                ("pdfplumber", self._extract_with_pdfplumber),
                ("pypdf2", self._extract_with_pypdf2)
            ]
            
            for method_name, extract_func in methods:
                try:
                    text = extract_func(file_content)
                    if text and text.strip():
                        logger.info(f"Successfully extracted text using {method_name}")
                        return self._clean_text(text), method_name
                except Exception as e:
                    logger.warning(f"Method {method_name} failed: {str(e)}")
                    continue
            
            return "", "none"
        
        else:
            # Use specific method
            extract_funcs = {
                "pymupdf": self._extract_with_pymupdf,
                "pdfplumber": self._extract_with_pdfplumber,
                "pypdf2": self._extract_with_pypdf2
            }
            
            if method in extract_funcs:
                try:
                    text = extract_funcs[method](file_content)
                    return self._clean_text(text), method
                except Exception as e:
                    logger.error(f"Extraction with {method} failed: {str(e)}")
                    return "", method
            
            return "", "invalid_method"
    
    def _extract_with_pymupdf(self, file_content: bytes) -> str:
        """Extract text using PyMuPDF"""
        doc = fitz.open(stream=file_content, filetype="pdf")
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            if text.strip():
                text_parts.append(text)
        
        doc.close()
        return '\n'.join(text_parts)
    
    def _extract_with_pdfplumber(self, file_content: bytes) -> str:
        """Extract text using pdfplumber"""
        import io
        text_parts = []
        
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        return '\n'.join(text_parts)
    
    def _extract_with_pypdf2(self, file_content: bytes) -> str:
        """Extract text using PyPDF2"""
        import io
        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text.strip():
                text_parts.append(text)
        
        return '\n'.join(text_parts)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text for better processing
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        import re
        
        # Fix hyphenated words across lines
        text = re.sub(r'-\s*\n\s*', '', text)
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers (standalone numbers)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Remove common headers/footers
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        text = text.strip()
        
        return text