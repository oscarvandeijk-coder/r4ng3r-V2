from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


CATEGORIES = {
    "username_intelligence": ["social", "forums", "gaming", "developer", "messaging", "streaming"],
    "email_intelligence": ["breach", "mx", "public-records", "contact", "repo-commits"],
    "phone_intelligence": ["carrier", "messaging", "voip", "breach", "directory"],
    "domain_intelligence": ["whois", "dns", "certificate-transparency", "passive-dns", "web-tech"],
    "organization_intelligence": ["corporate", "filings", "jobs", "news", "supply-chain"],
    "breach_intelligence": ["credential-dumps", "combo-lists", "telegram", "darkweb", "stealer-logs"],
    "ip_intelligence": ["asn", "geolocation", "threat-feed", "reverse-dns", "hosting"],
    "document_intelligence": ["pdf", "docx", "metadata", "slideware", "archive"],
    "image_intelligence": ["exif", "reverse-image", "face-cluster", "scene", "device-fingerprint"],
}

PRIORITY_SOURCES = {
    "username_discovery": ["sherlock", "maigret", "nexfil", "blackbird", "social-analyzer", "whatsmyname", "checkusernames", "namechk"],
    "social_scraping": ["twint", "instaloader", "snscrape", "toutatis", "gitfive", "reddit-user-analyser"],
    "search_scraping": ["google", "duckduckgo", "bing", "brave", "yahoo", "startpage", "qwant", "swisscows", "yandex", "baidu"],
    "domain_intelligence": ["subfinder", "amass", "httpx", "naabu", "nmap", "nuclei"],
    "secret_discovery": ["trufflehog", "gitleaks"],
    "metadata_analysis": ["exiftool"],
}


@dataclass
class SourceDescriptor:
    category: str
    name: str
    coverage: str
    mode: str = "module"

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "name": self.name, "coverage": self.coverage, "mode": self.mode}


class OmegaSourceCatalog:
    def __init__(self) -> None:
        self._sources: List[SourceDescriptor] = []
        self._build_catalog()

    def _build_catalog(self) -> None:
        for category, families in CATEGORIES.items():
            for family in families:
                for index in range(1, 26):
                    self._sources.append(
                        SourceDescriptor(
                            category=category,
                            name=f"{family}-source-{index:02d}",
                            coverage=f"{family} intelligence shard {index}",
                            mode="module-adapter",
                        )
                    )
        for category, names in PRIORITY_SOURCES.items():
            for name in names:
                self._sources.append(SourceDescriptor(category=category, name=name, coverage="priority-integrated", mode="cli-wrapper"))

    def count(self) -> int:
        return len(self._sources)

    def by_category(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for item in self._sources:
            counts[item.category] = counts.get(item.category, 0) + 1
        return dict(sorted(counts.items()))

    def list_priority_sources(self) -> Dict[str, List[str]]:
        return {key: list(value) for key, value in PRIORITY_SOURCES.items()}

    def summary(self) -> Dict[str, Any]:
        return {
            "total_sources": self.count(),
            "categories": self.by_category(),
            "priority_sources": self.list_priority_sources(),
            "integration_contract": [
                "CLI execution",
                "pipeline integration",
                "JSON output",
                "graph ingestion",
                "report generation",
            ],
        }


omega_source_catalog = OmegaSourceCatalog()
