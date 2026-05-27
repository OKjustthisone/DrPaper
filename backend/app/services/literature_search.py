import concurrent.futures
import re
import socket
import time
import xml.etree.ElementTree as ET
import requests

# Force IPv4 for all requests (IPv6 causes timeouts on these APIs)
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(host, port, family=0, *args, **kwargs):
    return _orig_getaddrinfo(host, port, socket.AF_INET, *args, **kwargs)
socket.getaddrinfo = _ipv4_getaddrinfo

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
OPENALEX_BASE = "https://api.openalex.org"
ARXIV_BASE = "https://export.arxiv.org/api/query"

REQ_TIMEOUT = 30
HEADERS = {"User-Agent": "DrPaper/1.0 (mailto:drpaper@example.com)"}


def search_papers(query: str, sources: list[str], page: int = 1, limit: int = 10) -> dict:
    """Search across selected literature databases in parallel."""
    result = {"results": [], "total": 0, "page": page}
    futures = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        if "pmc" in sources:
            futures["pmc"] = executor.submit(_search_pmc, query, page, limit)
        if "openalex" in sources:
            futures["openalex"] = executor.submit(_search_openalex, query, page, limit)
        if "arxiv" in sources:
            futures["arxiv"] = executor.submit(_search_arxiv, query, page, limit)

        for src, fut in futures.items():
            try:
                out = fut.result(timeout=REQ_TIMEOUT + 10)
                if isinstance(out, dict):
                    result["results"].extend(out.get("results", []))
                    result["total"] += out.get("total", 0)
            except Exception:
                pass

    result["total"] = min(result["total"], 200)
    return result


def fetch_full_text(paper_id: str) -> str:
    """Fetch full text given a paper_id like 'pmid:12345', 'arxiv:2106.xxxx', 'openalex:Wxxx'."""
    if paper_id.startswith("arxiv:"):
        return _fetch_arxiv_fulltext(paper_id.split(":", 1)[1])
    elif paper_id.startswith("pmid:"):
        return _fetch_pmc_fulltext_by_pmid(paper_id.split(":", 1)[1])
    elif paper_id.startswith("pmc:"):
        return _fetch_pmc_fulltext(paper_id.split(":", 1)[1])
    elif paper_id.startswith("openalex:"):
        return _fetch_openalex_fulltext(paper_id.split(":", 1)[1])
    return ""


# ---- PMC / PubMed via Entrez ----

def _search_pmc(query: str, page: int, limit: int) -> dict:
    try:
        # 1. search
        r = requests.get(f"{ENTREZ_BASE}/esearch.fcgi", params={
            "db": "pmc", "term": query, "retstart": (page - 1) * limit,
            "retmax": limit, "retmode": "json", "sort": "relevance",
        }, timeout=REQ_TIMEOUT, headers=HEADERS)
        if r.status_code != 200:
            return {"results": [], "total": 0}
        data = r.json()
        ids = data.get("esearchresult", {}).get("idlist", [])
        total = int(data.get("esearchresult", {}).get("count", 0))
        if not ids:
            return {"results": [], "total": total}

        # 2. fetch summaries
        r2 = requests.get(f"{ENTREZ_BASE}/efetch.fcgi", params={
            "db": "pmc", "id": ",".join(ids), "retmode": "xml", "rettype": "abstract",
        }, timeout=REQ_TIMEOUT, headers=HEADERS)
        results = []
        if r2.status_code == 200:
            results = _parse_pmc_efetch(r2.text, ids)
        return {"results": results, "total": total}
    except Exception:
        return {"results": [], "total": 0}


