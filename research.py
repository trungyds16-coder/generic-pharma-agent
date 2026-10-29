from __future__ import annotations

import ipaddress
import json
import re
import socket
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

MAX_PAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_BYTES = 12 * 1024 * 1024
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def _validate_url(url: str) -> urllib.parse.SplitResult:
    parsed = urllib.parse.urlsplit((url or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Chỉ nhận URL công khai bắt đầu bằng http:// hoặc https://.")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("Không truy cập địa chỉ localhost/mạng nội bộ.")
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            addresses = [
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(
                    host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM
                )
            ]
        except OSError as exc:
            raise ValueError(f"Không phân giải được máy chủ {host}: {exc}") from exc
    if any(not addr.is_global for addr in addresses):
        raise ValueError("URL trỏ tới địa chỉ mạng riêng hoặc đặc biệt; đã chặn để tránh truy cập nhầm máy nội bộ.")
    return parsed


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_SafeRedirect())


def _request(url: str, *, accept: str, timeout: int = 25, data: bytes | None = None):
    _validate_url(url)
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
    }
    request = urllib.request.Request(url, data=data, headers=headers)
    return _OPENER.open(request, timeout=timeout)


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.title = ""
        self._skip = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg", "nav", "footer"):
            self._skip += 1
        if tag == "title":
            self._in_title = True
        if tag in ("p", "div", "br", "li", "h1", "h2", "h3", "tr") and not self._skip:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in ("script", "style", "noscript", "svg", "nav", "footer") and self._skip:
            self._skip -= 1
        if tag in ("p", "div", "li", "h1", "h2", "h3", "tr") and not self._skip:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if not self._skip:
            text = re.sub(r"\s+", " ", data).strip()
            if text:
                self.parts.append(text + " ")


class _SearchParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.results = []
        self._current = None
        self._capture_title = False
        self._capture_snippet = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = a.get("class", "").split()
        if tag == "a" and "result__a" in classes:
            raw_url = a.get("href", "")
            # Clean DDG redirect URL if present
            clean_url = raw_url
            if "uddg=" in raw_url:
                try:
                    parsed = urllib.parse.urlparse(raw_url)
                    params = urllib.parse.parse_qs(parsed.query)
                    clean_url = params.get("uddg", [raw_url])[0]
                except Exception:
                    clean_url = raw_url
            if not clean_url.startswith("https://duckduckgo.com/y.js"):
                self._current = {"url": clean_url, "title": "", "snippet": ""}
                self._capture_title = True
        elif tag in ("a", "div", "td") and any("snippet" in c for c in classes):
            self._capture_snippet = True

    def handle_endtag(self, tag):
        if tag == "a" and self._capture_title:
            self._capture_title = False
            if self._current and self._current.get("url"):
                self.results.append(self._current)
        elif self._capture_snippet and tag in ("a", "div", "td"):
            self._capture_snippet = False

    def handle_data(self, data):
        if self._capture_title and self._current:
            self._current["title"] += data
        elif self._capture_snippet and self.results:
            self.results[-1]["snippet"] += data


