# PDF Text Extraction Best Practices

## Overview

PDF text extraction is a fundamental task in natural language processing and data analysis, allowing researchers and data analysts to gain insights from unstructured text data contained within PDF files. Python offers a rich ecosystem of libraries for PDF data extraction, catering to a variety of needs. Whether you're dealing with text, tables, or images, there's a library suited for your task.

**Key Challenges in PDF Text Extraction:**
- **Encoding Issues**: PDF documents can come in a variety of encodings including UTF-8, ASCII, Unicode, etc. So, converting the PDF to text might result in the loss of data due to the encoding scheme
- **Layout Complexity**: PDFs with complex layouts, multi-column formats, tables, and embedded images
- **Scanned Documents**: Image-based PDFs that require OCR (Optical Character Recognition)
- **Font and Character Issues**: Custom fonts, missing Unicode mappings, and garbled text
- **Structural Elements**: Headers, footers, page numbers that can interfere with content extraction

**Best Library Selection Strategy (2025):**
Selecting the best library depends on your specific use case: For basic text extraction: PyPDF2 or PDFMiner. For layout-sensitive tasks: PyMuPDF or pdfplumber. For table extraction: camelot or Tabula-py. For metadata or multi-format support: Tika

## PyPDF2 vs Alternative Libraries

### Comprehensive Library Comparison

#### 1. PyPDF2
**Best For:** Simple and quick text extraction tasks, beginners

**Strengths:**
- User-friendly, making it an excellent choice for beginners. With PyPDF2, you can easily read PDF files and extract text content, as well as manage other PDF operations like merging or splitting pages
- Pure Python implementation
- Lightweight and fast installation
- Good for basic PDF manipulation (merge, split, crop)

**Weaknesses:**
- Best for simple and quick text extraction tasks. It's lightweight but struggles with complex layouts and is less accurate
- Good support for text extraction but may struggle with complex layouts in unstructured PDF files
- Limited support for complex PDF structures
- No built-in table extraction
- No image extraction capabilities

**Performance:** Speed is moderate as it may take longer for processing large PDF files

#### 2. PyMuPDF (Fitz)
**Best For:** High-performance text extraction, complex documents, production systems

**Strengths:**
- PyMuPDF ranks #1 in performance benchmarks with 0.1s average processing time
- Known for its high-performance rendering and parsing. Strong text extraction capabilities
- Offers fast and accurate text extraction with good support for complex layouts. It's a great all-rounder with additional features like image extraction
- PyMuPDF, also known as Fitz, offers advanced features for extracting text with formatting and annotations. It processes PDFs faster and supports multiple file formats like XPS and CBZ
- Comprehensive metadata extraction
- Can handle annotations, links, and bookmarks
- Supports conversion to images

**Weaknesses:**
- requires installation of non-Python software (MuPDF). It also does not enable easy access to shape objects (rectangles, lines, etc.), and does not provide table-extraction or visual debugging tools
- More complex compared to other libraries. Provides a rich set of functionalities but may have a steeper learning curve
- Larger dependency footprint

#### 3. pdfplumber
**Best For:** Layout-sensitive tasks, table extraction, visual debugging

**Strengths:**
- Built on top of pdfminer.six, it simplifies the API and adds features like table and image extraction, making it a good choice for more complex PDF documents
- Provides access to detailed information about each char, rectangle, line, et cetera — and easily extract text and tables
- Excellent for preserving text positioning and layout
- Built-in table extraction capabilities
- Visual debugging tools for understanding PDF structure
- Fine-grained control over extraction process

**Weaknesses:**
- pymupdf is substantially faster than pdfminer.six (and thus also pdfplumber)
- Moderate speed, depending on the complexity of the PDF
- More complex setup for simple tasks

#### 4. pdfminer.six
**Best For:** Advanced layout analysis, preserving document structure

**Strengths:**
- Excellent support with advanced layout information extraction
- The pdfminer.six library takes into account the structure of the PDF document and attempts to retain the line breaks and formatting present in the original document
- Most comprehensive layout analysis
- Handles complex document structures well
- Foundation for pdfplumber

**Weaknesses:**
- More complex compared to other libraries
- Steeper learning curve
- Slower processing compared to PyMuPDF

### Performance Benchmark Summary (2025)

Based on official benchmarking data:

