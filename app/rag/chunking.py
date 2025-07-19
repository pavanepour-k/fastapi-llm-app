"""
Document processing and chunking for RAG
"""

import re
from typing import List, Dict, Any
from pathlib import Path
import fitz  # PyMuPDF for PDF processing


class DocumentProcessor:
    """
    Document processor for extracting and chunking text content.
    
    Single Responsibility: Document text extraction and chunking
    """
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def process_file(self, file_path: Path, filename: str) -> List[Dict[str, Any]]:
        """
        Process uploaded file and return chunks with metadata.
        
        Single Responsibility: File processing coordination
        """
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.pdf':
            return await self._process_pdf(file_path, filename)
        elif file_extension == '.txt':
            return await self._process_text(file_path, filename)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    async def _process_pdf(self, file_path: Path, filename: str) -> List[Dict[str, Any]]:
        """
        Extract and chunk PDF content.
        
        Single Responsibility: PDF text extraction
        """
        chunks = []
        
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():  # Only process pages with text
                    cleaned_text = self._clean_text(text)
                    page_chunks = self._chunk_text(cleaned_text)
                    
                    for i, chunk in enumerate(page_chunks):
                        chunks.append({
                            "content": chunk,
                            "metadata": {
                                "source": filename,
                                "page": page_num + 1,
                                "chunk_index": i,
                                "file_type": "pdf"
                            }
                        })
            
            doc.close()
            
        except Exception as e:
            raise Exception(f"Error processing PDF {filename}: {str(e)}")
        
        return chunks
    
    async def _process_text(self, file_path: Path, filename: str) -> List[Dict[str, Any]]:
        """
        Process plain text file.
        
        Single Responsibility: Text file processing
        """
        chunks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            cleaned_text = self._clean_text(text)
            text_chunks = self._chunk_text(cleaned_text)
            
            for i, chunk in enumerate(text_chunks):
                chunks.append({
                    "content": chunk,
                    "metadata": {
                        "source": filename,
                        "chunk_index": i,
                        "file_type": "txt"
                    }
                })
                
        except Exception as e:
            raise Exception(f"Error processing text file {filename}: {str(e)}")
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Single Responsibility: Text normalization
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)]', '', text)
        
        return text.strip()
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Single Responsibility: Text chunking with overlap
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Find end position
            end = start + self.chunk_size
            
            if end >= len(text):
                # Last chunk
                chunks.append(text[start:])
                break
            
            # Try to break at sentence boundary
            chunk_text = text[start:end]
            last_sentence_end = max(
                chunk_text.rfind('.'),
                chunk_text.rfind('!'),
                chunk_text.rfind('?')
            )
            
            if last_sentence_end > self.chunk_size // 2:
                # Found good break point
                chunks.append(text[start:start + last_sentence_end + 1])
                start = start + last_sentence_end + 1 - self.chunk_overlap
            else:
                # No good break point, use word boundary
                chunk_text = text[start:end]
                last_space = chunk_text.rfind(' ')
                
                if last_space > self.chunk_size // 2:
                    chunks.append(text[start:start + last_space])
                    start = start + last_space + 1 - self.chunk_overlap
                else:
                    # Force split
                    chunks.append(chunk_text)
                    start = end - self.chunk_overlap
        
        return [chunk.strip() for chunk in chunks if chunk.strip()]


# Global document processor instance
document_processor = DocumentProcessor()
