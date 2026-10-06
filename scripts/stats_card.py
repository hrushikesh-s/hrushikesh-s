"""Write stats.svg, a card of merged pull requests per repository.

Counts the merged and open pull requests of USER in repositories owned by
others, through the GitHub search API. Run by .github/workflows/stats.yml.
"""

import json
import os
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date
from html import escape

USER = "hrushikesh-s"
MAX_BARS = 6


def search(query: str) -> list[dict]:
    """Return all pull requests that match a search query."""
    items, page = [], 1
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    while True:
        url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
            {"q": query, "per_page": 100, "page": page}
        )
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request) as response:
            data = json.load(response)
        items += data["items"]
        if len(items) >= data["total_count"] or not data["items"]:
            return items
        page += 1


def repo_counts(query: str) -> Counter:
    """Count pull requests per repository, leaving out USER's own repositories."""
    repos = [item["repository_url"].split("/repos/")[1] for item in search(query)]
    return Counter(repo for repo in repos if not repo.startswith(f"{USER}/"))


def card(merged: Counter, n_open: int) -> str:
    """Build the SVG card."""
    width, height = 860, 248
    tiles = [
        (sum(merged.values()), "merged pull requests"),
        (len(merged), "repositories"),
        (n_open, "pull requests in review"),
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Merged pull requests per repository">',
        "<style>"
        ":root{--bg:#f6f8fa;--line:#d0d7de;--ink:#1f2328;--muted:#59636e;"
        "--bar:#0f8a7e;--track:#e6ebf0}"
        "@media (prefers-color-scheme:dark){:root{--bg:#161b22;--line:#30363d;"
        "--ink:#e6edf3;--muted:#9198a1;--bar:#2bc4b0;--track:#21262d}}"
        "text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,"
        "Arial,sans-serif}"
        ".big{font-size:40px;font-weight:600;fill:var(--ink)}"
        ".label{font-size:13px;fill:var(--muted)}"
        ".head{font-size:12px;font-weight:600;fill:var(--muted);letter-spacing:.08em}"
        ".repo{font-size:13px;fill:var(--ink)}"
        ".num{font-size:13px;font-weight:600;fill:var(--ink)}"
        "</style>",
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" '
        'fill="var(--bg)" stroke="var(--line)"/>',
        '<text class="head" x="28" y="40">OPEN-SOURCE CONTRIBUTIONS</text>',
    ]
    for idx, (value, label) in enumerate(tiles):
        y = 92 + idx * 50
        parts.append(f'<text class="big" x="28" y="{y}">{value}</text>')
        parts.append(f'<text class="label" x="96" y="{y - 6}">{escape(label)}</text>')
    parts.append(
        f'<line x1="300" y1="28" x2="300" y2="{height - 28}" stroke="var(--line)"/>'
    )
    parts.append('<text class="head" x="330" y="40">MERGED PER REPOSITORY</text>')
    rows = merged.most_common(MAX_BARS)
    top = rows[0][1] if rows else 1
    bar_x, bar_w = 540, 250
    for idx, (repo, count) in enumerate(rows):
        y = 70 + idx * 26
        length = max(8, bar_w * count / top)
        parts += [
            f'<text class="repo" x="330" y="{y + 4}">{escape(repo)}</text>',
            f'<rect x="{bar_x}" y="{y - 6}" width="{bar_w}" height="10" rx="4" '
            'fill="var(--track)"/>',
            f'<rect x="{bar_x}" y="{y - 6}" width="{length:.1f}" height="10" rx="4" '
            'fill="var(--bar)"/>',
            f'<text class="num" x="{bar_x + bar_w + 12}" y="{y + 4}">{count}</text>',
        ]
    parts.append(
        f'<text class="label" x="{width - 28}" y="{height - 14}" '
        f'text-anchor="end" font-size="11">updated {date.today()}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    merged = repo_counts(f"author:{USER} type:pr is:merged")
    n_open = sum(repo_counts(f"author:{USER} type:pr is:open").values())
    with open("stats.svg", "w") as file:
        file.write(card(merged, n_open))
