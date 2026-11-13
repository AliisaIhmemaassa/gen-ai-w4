#!/usr/bin/env python3
"""web_search: DuckDuckGo HTML haku curlilla subprocess.run-kutsulla.

Palauta lista sanakirjoja {title, url}.
"""
import re
import subprocess
import sys
from urllib.parse import quote, urlparse, unquote, parse_qs


def web_search(query, max_results=5):
    """Hae DuckDuckGo HTML-haulla ja palauta [{title, url}, ...]."""
    url = "https://html.duckduckgo.com/html/?q=" + quote(query)
    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-L",
                "--max-time", "15",
                "-A", "Mozilla/5.0 (X11; Linux x86_64)",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        html = result.stdout
    except Exception as exc:
        return [{"title": "Haku epäonnistui", "url": "", "error": str(exc)}]

    results = []
    pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        re.DOTALL,
    )
    for match in pattern.finditer(html):
        href = match.group(1)
        title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if href.startswith("//"):
            href = "https:" + href
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            href = unquote(qs["uddg"][0])
        if title and href:
            results.append({"title": title, "url": href})
        if len(results) >= max_results:
            break
    if not results:
        results = [{"title": "Ei tuloksia", "url": ""}]
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Käyttö: python search.py <hakusana> [max_results]")
        sys.exit(1)

    query = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    for item in web_search(query, max_results):
        print(f"- {item['title']}: {item['url']}")
