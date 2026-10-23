import os
import hashlib
from typing import Tuple, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import docx
from app.core.config import settings
from app.core.ssrf import validate_safe_url

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

class FetchResult:
    def __init__(self, content: str, title: str, mime_type: str, content_hash: str, error: Optional[str] = None):
        self.content = content
        self.title = title
        self.mime_type = mime_type
        self.content_hash = content_hash
        self.error = error

async def fetch_url_content(url: str) -> FetchResult:
    """
    Safely fetches content from a public URL with SSRF protection,
    redirect validation, and size limit checks.
    """
    is_safe, reason = validate_safe_url(url)
    if not is_safe:
        return FetchResult("", "", "", "", error=f"Security rejection: {reason}")

    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
            max_redirects=5
        ) as client:
            response = await client.get(url, headers=headers)
            
            # Recheck final URL destination after redirects for SSRF
            final_url = str(response.url)
            is_dest_safe, dest_reason = validate_safe_url(final_url)
            if not is_dest_safe:
                return FetchResult("", "", "", "", error=f"Security rejection after redirect: {dest_reason}")

            if response.status_code == 403:
                return FetchResult("", "", "", "", error="Access blocked by provider (HTTP 403 Forbidden). Authentication or login required.")
            if response.status_code == 404:
                return FetchResult("", "", "", "", error="Resource not found (HTTP 404).")
            if response.status_code == 429:
                return FetchResult("", "", "", "", error="Rate limited by source provider (HTTP 429). Please try again later.")
            if response.status_code >= 400:
                return FetchResult("", "", "", "", error=f"HTTP request failed with status code {response.status_code}.")

            content_type = response.headers.get("content-type", "").lower()
            raw_bytes = response.content
            
            if len(raw_bytes) > settings.MAX_SCRAPE_BYTES:
                return FetchResult("", "", "", "", error="Page exceeds maximum allowed download size (5MB).")

            content_hash = hashlib.sha256(raw_bytes).hexdigest()

            # HTML extraction
            if "text/html" in content_type or "application/xhtml" in content_type:
                soup = BeautifulSoup(raw_bytes, "html.parser")
                
                # Remove script and style elements
                for script in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
                    script.extract()

                page_title = soup.title.string.strip() if soup.title and soup.title.string else url
                
                # Extract main readable text
                text = soup.get_text(separator="\n", strip=True)
                return FetchResult(content=text, title=page_title, mime_type="text/html", content_hash=content_hash)

            # PDF URL
            elif "application/pdf" in content_type:
                doc = fitz.open(stream=raw_bytes, filetype="pdf")
                text_pages = [page.get_text() for page in doc]
                doc.close()
                extracted_text = "\n\n".join(text_pages).strip()
                title = os.path.basename(url.split("?")[0]) or "PDF Document"
                return FetchResult(content=extracted_text, title=title, mime_type="application/pdf", content_hash=content_hash)

            # Plain text
            else:
                text = response.text
                return FetchResult(content=text, title=url, mime_type="text/plain", content_hash=content_hash)

    except httpx.TimeoutException:
        return FetchResult("", "", "", "", error="Connection timed out while trying to fetch the URL.")
    except httpx.RequestError as e:
        return FetchResult("", "", "", "", error=f"Network error while connecting to source: {str(e)}")
    except Exception as e:
        return FetchResult("", "", "", "", error=f"Extraction failure: {str(e)}")

def extract_document_file(file_path: str, filename: str) -> FetchResult:
    """
    Extracts text from uploaded PDF, DOCX, or text files.
    """
    try:
        ext = os.path.splitext(filename)[1].lower()
        with open(file_path, "rb") as f:
            raw_bytes = f.read()
        content_hash = hashlib.sha256(raw_bytes).hexdigest()

        if ext == ".pdf":
            doc = fitz.open(file_path)
            text_pages = [page.get_text() for page in doc]
            doc.close()
            text = "\n\n".join(text_pages).strip()
            return FetchResult(content=text, title=filename, mime_type="application/pdf", content_hash=content_hash)

        elif ext == ".docx":
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        paragraphs.append(row_text)
            text = "\n".join(paragraphs).strip()
            return FetchResult(content=text, title=filename, mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", content_hash=content_hash)

        elif ext in (".txt", ".md"):
            text = raw_bytes.decode("utf-8", errors="replace").strip()
            return FetchResult(content=text, title=filename, mime_type="text/plain", content_hash=content_hash)

        else:
            return FetchResult("", "", "", "", error=f"Unsupported document format: {ext}")

    except Exception as e:
        return FetchResult("", "", "", "", error=f"Error reading document: {str(e)}")