def _parse_pmc_efetch(xml_text: str, ids: list[str]) -> list[dict]:
    results = []
    try:
        root = ET.fromstring(xml_text)
        for article in root.findall(".//article"):
            pmcid_elem = article.find(".//article-id[@pub-id-type='pmc']")
            pmid_elem = article.find(".//article-id[@pub-id-type='pmid']")
            pmcid = pmcid_elem.text if pmcid_elem is not None else ""
            pmid = pmid_elem.text if pmid_elem is not None else ""
            pid = f"pmid:{pmid}" if pmid else f"pmc:{pmcid}"

            title_elem = article.find(".//article-title")
            title = "".join(title_elem.itertext()).strip() if title_elem is not None else "No title"

            abstract_elems = article.findall(".//abstract//p")
            abstract = " ".join("".join(a.itertext()).strip() for a in abstract_elems)

            authors = []
            for contrib in article.findall(".//contrib[@contrib-type='author']"):
                surname = contrib.findtext(".//surname", "")
                given = contrib.findtext(".//given-names", "")
                if surname:
                    authors.append(f"{given} {surname}".strip())

            pub_date = article.find(".//pub-date")
            year = ""
            if pub_date is not None:
                y = pub_date.findtext("year", "")
                year = y

            journal_elem = article.find(".//journal-title")
            journal = journal_elem.text.strip() if journal_elem is not None and journal_elem.text else ""

            doi = ""
            for aid in article.findall(".//article-id[@pub-id-type='doi']"):
                doi = aid.text or ""
                break

            results.append({
                "id": pid,
                "title": title[:300],
                "authors": ", ".join(authors[:5]),
                "abstract": abstract[:1500],
                "year": year,
                "source": "pmc",
                "url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/" if pmcid else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "full_text_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/?report=classic" if pmcid else "",
                "doi": doi,
                "journal": journal,
            })
    except ET.ParseError:
        pass
    return results


# ---- OpenAlex ----

def _search_openalex(query: str, page: int, limit: int) -> dict:
    try:
        r = requests.get(f"{OPENALEX_BASE}/works", params={
            "search": query, "per_page": limit, "page": page,
        }, timeout=REQ_TIMEOUT, headers=HEADERS)
        if r.status_code != 200:
            return {"results": [], "total": 0}
        data = r.json()
        results = []
        for w in data.get("results", []):
            title = w.get("title", "No title")
            abstract = ""
            if "abstract_inverted_index" in w and w["abstract_inverted_index"]:
                abstract = _unpack_inverted_index(w["abstract_inverted_index"])
            authors = []
            for a in w.get("authorships", []):
                name = a.get("author", {}).get("display_name", "")
                if name:
                    authors.append(name)
            pub_year = str(w.get("publication_year", ""))
            doi = w.get("doi", "") or ""
            oa_url = ""
            oa = w.get("open_access", {})
            if oa.get("is_oa"):
                oa_url = oa.get("oa_url", "")
            results.append({
                "id": f"openalex:{w.get('id','').split('/')[-1]}",
                "title": title[:300],
                "authors": ", ".join(authors[:5]),
                "abstract": abstract[:1500],
                "year": pub_year,
                "source": "openalex",
                "url": doi if doi else w.get("primary_location", {}).get("landing_page_url", ""),
                "full_text_url": oa_url,
                "doi": doi,
                "journal": w.get("primary_location", {}).get("source", {}).get("display_name", ""),
            })
        return {"results": results, "total": min(int(data.get("meta", {}).get("count", 0)), 1000)}
    except Exception:
        return {"results": [], "total": 0}


def _unpack_inverted_index(inv: dict) -> str:
    indexed = {}
    for word, positions in inv.items():
        for pos in positions:
            indexed[pos] = word
    return " ".join(indexed[i] for i in sorted(indexed))


# ---- arXiv ----