| Library | Average Speed | Best Use Case | Complexity |
|---------|---------------|---------------|------------|
| PyMuPDF | 0.1s | Production, speed-critical | Medium |
| pypdfium2 | 0.1s | Alternative to PyMuPDF | Medium |
| pdfplumber | 0.2s+ | Layout analysis, tables | High |
| PyPDF2 | Variable | Simple extraction | Low |

## Handling Different PDF Formats

### 1. Native vs. Scanned PDFs

#### Native PDFs (Text-based)
**Characteristics:**
- Text is digitally encoded and searchable
- Created directly from applications (Word, LaTeX, etc.)
- Fonts and character mappings are preserved

**Best Libraries:**
- PyMuPDF for speed and comprehensive extraction
- pdfplumber for layout preservation
- PyPDF2 for simple cases

#### Scanned PDFs (Image-based)
**Characteristics:**
- contain no raw text data. Instead, all text is embedded within images, making Optical Character Recognition (OCR) essential for text extraction
- Require OCR processing
- Lower accuracy potential
- Preprocessing may be needed

**Recommended Approach:**
Scanned PDFs require conversion to images before text extraction. Use libraries like PyMuPDF or Pillow to convert each page into an image

### 2. Encoding and Unicode Issues

#### Common Encoding Problems:
- PDF files can contain text encoded in various character encodings, and some characters might not be recognized correctly. It's essential to handle Unicode characters and specify the appropriate encoding while extracting text to avoid potential data corruption
- Missing Unicode mappings in fonts
- Custom font encodings
- Garbled text from improper character conversion

#### Best Practices:
```python
import unicodedata

def normalize_unicode(text):
    """Normalize Unicode characters to standard form"""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')

def handle_encoding_errors(text):
    """Clean text with encoding issues"""
    # Handle common encoding problems
    text = text.replace('\ufffd', ' ')  # Replace Unicode replacement character
    text = text.replace('\x00', '')     # Remove null bytes
    text = text.encode('utf-8', 'ignore').decode('utf-8')
    return text
```

### 3. Complex Layout Handling

#### Multi-column Documents:
- Use pdfplumber for column detection and ordering
- Consider page segmentation before extraction
- PyMuPDF with custom text extraction parameters

#### Tables and Structured Data:
- pdfplumber: Built-in table detection
- Camelot: Specialized table extraction
- tabula-py: Alternative table extraction

#### Headers and Footers:
Many PDFs include dynamic elements, such as header and footer repetition across pages. Parsing tools often don't differentiate between main content and repetitive page elements, so headers, footers, and page numbers can interfere with the extraction of actual content

### 4. OCR Integration for Scanned PDFs

#### OCR Libraries Comparison (2025):

**Tesseract (pytesseract):**
- Broad Language Support: Tesseract can recognize over 100 languages right out of the box, including support for Unicode (UTF-8)
- Free and open-source
- Good accuracy for machine-printed text
- Community support

**EasyOCR:**
- If your project demands simplicity and ease of use, EasyOCR stands out. Its user-friendly API, built on deep learning frameworks like PyTorch, ensures fast and efficient OCR with support for numerous languages
- Deep learning-based
- Better handling of complex layouts

**OCRmyPDF:**
- Layout preservation: OCRmyPDF preserves the original layout, formatting, and structure of PDF documents while adding a searchable text layer
- Specialized for PDF processing
- Maintains original PDF structure

## Text Cleaning and Preprocessing

### Essential Preprocessing Steps for LLM Integration

The retrieval-augmented generation (RAG) process has gained popularity due to its potential to enhance the understanding of large language models (LLMs), providing them with context and helping to prevent hallucinations. For instance, if our "context documents" contain typos or unusual characters for an LLM, such as emojis, it could potentially confuse the LLM's understanding of the provided context

#### 1. Basic Text Normalization

**Case Normalization:**
Normalization: Convert the text to lowercase for consistency

```python
def normalize_case(text):
    """Convert text to lowercase for consistency"""
    return text.lower()
```

**Whitespace Handling:**
```python
import re

def normalize_whitespace(text):
    """Normalize all whitespace to single spaces"""
    # Replace multiple whitespace characters with single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text
```

**Line Break Handling:**
```python
def handle_line_breaks(text):
    """Handle hyphenation and line breaks from PDF extraction"""
    # Handle hyphenated words across lines
    text = re.sub(r'-\s*\n\s*', '', text)
    # Replace line breaks with spaces
    text = re.sub(r'\n+', ' ', text)
    return text
```

