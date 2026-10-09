"""Fill in the status column of the pull request tables in README.md.

A table row with exactly one pull request link gets its status from the GitHub
API: "merged <month> <year>", "in review", "draft" or "closed". Rows with no
pull request link or with several links are left as they are. Run by
.github/workflows/stats.yml.
"""

import json
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path

PR_LINK = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/pull/(\d+)")


def status(owner: str, repo: str, number: str) -> str:
    """Return the status of one pull request."""
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
        pr = json.load(r)
    if pr["merged_at"]:
        merged = datetime.strptime(pr["merged_at"][:7], "%Y-%m")
        return "merged " + merged.strftime("%b %Y")
    if pr["state"] == "closed":
        return "closed"
    return "draft" if pr["draft"] else "in review"


readme = Path("README.md")
lines = readme.read_text().splitlines()
for i, line in enumerate(lines):
    links = PR_LINK.findall(line)
    if line.startswith("| ") and len(links) == 1:
        cells = line.split(" | ")
        cells[-1] = status(*links[0]) + " |"
        lines[i] = " | ".join(cells)
readme.write_text("\n".join(lines) + "\n")