def _search_ddg(query: str, limit: int):
    # Strategy 1: DDG HTML via POST
    post_data = urllib.parse.urlencode({"q": query}).encode("utf-8")
    try:
        url = "https://html.duckduckgo.com/html/"
        with _request(url, accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", timeout=15, data=post_data) as response:
            raw = response.read(MAX_PAGE_BYTES).decode("utf-8", errors="replace")
        parser = _SearchParser()
        parser.feed(raw)
        if parser.results:
            return parser.results[:limit]
    except Exception:
        pass

    # Strategy 2: DDG Lite
    try:
        url_lite = "https://lite.duckduckgo.com/lite/"
        with _request(url_lite, accept="text/html", timeout=15, data=post_data) as response:
            raw = response.read(MAX_PAGE_BYTES).decode("utf-8", errors="replace")
        parser = _SearchParser()
        parser.feed(raw)
        if parser.results:
            return parser.results[:limit]
    except Exception:
        pass

    # Strategy 3: DDG HTML via GET fallback
    try:
        url_get = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
        with _request(url_get, accept="text/html", timeout=15) as response:
            raw = response.read(MAX_PAGE_BYTES).decode("utf-8", errors="replace")
        parser = _SearchParser()
        parser.feed(raw)
        return parser.results[:limit]
    except Exception:
        return []


def search_web(query: str, priority_domains: list[str] | None = None, limit: int = 8) -> str:
    if not query.strip():
        return "Hãy nhập nội dung cần tìm."
    outputs = []
    for domain in (priority_domains or [])[:8]:
        host = urllib.parse.urlsplit(domain if "://" in domain else "https://" + domain).hostname or ""
        if host:
            for item in _search_ddg(f"site:{host} {query}", min(3, limit)):
                item["source_type"] = f"Nguồn ưu tiên {host}"
                outputs.append(item)
    for item in _search_ddg(query, limit):
        item["source_type"] = "Tìm kiếm web"
        outputs.append(item)
    unique = []
    seen = set()
    for item in outputs:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(item)
    if not unique:
        return "Không lấy được kết quả tìm kiếm tự động. Có thể website tìm kiếm đang chặn truy cập hoặc máy không có mạng."
    return "\n\n".join(
        f"[{i+1}] {r.get('title','').strip()} ({r.get('source_type','')})\n{r.get('url','')}\n{r.get('snippet','').strip()}"
        for i, r in enumerate(unique[: limit * 2])
    )


def fetch_url(url: str, max_chars: int = 16000) -> str:
    with _request(url, accept="text/html,text/plain,application/pdf;q=0.9,*/*;q=0.5") as response:
        content_type = response.headers.get("Content-Type", "").lower()
        final = response.geturl()
        data = response.read(MAX_PAGE_BYTES + 1)
    if len(data) > MAX_PAGE_BYTES:
        data = data[:MAX_PAGE_BYTES]
    if "pdf" in content_type or final.lower().split("?", 1)[0].endswith(".pdf"):
        try:
            import fitz
            doc = fitz.open(stream=data, filetype="pdf")
            text = "\n\n".join(f"[Trang {i+1}]\n" + page.get_text("text", sort=True) for i, page in enumerate(doc))
        except ImportError:
            return f"URL là PDF nhưng PyMuPDF chưa được cài: {final}"
    elif "html" in content_type or b"<html" in data[:1000].lower():
        parser = _TextParser()
        parser.feed(data.decode("utf-8", errors="replace"))
        text = " ".join(parser.parts)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n", text).strip()
        if parser.title:
            text = f"Tiêu đề: {parser.title.strip()}\nURL: {final}\n\n{text}"
    else:
        text = data.decode("utf-8", errors="replace")
    return f"Nguồn: {final}\n\n{text[:max_chars]}" + ("\n...[đã rút gọn]" if len(text) > max_chars else "")


def download_image(url: str, destination: str) -> str:
    target = Path(destination)
    if target.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        raise ValueError("Ảnh tải về phải có đuôi PNG/JPG/WEBP/GIF.")
    with _request(url, accept="image/png,image/jpeg,image/webp,image/gif", timeout=30) as response:
        mime = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
        if mime not in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
            raise ValueError(f"Nguồn không trả file ảnh được hỗ trợ (Content-Type={mime}).")
        data = response.read(MAX_IMAGE_BYTES + 1)
        source = response.geturl()
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Ảnh vượt giới hạn 12 MB.")
    if not data:
        raise ValueError("Ảnh tải về rỗng.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return f"Đã lưu ảnh {len(data):,} byte: {target}\nNguồn: {source}"


def download_compound_structure(compound: str, destination: str) -> str:
    if not compound.strip():
        raise ValueError("Thiếu tên hoạt chất/CAS/InChIKey.")
    target = Path(destination)
    if target.suffix.lower() not in {".png", ".gif", ".jpg", ".jpeg"}:
        target = target.with_suffix(".png")

    # Strategy 1: PubChem REST API
    encoded = urllib.parse.quote(compound.strip(), safe="")
    cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded}/cids/JSON"
    pubchem_error = None
    try:
        with _request(cid_url, accept="application/json", timeout=20) as response:
            payload = response.read(256_000).decode("utf-8", errors="replace")
        data = json.loads(payload)
        cids = data.get("IdentifierList", {}).get("CID", [])
        if cids:
            cid = int(cids[0])
            img_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG?image_size=500x500"
            result = download_image(img_url, str(target))
            return (
                f"{result}\nPubChem CID: {cid}\nTra cứu đầu vào: {compound}\n"
                f"Hãy đối chiếu tên/CAS/InChIKey trong hồ sơ trước khi dùng.\n"
                f"Hồ sơ: https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
            )
    except Exception as exc:
        pubchem_error = str(exc)

    # Strategy 2: Cactus NCI Chemical Structure Resolver fallback
    try:
        cactus_url = f"https://cactus.nci.nih.gov/chemical/structure/{encoded}/image"
        result = download_image(cactus_url, str(target))
        return (
            f"{result}\nNguồn dự phòng: Cactus NCI Chemical Resolver\n"
            f"Tra cứu đầu vào: {compound}\n"
            f"(Ghi chú: PubChem tạm thời phản hồi lỗi: {pubchem_error})"
        )
    except Exception as cactus_exc:
        raise RuntimeError(
            f"Không tải được cấu trúc phân tử cho '{compound}'. "
            f"PubChem: {pubchem_error}; Cactus NCI: {cactus_exc}"
        ) from cactus_exc
