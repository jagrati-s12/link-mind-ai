import os
import re
import html
import json
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

async def try_fetch_job_board_api(url: str, client: httpx.AsyncClient) -> Optional[FetchResult]:
    """
    Directly extracts job details for SPAs and job board providers
    (HackerRank, Greenhouse, Lever) that load descriptions asynchronously via JS.
    """
    try:
        # 1. HackerRank Career Page (e.g. hackerrank.com/careers/job?id=8229735)
        hr_match = re.search(r'hackerrank\.com/careers/job\?.*?\bid=(\d+)', url, re.I)
        if hr_match:
            job_id = hr_match.group(1)
            api_url = f"https://boards-api.greenhouse.io/v1/boards/hackerrank/jobs/{job_id}"
            resp = await client.get(api_url)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", "Development Engineer Intern")
                company = "HackerRank"
                loc = data.get("location", {}).get("name", "Onsite in Bangalore")
                departments = ", ".join(d.get("name") for d in data.get("departments", []) if d.get("name"))
                content_html = html.unescape(data.get("content", ""))
                soup = BeautifulSoup(content_html, "html.parser")
                desc_text = soup.get_text(separator="\n", strip=True)

                formatted = (
                    f"{title}\n"
                    f"Company: {company}\n"
                    f"Location: {loc}\n"
                    + (f"Department: {departments}\n" if departments else "")
                    + f"Application URL: {url}\n\n"
                    f"About the Role:\n{desc_text}"
                )
                c_hash = hashlib.sha256(formatted.encode("utf-8")).hexdigest()
                return FetchResult(
                    content=formatted,
                    title=f"{company} - {title}",
                    mime_type="text/html",
                    content_hash=c_hash
                )

        # 2. Greenhouse Board Pages (boards.greenhouse.io/<company>/jobs/<id>)
        gh_match = re.search(r'boards\.greenhouse\.io/([^/]+)/jobs/(\d+)', url, re.I)
        if not gh_match:
            gh_match = re.search(r'boards\.greenhouse\.io/embed/job\.html\?.*?\bfor=([^&]+).*?\btoken=(\d+)', url, re.I)
        if gh_match:
            board, job_id = gh_match.group(1), gh_match.group(2)
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}"
            resp = await client.get(api_url)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", "")
                company = board.capitalize()
                loc = data.get("location", {}).get("name", "")
                content_html = html.unescape(data.get("content", ""))
                soup = BeautifulSoup(content_html, "html.parser")
                desc_text = soup.get_text(separator="\n", strip=True)

                formatted = (
                    f"{title}\n"
                    f"Company: {company}\n"
                    f"Location: {loc}\n"
                    f"Application URL: {url}\n\n"
                    f"{desc_text}"
                )
                c_hash = hashlib.sha256(formatted.encode("utf-8")).hexdigest()
                return FetchResult(
                    content=formatted,
                    title=f"{company} - {title}",
                    mime_type="text/html",
                    content_hash=c_hash
                )

        # 3. Lever Postings (jobs.lever.co/<company>/<id>)
        lever_match = re.search(r'jobs\.lever\.co/([^/]+)/([a-f0-9\-]+)', url, re.I)
        if lever_match:
            company, job_id = lever_match.group(1), lever_match.group(2)
            api_url = f"https://api.lever.co/v0/postings/{company}/{job_id}"
            resp = await client.get(api_url)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("text", "")
                categories = data.get("categories", {})
                loc = categories.get("location", "")
                commitment = categories.get("commitment", "")
                desc_html = html.unescape(data.get("descriptionHtml", "") + "\n" + data.get("additional", ""))
                soup = BeautifulSoup(desc_html, "html.parser")
                desc_text = soup.get_text(separator="\n", strip=True)

                formatted = (
                    f"{title}\n"
                    f"Company: {company.capitalize()}\n"
                    f"Location: {loc}\n"
                    + (f"Type: {commitment}\n" if commitment else "")
                    + f"Application URL: {url}\n\n"
                    f"{desc_text}"
                )
                c_hash = hashlib.sha256(formatted.encode("utf-8")).hexdigest()
                return FetchResult(
                    content=formatted,
                    title=f"{company.capitalize()} - {title}",
                    mime_type="text/html",
                    content_hash=c_hash
                )
    except Exception:
        pass

    return None

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
            # Check if URL matches known job board SPA APIs (HackerRank, Greenhouse, Lever)
            job_board_res = await try_fetch_job_board_api(url, client)
            if job_board_res:
                return job_board_res

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
                
                # Check JSON-LD for rich job postings
                json_ld_text = ""
                for s in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = json.loads(s.string or "")
                        if isinstance(data, dict) and data.get("@type") == "JobPosting":
                            j_title = data.get("title", "")
                            j_org = data.get("hiringOrganization", {}).get("name", "") if isinstance(data.get("hiringOrganization"), dict) else ""
                            j_loc = ""
                            if isinstance(data.get("jobLocation"), dict):
                                addr = data.get("jobLocation", {}).get("address", {})
                                j_loc = addr.get("addressLocality", "") if isinstance(addr, dict) else ""
                            j_desc = BeautifulSoup(html.unescape(data.get("description", "")), "html.parser").get_text(separator="\n", strip=True)
                            json_ld_text = f"{j_title}\nCompany: {j_org}\nLocation: {j_loc}\n\n{j_desc}"
                            break
                    except Exception:
                        pass
                
                # Check OpenGraph / Twitter meta titles if page title is generic or Untitled
                og_title = ""
                og_tag = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
                if og_tag and og_tag.get("content"):
                    og_title = og_tag.get("content").strip()

                h1_tag = soup.find("h1")
                h1_text = h1_tag.get_text().strip() if h1_tag else ""

                # Remove script and style elements
                for script in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
                    script.extract()

                raw_title = soup.title.string.strip() if soup.title and soup.title.string else ""
                
                if raw_title and raw_title.lower() not in ("untitled", "loading...", "job application", "careers"):
                    page_title = raw_title
                elif og_title and og_title.lower() not in ("untitled", "careers"):
                    page_title = og_title
                elif h1_text and len(h1_text) < 100:
                    page_title = h1_text
                else:
                    page_title = raw_title or url

                # Extract main readable text
                text = soup.get_text(separator="\n", strip=True)
                if json_ld_text:
                    text = f"{json_ld_text}\n\n---\n{text}"

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
