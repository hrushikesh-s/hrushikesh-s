#!/usr/bin/env python3
"""Update the GitLab merge requests table in README.md from the public GitLab API."""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECTS = ["cplin/pheasy"]
AUTHOR = "hpsahasrabuddhe"
README_PATH = Path(__file__).resolve().parents[1] / "README.md"
START_MARKER = "<!-- GITLAB-MRS:START -->"
END_MARKER = "<!-- GITLAB-MRS:END -->"


def fetch_mrs(project: str) -> list[dict]:
    encoded = urllib.parse.quote(project, safe="")
    params = urllib.parse.urlencode(
        {
            "author_username": AUTHOR,
            "state": "all",
            "per_page": 100,
            "order_by": "updated_at",
            "sort": "desc",
        }
    )
    url = f"https://gitlab.com/api/v4/projects/{encoded}/merge_requests?{params}"
    headers = {"User-Agent": "hrushikesh-s-profile-readme"}
    token = os.environ.get("GITLAB_TOKEN", "").strip()
    if token:
        headers["PRIVATE-TOKEN"] = token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def format_status(mr: dict) -> str:
    state = mr.get("state", "")
    if state == "merged":
        merged_at = mr.get("merged_at") or mr.get("updated_at") or ""
        if merged_at:
            dt = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
            return f"merged {dt.strftime('%b %Y')}"
        return "merged"
    if mr.get("draft"):
        return "draft"
    return "in review"


def build_table(mrs: list[dict]) -> str:
    visible = [m for m in mrs if m.get("state") in ("merged", "opened")]
    visible.sort(
        key=lambda m: (
            0 if m.get("state") == "merged" else 1,
            -(m.get("iid") or 0),
        )
    )
    lines = ["| Merge request | Status |", "|---|---|"]
    for mr in visible:
        title = (mr.get("title") or "").replace("|", r"\|").strip()
        iid = mr.get("iid")
        url = mr.get("web_url")
        status = format_status(mr)
        lines.append(f"| [{title} (`!{iid}`)]({url}) | {status} |")
    return "\n".join(lines)


def main() -> int:
    all_mrs: list[dict] = []
    for project in PROJECTS:
        all_mrs.extend(fetch_mrs(project))

    table = build_table(all_mrs)
    readme = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        re.DOTALL,
    )
    if not pattern.search(readme):
        raise SystemExit(
            f"Markers {START_MARKER} .. {END_MARKER} not found in {README_PATH}"
        )

    updated = pattern.sub(f"{START_MARKER}\n{table}\n{END_MARKER}", readme, count=1)
    if updated != readme:
        README_PATH.write_text(updated, encoding="utf-8")
        print("README.md updated.")
    else:
        print("README.md already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