def _search_arxiv(query: str, page: int, limit: int) -> dict:
    try:
        # arXiv rate-limits; retry with backoff on 429
        for attempt in range(3):
            r = requests.get(ARXIV_BASE, params={
                "search_query": f"all:{query}",
                "start": (page - 1) * limit,
                "max_results": limit,
                "sortBy": "relevance",
            }, timeout=REQ_TIMEOUT, headers=HEADERS)
            if r.status_code == 429:
                time.sleep(3 * (attempt + 1))
                continue
            break
        if r.status_code != 200:
            return {"results": [], "total": 0}
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        root = ET.fromstring(r.text)
        total = 0
        for e in root.findall("atom:totalResults", ns):
            total = int(e.text or "0")
        results = []
        for entry in root.findall("atom:entry", ns):
            eid = entry.findtext("atom:id", "", ns).strip()
            arxiv_id = eid.split("/abs/")[-1] if "/abs/" in eid else eid
            title = entry.findtext("atom:title", "No title", ns).strip().replace("\n", " ")
            summary = entry.findtext("atom:summary", "", ns).strip().replace("\n", " ")
            authors = [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns)]
            pub_date = entry.findtext("atom:published", "", ns)
            year = pub_date[:4] if pub_date else ""
            doi = ""
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "doi":
                    doi = link.get("href", "")
                    break
            results.append({
                "id": f"arxiv:{arxiv_id}",
                "title": title[:300],
                "authors": ", ".join(authors[:5]),
                "abstract": summary[:1500],
                "year": year,
                "source": "arxiv",
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "full_text_url": f"https://arxiv.org/pdf/{arxiv_id}",
                "doi": doi.replace("http://dx.doi.org/", "").split("https://doi.org/")[-1],
                "journal": "arXiv preprint",
            })
        return {"results": results, "total": min(total, 200)}
    except Exception:
        return {"results": [], "total": 0}


# ---- Full Text Fetch ----

def _fetch_arxiv_fulltext(arxiv_id: str) -> str:
    try:
        r = requests.get(f"https://arxiv.org/abs/{arxiv_id}", timeout=REQ_TIMEOUT)
        if r.status_code == 200:
            text = re.sub(r"<[^>]+>", " ", r.text)
            text = re.sub(r"\s+", " ", text)
            start = text.find("Abstract:")
            if start >= 0:
                return f"arXiv {arxiv_id}\n\n" + text[start:start + 8000]
    except Exception:
        pass
    return f"[arXiv {arxiv_id}] Full text fetch failed. Read at: https://arxiv.org/abs/{arxiv_id}"


def _fetch_pmc_fulltext(pmcid: str) -> str:
    try:
        r = requests.get(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/?report=classic", timeout=REQ_TIMEOUT)
        if r.status_code != 200:
            return f"[PMC {pmcid}] Full text not available."
        text = re.sub(r"<[^>]+>", " ", r.text)
        text = re.sub(r"&[a-z]+;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 50000:
            text = text[:50000] + "...[truncated]"
        return f"PMC {pmcid}\n\n{text}"
    except Exception:
        return f"[PMC {pmcid}] Full text fetch error."


def _fetch_pmc_fulltext_by_pmid(pmid: str) -> str:
    try:
        r = requests.get(f"{ENTREZ_BASE}/elink.fcgi", params={
            "dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "json",
        }, timeout=REQ_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            links = data.get("linksets", [{}])[0].get("linksetdbs", [])
            for link in links:
                if link.get("linkname") == "pmc_pmc":
                    pmc_ids = link.get("links", [])
                    if pmc_ids:
                        return _fetch_pmc_fulltext(pmc_ids[0])
        r2 = requests.get(f"{ENTREZ_BASE}/efetch.fcgi", params={
            "db": "pubmed", "id": pmid, "retmode": "xml", "rettype": "abstract",
        }, timeout=REQ_TIMEOUT)
        if r2.status_code == 200:
            text = re.sub(r"<[^>]+>", " ", r2.text)
            text = re.sub(r"\s+", " ", text).strip()
            return f"PubMed {pmid} (abstract)\n\n{text[:8000]}"
    except Exception:
        pass
    return f"[PubMed {pmid}] Full text not available."


def _fetch_openalex_fulltext(work_id: str) -> str:
    try:
        r = requests.get(f"{OPENALEX_BASE}/works/W{work_id}", timeout=REQ_TIMEOUT)
        if r.status_code != 200:
            return f"[OpenAlex W{work_id}] Full text not available."
        data = r.json()
        abstract = _unpack_inverted_index(data.get("abstract_inverted_index", {}) or {})
        text = f"Title: {data.get('title', '')}\n\nAbstract: {abstract}"
        oa = data.get("open_access", {})
        if oa.get("is_oa") and oa.get("oa_url"):
            text += f"\n\nOpen Access URL: {oa['oa_url']}"
        return text[:8000]
    except Exception:
        return f"[OpenAlex W{work_id}] Full text fetch error."
