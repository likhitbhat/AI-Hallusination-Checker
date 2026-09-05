import re
from urllib.parse import urlparse
from app.config import settings


class SourceReliabilityScorer:
    """Evaluates external source credibility based on domain reputation and top-level domain."""

    MAJOR_ORGS = {
        "un.org", "who.int", "worldbank.org", "imf.org", "oecd.org",
        "europa.eu", "wto.org", "nasa.gov", "unesco.org", "iso.org"
    }

    ENCYCLOPEDIAS = {
        "wikipedia.org", "britannica.com", "investopedia.com", "merriam-webster.com"
    }

    MAJOR_NEWS = {
        "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "nytimes.com",
        "wsj.com", "theguardian.com", "bloomberg.com", "thehindu.com",
        "timesofindia.indiatimes.com", "ft.com", "economist.com", "aljazeera.com"
    }

    ACADEMIC_DOMAINS = {
        "arxiv.org", "ncbi.nlm.nih.gov", "sciencedirect.com", "nature.com",
        "springer.com", "jstor.org", "ieee.org", "biorxiv.org", "cell.com"
    }

    LOW_CREDIBILITY_PATTERNS = [
        r"blogspot\.", r"wordpress\.", r"medium\.com", r"reddit\.com",
        r"quora\.com", r"tumblr\.com", r"pinterest\.com", r"facebook\.com"
    ]

    def extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc
        except Exception:
            return ""

    def score_source(self, url: str) -> float:
        domain = self.extract_domain(url)
        if not domain:
            return settings.RELIABILITY_UNKNOWN

        # 1. Government Domains (.gov, .mil, .gov.in, .gov.uk, etc.)
        if re.search(r"\.(?:gov|mil)(?:\.[a-z]{2})?$", domain) or domain.endswith(".gov"):
            return settings.RELIABILITY_GOVERNMENT

        # 2. Academic (.edu, .ac.uk, .ac.in, etc.)
        if re.search(r"\.(?:edu|ac)(?:\.[a-z]{2})?$", domain) or domain in self.ACADEMIC_DOMAINS:
            return settings.RELIABILITY_ACADEMIC

        # 3. Major International Organizations
        if domain in self.MAJOR_ORGS or domain.endswith(".int"):
            return settings.RELIABILITY_MAJOR_ORG

        # 4. Established Encyclopedias
        if any(domain.endswith(enc) for enc in self.ENCYCLOPEDIAS):
            return settings.RELIABILITY_ENCYCLOPEDIA

        # 5. Established News Outlets
        if any(domain.endswith(news) for news in self.MAJOR_NEWS):
            return settings.RELIABILITY_MAJOR_NEWS

        # 6. Check for user-generated or blogging platforms
        for low in self.LOW_CREDIBILITY_PATTERNS:
            if re.search(low, domain):
                return settings.RELIABILITY_UNKNOWN

        # 7. Standard general website
        return settings.RELIABILITY_GENERAL


source_reliability_scorer = SourceReliabilityScorer()