#### 2. Advanced Text Cleaning

**Remove Special Characters:**
Digits in the text don't add extra information to data and induce noise into algorithms. Hence, it's a good practice to remove digits from the text

```python
import string
import re

def remove_special_characters(text, keep_punctuation=False):
    """Remove or normalize special characters"""
    if not keep_punctuation:
        # Remove all punctuation
        text = ''.join([c for c in text if c not in string.punctuation])
    
    # Remove digits (optional)
    text = re.sub(r'\d+', '', text)
    
    # Remove extra special characters
    text = re.sub(r'[^\w\s]', ' ', text)
    
    return text
```

**URL and Email Cleaning:**
Many times people use URLs, especially on social media, to provide extra information to the context. The URLs don't generalize across samples and hence are noise

```python
def remove_urls_emails(text):
    """Remove URLs and email addresses"""
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    return text
```

#### 3. PDF-Specific Cleaning

**Header/Footer Removal:**
```python
def remove_headers_footers(text, patterns=None):
    """Remove common header/footer patterns"""
    if patterns is None:
        patterns = [
            r'Page \d+ of \d+',
            r'Copyright ©.*',
            r'Confidential.*',
            r'^\d+$',  # Page numbers on separate lines
        ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    return text
```

**OCR Error Correction:**
```python
def clean_ocr_errors(text):
    """Clean common OCR errors"""
    # Fix common OCR substitutions
    ocr_fixes = {
        r'\bl\b': 'I',  # lowercase l mistaken for I
        r'\b0\b': 'O',  # zero mistaken for O
        r'\brn\b': 'm', # rn mistaken for m
        r'\bvv\b': 'w', # vv mistaken for w
    }
    
    for pattern, replacement in ocr_fixes.items():
        text = re.sub(pattern, replacement, text)
    
    return text
```

### 4. Comprehensive Text Cleaning Pipeline

The order in the above function does matter. You should complete certain steps before others, such as making lowercase first

```python
import re
import string
import unicodedata
from typing import List, Optional

class PDFTextCleaner:
    """Comprehensive text cleaning pipeline for PDF-extracted text"""
    
    def __init__(self, 
                 remove_numbers: bool = False,
                 remove_punctuation: bool = False,
                 remove_stopwords: bool = False,
                 lemmatize: bool = False):
        self.remove_numbers = remove_numbers
        self.remove_punctuation = remove_punctuation
        self.remove_stopwords = remove_stopwords
        self.lemmatize = lemmatize
        
        # Initialize NLTK components if needed
        if remove_stopwords or lemmatize:
            try:
                import nltk
                from nltk.corpus import stopwords
                from nltk.stem import WordNetLemmatizer
                
                nltk.download('stopwords', quiet=True)
                nltk.download('wordnet', quiet=True)
                nltk.download('punkt', quiet=True)
                
                self.stop_words = set(stopwords.words('english'))
                self.lemmatizer = WordNetLemmatizer()
            except ImportError:
                print("NLTK not available for advanced preprocessing")
                self.remove_stopwords = False
                self.lemmatize = False
    
    def clean_text(self, text: str) -> str:
        """Apply complete cleaning pipeline"""
        if not text or not isinstance(text, str):
            return ""
        
        # Step 1: Unicode normalization
        text = self._normalize_unicode(text)
        
        # Step 2: Handle PDF-specific issues
        text = self._handle_pdf_artifacts(text)
        
        # Step 3: Basic normalization
        text = self._basic_normalization(text)
        
        # Step 4: Character cleaning
        text = self._clean_characters(text)
        
        # Step 5: Advanced cleaning (optional)
        if self.remove_stopwords or self.lemmatize:
            text = self._advanced_cleaning(text)
        
        # Step 6: Final cleanup
        text = self._final_cleanup(text)
        
        return text
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters"""
        # Normalize Unicode to NFKD form
        text = unicodedata.normalize('NFKD', text)
        # Remove non-ASCII characters if needed
        text = text.encode('ascii', 'ignore').decode('ascii')
        return text
    
    def _handle_pdf_artifacts(self, text: str) -> str:
        """Handle PDF-specific extraction artifacts"""
        # Fix hyphenated words across lines
        text = re.sub(r'-\s*\n\s*', '', text)
        
        # Handle soft line breaks
        text = re.sub(r'(?<=[a-z])\n(?=[a-z])', ' ', text)
        
        # Remove page numbers (standalone numbers)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Remove common header/footer patterns
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Copyright ©.*', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _basic_normalization(self, text: str) -> str:
        """Basic text normalization"""
        # Convert to lowercase
        text = text.lower()
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove URLs and emails
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        
        return text
    
    def _clean_characters(self, text: str) -> str:
        """Clean unwanted characters"""
        if self.remove_numbers:
            text = re.sub(r'\d+', '', text)
        
        if self.remove_punctuation:
            text = ''.join([c for c in text if c not in string.punctuation])
        else:
            # Keep basic punctuation, remove others
            text = re.sub(r'[^\w\s.,!?;:]', ' ', text)
        
        return text
    
    def _advanced_cleaning(self, text: str) -> str:
        """Advanced NLP preprocessing"""
        if not hasattr(self, 'stop_words'):
            return text
        
        import nltk
        
        # Tokenize
        tokens = nltk.word_tokenize(text)
        
        # Remove stopwords
        if self.remove_stopwords:
            tokens = [token for token in tokens if token.lower() not in self.stop_words]
        
        # Lemmatize
        if self.lemmatize:
            tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        
        # Rejoin
        text = ' '.join(tokens)
        
        return text
    
    def _final_cleanup(self, text: str) -> str:
        """Final text cleanup"""
        # Remove extra whitespace again
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove very short words (optional)
        words = text.split()
        words = [word for word in words if len(word) > 2]
        text = ' '.join(words)
        
        return text
```

## Example Implementation

### Robust PDF Text Extraction Pipeline

```python
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

# Core libraries
import fitz  # PyMuPDF
import pdfplumber
import PyPDF2

# OCR libraries
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("OCR libraries not available. Install pytesseract and pdf2image for OCR support.")

# Text processing
import re
import unicodedata

class ExtractionMethod(Enum):
    """Available extraction methods"""
    PYMUPDF = "pymupdf"
    PDFPLUMBER = "pdfplumber"
    PYPDF2 = "pypdf2"
    OCR = "ocr"

@dataclass
class ExtractionResult:
    """Result of PDF text extraction"""
    text: str
    method_used: ExtractionMethod
    success: bool
    error_message: Optional[str] = None
    metadata: Dict = None
    page_count: int = 0
    processing_time: float = 0.0

class RobustPDFExtractor:
    """
    Robust PDF text extraction with multiple fallback methods and comprehensive error handling.
    
    Tries multiple extraction methods in order:
    1. PyMuPDF (fastest, good for most PDFs)
    2. pdfplumber (better for complex layouts)
    3. PyPDF2 (fallback for simple PDFs)
    4. OCR (for scanned documents)
    """
    
    def __init__(self, 
                 ocr_enabled: bool = True,
                 ocr_language: str = 'eng',
                 max_file_size_mb: int = 100,
                 timeout_seconds: int = 300):
        """
        Initialize the PDF extractor.
        
        Args:
            ocr_enabled: Whether to use OCR as fallback
            ocr_language: Language for OCR (default: English)
            max_file_size_mb: Maximum file size to process
            timeout_seconds: Timeout for processing
        """
        self.ocr_enabled = ocr_enabled and OCR_AVAILABLE
        self.ocr_language = ocr_language
        self.max_file_size_mb = max_file_size_mb
        self.timeout_seconds = timeout_seconds
        
        # Initialize text cleaner
        self.text_cleaner = PDFTextCleaner(
            remove_numbers=False,  # Keep numbers for most use cases
            remove_punctuation=False,
            remove_stopwords=False,
            lemmatize=False
        )
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def extract_text(self, pdf_path: Union[str, Path], 
                    preferred_method: Optional[ExtractionMethod] = None,
                    clean_text: bool = True,
                    page_range: Optional[Tuple[int, int]] = None) -> ExtractionResult:
        """
        Extract text from PDF using the most appropriate method.
        
        Args:
            pdf_path: Path to the PDF file
            preferred_method: Preferred extraction method (will try this first)
            clean_text: Whether to apply text cleaning
            page_range: Tuple of (start_page, end_page) to extract (1-indexed)
            
        Returns:
            ExtractionResult with extracted text and metadata
        """
        import time
        start_time = time.time()
        
        pdf_path = Path(pdf_path)
        
        # Validate file
        validation_result = self._validate_file(pdf_path)
        if not validation_result[0]:
            return ExtractionResult(
                text="",
                method_used=ExtractionMethod.PYMUPDF,
                success=False,
                error_message=validation_result[1],
                processing_time=time.time() - start_time
            )
        
        # Determine extraction methods to try
        methods = self._get_extraction_methods(preferred_method)
        
        # Try each method until one succeeds
        for method in methods:
            try:
                self.logger.info(f"Attempting extraction with {method.value}")
                
                if method == ExtractionMethod.PYMUPDF:
                    result = self._extract_with_pymupdf(pdf_path, page_range)
                elif method == ExtractionMethod.PDFPLUMBER:
                    result = self._extract_with_pdfplumber(pdf_path, page_range)
                elif method == ExtractionMethod.PYPDF2:
                    result = self._extract_with_pypdf2(pdf_path, page_range)
                elif method == ExtractionMethod.OCR:
                    result = self._extract_with_ocr(pdf_path, page_range)
                else:
                    continue
                
                # Check if extraction was successful
                if result.success and result.text.strip():
                    # Apply text cleaning if requested
                    if clean_text:
                        result.text = self.text_cleaner.clean_text(result.text)
                    
                    result.processing_time = time.time() - start_time
                    self.logger.info(f"Successfully extracted text using {method.value}")
                    return result
                
            except Exception as e:
                self.logger.warning(f"Method {method.value} failed: {str(e)}")
                continue
        
        # All methods failed
        return ExtractionResult(
            text="",
            method_used=ExtractionMethod.PYMUPDF,
            success=False,
            error_message="All extraction methods failed",
            processing_time=time.time() - start_time
        )
    
    def _validate_file(self, pdf_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate PDF file before processing"""
        if not pdf_path.exists():
            return False, f"File does not exist: {pdf_path}"
        
        if not pdf_path.is_file():
            return False, f"Path is not a file: {pdf_path}"
        
        # Check file size
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            return False, f"File too large: {file_size_mb:.1f}MB > {self.max_file_size_mb}MB"
        
        # Check if it's a PDF file
        if pdf_path.suffix.lower() != '.pdf':
            return False, f"Not a PDF file: {pdf_path}"
        
        return True, None
    
    def _get_extraction_methods(self, preferred: Optional[ExtractionMethod]) -> List[ExtractionMethod]:
        """Get ordered list of extraction methods to try"""
        all_methods = [
            ExtractionMethod.PYMUPDF,
            ExtractionMethod.PDFPLUMBER,
            ExtractionMethod.PYPDF2
        ]
        
        if self.ocr_enabled:
            all_methods.append(ExtractionMethod.OCR)
        
        # If preferred method specified, try it first
        if preferred and preferred in all_methods:
            methods = [preferred]
            methods.extend([m for m in all_methods if m != preferred])
            return methods
        
        return all_methods
    
    def _extract_with_pymupdf(self, pdf_path: Path, page_range: Optional[Tuple[int, int]] = None) -> ExtractionResult:
        """Extract text using PyMuPDF"""
        try:
            doc = fitz.open(str(pdf_path))
            
            # Determine page range
            start_page = 0
            end_page = len(doc)
            
            if page_range:
                start_page = max(0, page_range[0] - 1)  # Convert to 0-indexed
                end_page = min(len(doc), page_range[1])
            
            text_parts = []
            
            for page_num in range(start_page, end_page):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                
                if page_text.strip():
                    text_parts.append(page_text)
            
            # Get metadata
            metadata = {
                'total_pages': len(doc),
                'extracted_pages': end_page - start_page,
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'creator': doc.metadata.get('creator', ''),
                'producer': doc.metadata.get('producer', ''),
            }
            
            doc.close()
            
            full_text = '\n'.join(text_parts)
            
            return ExtractionResult(
                text=full_text,
                method_used=ExtractionMethod.PYMUPDF,
                success=True,
                metadata=metadata,
                page_count=end_page - start_page
            )
            
        except Exception as e:
            return ExtractionResult(
                text="",
                method_used=ExtractionMethod.PYMUPDF,
                success=False,
                error_message=str(e)
            )
    
    def _extract_with_pdfplumber(self, pdf_path: Path, page_range: Optional[Tuple[int, int]] = None) -> ExtractionResult:
        """Extract text using pdfplumber"""
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                
                # Determine page range
                start_page = 0
                end_page = len(pdf.pages)
                
                if page_range:
                    start_page = max(0, page_range[0] - 1)  # Convert to 0-indexed
                    end_page = min(len(pdf.pages), page_range[1])
                
                text_parts = []
                
                for page_num in range(start_page, end_page):
                    page = pdf.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_parts.append(page_text)
                
                # Get metadata
                metadata = {
                    'total_pages': len(pdf.pages),
                    'extracted_pages': end_page - start_page,
                    'metadata': pdf.metadata or {}
                }
                
                full_text = '\n'.join(text_parts)
                
                return ExtractionResult(
                    text=full_text,
                    method_used=ExtractionMethod.PDFPLUMBER,
                    success=True,
                    metadata=metadata,
                    page_count=end_page - start_page
                )
                
        except Exception as e:
            return ExtractionResult(
                text="",
                method_used=ExtractionMethod.PDFPLUMBER,
                success=False,
                error_message=str(e)
            )
    
    def _extract_with_pypdf2(self, pdf_path: Path, page_range: Optional[Tuple[int, int]] = None) -> ExtractionResult:
        """Extract text using PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Determine page range
                start_page = 0
                end_page = len(reader.pages)
                
                if page_range:
                    start_page = max(0, page_range[0] - 1)  # Convert to 0-indexed
                    end_page = min(len(reader.pages), page_range[1])
                
                text_parts = []
                
                for page_num in range(start_page, end_page):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text.strip():
                        text_parts.append(page_text)
                
                # Get metadata
                metadata = {
                    'total_pages': len(reader.pages),
                    'extracted_pages': end_page - start_page,
                }
                
                # Try to get document info
                try:
                    if reader.metadata:
                        metadata.update({
                            'title': reader.metadata.get('/Title', ''),
                            'author': reader.metadata.get('/Author', ''),
                            'creator': reader.metadata.get('/Creator', ''),
                            'producer': reader.metadata.get('/Producer', ''),
                        })
                except:
                    pass
                
                full_text = '\n'.join(text_parts)
                
                return ExtractionResult(
                    text=full_text,
                    method_used=ExtractionMethod.PYPDF2,
                    success=True,
                    metadata=metadata,
                    page_count=end_page - start_page
                )
                
        except Exception as e:
            return ExtractionResult(
                text="",
                method_used=ExtractionMethod.PYPDF2,
                success=False,
                error_message=str(e)
            )
    
    def _extract_with_ocr(self, pdf_path: Path, page_range: Optional[Tuple[int, int]] = None) -> ExtractionResult:
        """Extract text using OCR"""
        if not OCR_AVAILABLE:
            return ExtractionResult(
                text="",
                method_used=ExtractionMethod.OCR,
                success=False,
                error_message="OCR libraries not available"
            )
        
        try:
            # Convert PDF to images
            images = convert_from_path(str(pdf_path))
            
            # Determine page range
            start_page = 0
            end_page = len(images)
            
            if page_range:
                start_page = max(0, page_range[0] - 1)  # Convert to 0-indexed
                end_page = min(len(images), page_range[1])
            
            text_parts = []
            
            for page_num in range(start_page, end_page):
                image = images[page_num]
                
                # Preprocess image for better OCR
                image = self._preprocess_image_for_ocr(image)
                
                # Extract text
                page_text = pytesseract.image_to_string(
                    image,
                    lang=self.ocr_language,
                    config='--psm 6'  # Assume uniform block of text
                )
                
                if page_text.strip():
                    text_parts.append(page_text)
            
            metadata = {
                'total_pages': len(images),
                'extracted_pages': end_page - start_page,
                'ocr_language': self.ocr_language
            }
            
            full_text = '\n'.join(text_parts)
            
            return ExtractionResult(
                text=full_text,
                method_used=ExtractionMethod.OCR,
                success=True,
                metadata=metadata,
                page_count=end_page - start_page
            )
            
        except Exception as e:
            return ExtractionResult(
                text="",
                method_used=ExtractionMethod.OCR,
                success=False,
                error_message=str(e)
            )
    
    def _preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # You can add more preprocessing steps here:
        # - Deskewing
        # - Noise reduction
        # - Contrast enhancement
        # - Binarization
        
        return image
    
    def extract_text_from_directory(self, 
                                  directory_path: Union[str, Path],
                                  pattern: str = "*.pdf",
                                  **kwargs) -> Dict[str, ExtractionResult]:
        """
        Extract text from all PDF files in a directory.
        
        Args:
            directory_path: Path to directory containing PDFs
            pattern: File pattern to match (default: "*.pdf")
            **kwargs: Additional arguments passed to extract_text()
            
        Returns:
            Dictionary mapping file paths to extraction results
        """
        directory_path = Path(directory_path)
        results = {}
        
        if not directory_path.is_dir():
            self.logger.error(f"Directory does not exist: {directory_path}")
            return results
        
        pdf_files = list(directory_path.glob(pattern))
        
        for pdf_file in pdf_files:
            self.logger.info(f"Processing {pdf_file.name}")
            
            try:
                result = self.extract_text(pdf_file, **kwargs)
                results[str(pdf_file)] = result
                
                if result.success:
                    self.logger.info(f"✓ {pdf_file.name}: {len(result.text)} characters extracted")
                else:
                    self.logger.warning(f"✗ {pdf_file.name}: {result.error_message}")
                    
            except Exception as e:
                self.logger.error(f"✗ {pdf_file.name}: Unexpected error: {str(e)}")
                results[str(pdf_file)] = ExtractionResult(
                    text="",
                    method_used=ExtractionMethod.PYMUPDF,
                    success=False,
                    error_message=str(e)
                )
        
        return results

# Usage Example
def main():
    """Example usage of the robust PDF extractor"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize extractor
    extractor = RobustPDFExtractor(
        ocr_enabled=True,
        ocr_language='eng',
        max_file_size_mb=50
    )
    
    # Extract text from a single PDF
    pdf_path = "example.pdf"
    
    if Path(pdf_path).exists():
        result = extractor.extract_text(
            pdf_path,
            clean_text=True,
            page_range=(1, 10)  # Extract first 10 pages
        )
        
        if result.success:
            print(f"Extraction successful using {result.method_used.value}")
            print(f"Pages processed: {result.page_count}")
            print(f"Processing time: {result.processing_time:.2f}s")
            print(f"Text length: {len(result.text)} characters")
            print(f"Preview: {result.text[:200]}...")
        else:
            print(f"Extraction failed: {result.error_message}")
    
    # Extract from directory
    directory_results = extractor.extract_text_from_directory(
        "pdf_documents/",
        pattern="*.pdf",
        clean_text=True
    )
    
    # Summary
    successful = sum(1 for r in directory_results.values() if r.success)
    total = len(directory_results)
    print(f"\nDirectory processing complete: {successful}/{total} files processed successfully")

if __name__ == "__main__":
    main()
```

### Usage Examples

#### Basic Text Extraction:
```python
# Simple extraction
extractor = RobustPDFExtractor()
result = extractor.extract_text("document.pdf")

if result.success:
    print(f"Extracted {len(result.text)} characters using {result.method_used.value}")
    print(result.text[:500])  # First 500 characters
```

#### Advanced Configuration:
```python
# Advanced configuration with OCR
extractor = RobustPDFExtractor(
    ocr_enabled=True,
    ocr_language='eng+spa',  # English and Spanish
    max_file_size_mb=100,
    timeout_seconds=600
)

# Extract with custom cleaning
result = extractor.extract_text(
    "complex_document.pdf",
    preferred_method=ExtractionMethod.PDFPLUMBER,
    clean_text=True,
    page_range=(5, 15)  # Pages 5-15 only
)
```

#### Batch Processing:
```python
# Process multiple PDFs
extractor = RobustPDFExtractor()
results = extractor.extract_text_from_directory(
    "documents/",
    pattern="*.pdf",
    clean_text=True
)

# Generate summary report
for file_path, result in results.items():
    filename = Path(file_path).name
    if result.success:
        print(f"✓ {filename}: {len(result.text)} chars ({result.method_used.value})")
    else:
        print(f"✗ {filename}: {result.error_message}")
```

This comprehensive guide provides a robust foundation for PDF text extraction in 2025, incorporating the latest best practices, performance optimizations, and error handling strategies suitable for production environments and LLM preprocessing pipelines.