"""Write stats.svg and ecosystem.svg from live GitHub and GitLab API data.

Counts merged and open pull requests of USER in repositories owned by others
on GitHub, plus merge requests of GITLAB_USER in GITLAB_PROJECTS on GitLab.
Run by .github/workflows/stats.yml.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime
from html import escape

USER = "hrushikesh-s"
GITLAB_USER = "hpsahasrabuddhe"
GITLAB_PROJECTS = ["cplin/pheasy"]
MAX_BARS = 6
START_YEAR = 2023

SHARED_STYLE = (
    "<style>"
    ":root{--bg:#f6f8fa;--page:#ffffff;--line:#d0d7de;--ink:#1f2328;--muted:#59636e;"
    "--bar:#0f8a7e;--accent2:#0969da;--track:#e6ebf0}"
    "@media (prefers-color-scheme:dark){:root{--bg:#161b22;--page:#0d1117;"
    "--line:#30363d;--ink:#e6edf3;--muted:#9198a1;--bar:#2bc4b0;"
    "--accent2:#58a6ff;--track:#21262d}}"
    "text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,"
    "Arial,sans-serif}"
    ".big{font-size:38px;font-weight:600;fill:var(--ink)}"
    ".label{font-size:13px;fill:var(--muted)}"
    ".head{font-size:11px;font-weight:600;fill:var(--muted);letter-spacing:.08em}"
    ".repo{font-size:12.5px;fill:var(--ink)}"
    ".num{font-size:12.5px;font-weight:600;fill:var(--ink)}"
    "</style>"
)


def github_search(query: str) -> list[dict]:
    """Return all pull requests matching a GitHub search query."""
    items, page = [], 1
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    while True:
        url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
            {"q": query, "per_page": 100, "page": page}
        )
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
        items += data["items"]
        if len(items) >= data["total_count"] or not data["items"]:
            return items
        page += 1


def parse_quarter(iso_ts: str | None) -> tuple[int, int] | None:
    if not iso_ts:
        return None
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    return (dt.year, (dt.month - 1) // 3 + 1)


def collect_github() -> tuple[Counter, Counter, Counter]:
    """Return (merged_by_repo, open_by_repo, merged_by_quarter) for GitHub."""
    merged_by_repo: Counter = Counter()
    open_by_repo: Counter = Counter()
    quarters: Counter = Counter()

    for item in github_search(f"author:{USER} type:pr is:merged"):
        repo = item["repository_url"].split("/repos/")[1]
        if repo.startswith(f"{USER}/"):
            continue
        merged_by_repo[repo] += 1
        ts = (
            (item.get("pull_request") or {}).get("merged_at")
            or item.get("closed_at")
            or item.get("updated_at")
        )
        q = parse_quarter(ts)
        if q:
            quarters[q] += 1

    for item in github_search(f"author:{USER} type:pr is:open"):
        repo = item["repository_url"].split("/repos/")[1]
        if repo.startswith(f"{USER}/"):
            continue
        open_by_repo[repo] += 1

    return merged_by_repo, open_by_repo, quarters


def collect_gitlab() -> tuple[Counter, Counter, Counter]:
    """Return (merged_by_repo, open_by_repo, merged_by_quarter) for GitLab."""
    merged_by_repo: Counter = Counter()
    open_by_repo: Counter = Counter()
    quarters: Counter = Counter()

    headers = {"User-Agent": f"{USER}-profile-readme"}
    token = os.environ.get("GITLAB_TOKEN", "").strip()
    if token:
        headers["PRIVATE-TOKEN"] = token

    for project in GITLAB_PROJECTS:
        encoded = urllib.parse.quote(project, safe="")
        params = urllib.parse.urlencode(
            {"author_username": GITLAB_USER, "state": "all", "per_page": 100}
        )
        url = f"https://gitlab.com/api/v4/projects/{encoded}/merge_requests?{params}"
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=headers), timeout=30
        ) as response:
            mrs = json.load(response)
        for mr in mrs:
            state = mr.get("state")
            if state == "merged":
                merged_by_repo[project] += 1
                q = parse_quarter(mr.get("merged_at") or mr.get("updated_at"))
                if q:
                    quarters[q] += 1
            elif state == "opened":
                open_by_repo[project] += 1

    return merged_by_repo, open_by_repo, quarters


def build_stats_svg(
    merged: Counter, n_open: int, quarters: Counter, gitlab_repos: set[str]
) -> str:
    """Build Option A: KPIs + repo bar chart + quarterly merge cadence."""
    width, height = 860, 326
    tiles = [
        (sum(merged.values()), "merged PRs & MRs"),
        (len(merged), "external repositories"),
        (n_open, "in review"),
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Open-source contributions across GitHub and GitLab">',
        SHARED_STYLE,
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" '
        'fill="var(--bg)" stroke="var(--line)"/>',
        '<text class="head" x="28" y="38">OPEN-SOURCE CONTRIBUTIONS</text>',
    ]
    for idx, (value, label) in enumerate(tiles):
        y = 88 + idx * 48
        parts.append(f'<text class="big" x="28" y="{y}">{value}</text>')
        parts.append(f'<text class="label" x="98" y="{y - 6}">{escape(label)}</text>')

    parts.append('<line x1="296" y1="26" x2="296" y2="210" stroke="var(--line)"/>')
    parts.append(
        '<text class="head" x="324" y="38">MERGED PER REPOSITORY (GITHUB + GITLAB)</text>'
    )

    rows = merged.most_common(MAX_BARS)
    top = rows[0][1] if rows else 1
    bar_x, bar_w = 572, 222
    for idx, (repo, count) in enumerate(rows):
        y = 70 + idx * 25
        length = max(10.0, bar_w * count / top)
        is_gl = repo in gitlab_repos
        display = f"{repo} (GitLab)" if is_gl else repo
        fill = "var(--accent2)" if is_gl else "var(--bar)"
        parts += [
            f'<text class="repo" x="324" y="{y}">{escape(display)}</text>',
            f'<rect x="{bar_x}" y="{y - 10}" width="{bar_w}" height="9" rx="4.5" '
            'fill="var(--track)"/>',
            f'<rect x="{bar_x}" y="{y - 10}" width="{length:.1f}" height="9" rx="4.5" '
            f'fill="{fill}"/>',
            f'<text class="num" x="{bar_x + bar_w + 12}" y="{y}">{count}</text>',
        ]

    # Bottom section: quarterly cadence
    today = date.today()
    end_year = max(today.year, max((y for y, _ in quarters), default=today.year))
    start_year = min(START_YEAR, min((y for y, _ in quarters), default=START_YEAR))
    q_keys = [(y, q) for y in range(start_year, end_year + 1) for q in (1, 2, 3, 4)]
    max_q = max((quarters[k] for k in q_keys), default=1) or 1

    parts.append('<line x1="28" y1="224" x2="832" y2="224" stroke="var(--line)"/>')
    parts.append(
        f'<text class="head" x="28" y="246">'
        f"MERGED PR/MR CADENCE BY QUARTER ({start_year} to {end_year})</text>"
    )

    plot_x, plot_y, plot_w, plot_h = 28, 256, 804, 38
    n_bars = len(q_keys)
    gap = 8
    bw = (plot_w - gap * (n_bars - 1)) / n_bars

    for idx, (yr, q) in enumerate(q_keys):
        cnt = quarters[(yr, q)]
        bx = plot_x + idx * (bw + gap)
        if cnt == 0:
            bh = 3.0
            by = plot_y + plot_h - bh
            fill = "var(--track)"
            opacity = "1"
        else:
            bh = max(5.0, plot_h * cnt / max_q)
            by = plot_y + plot_h - bh
            fill = "var(--bar)"
            opacity = f"{0.45 + 0.55 * (cnt / max_q):.2f}"
        parts.append(
            f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
            f'rx="2" fill="{fill}" opacity="{opacity}">'
            f"<title>{yr} Q{q}: {cnt} merged</title></rect>"
        )
        if q == 1:
            parts.append(
                f'<text x="{bx:.1f}" y="{plot_y + plot_h + 15}" '
                f'fill="var(--muted)" font-size="10.5">{yr}</text>'
            )

    parts.append(
        f'<text x="{width - 28}" y="{plot_y + plot_h + 15}" fill="var(--muted)" '
        f'font-size="10.5" text-anchor="end">updated {today}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def build_ecosystem_svg(merged: Counter, open_by_repo: Counter) -> str:
    """Build Option C: 4-column software stack flow with live PR/MR counts."""
    width, height = 860, 214
    pheasy_m = merged.get("cplin/pheasy", 0)
    pheasy_o = open_by_repo.get("cplin/pheasy", 0)
    a2_m = merged.get("materialsproject/atomate2", 0)
    a2_o = open_by_repo.get("materialsproject/atomate2", 0)
    rc_m = merged.get("hackingmaterials/robocrystallographer", 0)
    mb_m = merged.get("materialsproject/matbench", 0)
    al_m = merged.get("CederGroupHub/alabos", 0)
    em_m = merged.get("materialsproject/emmet", 0)
    pmg_m = merged.get("materialsproject/pymatgen", 0) + merged.get(
        "materialsproject/pymatgen-core", 0
    )
    jf_m = merged.get("materialsproject/jobflow", 0) + merged.get(
        "materialsproject/fireworks", 0
    )

    pheasy_sub = (
        f"{pheasy_m} merged · {pheasy_o} in review"
        if pheasy_o
        else f"{pheasy_m} merged MRs"
    )
    a2_sub = (
        f"{a2_m} merged · {a2_o} in review" if a2_o else f"{a2_m} merged PRs"
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Open-source software ecosystem and live contributions">',
        SHARED_STYLE,
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" '
        'fill="var(--bg)" stroke="var(--line)"/>',
        '<text class="head" x="28" y="34">SOFTWARE ECOSYSTEM &amp; LIVE CONTRIBUTIONS</text>',
        # Col 1: Physics & MLIPs
        '<g transform="translate(28, 52)">',
        '<rect x="0" y="0" width="184" height="134" rx="8" fill="var(--page)" stroke="var(--line)"/>',
        '<text x="14" y="24" fill="var(--muted)" font-size="10.5" font-weight="600" letter-spacing="0.6">PHYSICS &amp; MLIPS</text>',
        '<text x="14" y="50" fill="var(--ink)" font-size="13" font-weight="600">Pheasy (GitLab)</text>',
        f'<text x="14" y="67" fill="var(--accent2)" font-size="11">{escape(pheasy_sub)}</text>',
        '<line x1="14" y1="80" x2="170" y2="80" stroke="var(--line)"/>',
        '<text x="14" y="101" fill="var(--ink)" font-size="12.5">MACE-OMAT / Field</text>',
        '<text x="14" y="118" fill="var(--muted)" font-size="11">Polar RASR · LASSO IFCs</text>',
        "</g>",
        # Arrow 1
        '<path d="M 218 119 L 238 119 M 233 114 L 239 119 L 233 124" '
        'fill="none" stroke="var(--muted)" stroke-width="1.5" stroke-linecap="round"/>',
        # Col 2: Workflows
        '<g transform="translate(244, 52)">',
        '<rect x="0" y="0" width="184" height="134" rx="8" fill="var(--page)" stroke="var(--bar)" stroke-width="1.5"/>',
        '<text x="14" y="24" fill="var(--bar)" font-size="10.5" font-weight="600" letter-spacing="0.6">WORKFLOWS</text>',
        '<text x="14" y="50" fill="var(--ink)" font-size="13" font-weight="600">atomate2</text>',
        f'<text x="14" y="67" fill="var(--bar)" font-size="11">{escape(a2_sub)}</text>',
        '<line x1="14" y1="80" x2="170" y2="80" stroke="var(--line)"/>',
        '<text x="14" y="101" fill="var(--ink)" font-size="12">Phonons · CTE · DWF</text>',
        '<text x="14" y="118" fill="var(--muted)" font-size="11">Finite-T · CALPHAD</text>',
        "</g>",
        # Arrow 2
        '<path d="M 434 119 L 454 119 M 449 114 L 455 119 L 449 124" '
        'fill="none" stroke="var(--muted)" stroke-width="1.5" stroke-linecap="round"/>',
        # Col 3: Libraries & Schemas
        '<g transform="translate(460, 52)">',
        '<rect x="0" y="0" width="184" height="134" rx="8" fill="var(--page)" stroke="var(--line)"/>',
        '<text x="14" y="24" fill="var(--muted)" font-size="10.5" font-weight="600" letter-spacing="0.6">LIBRARIES &amp; SCHEMAS</text>',
        f'<text x="14" y="50" fill="var(--ink)" font-size="12.5">robocrystallographer <tspan fill="var(--bar)" font-size="11" font-weight="600">{rc_m}</tspan></text>',
        f'<text x="14" y="72" fill="var(--ink)" font-size="12.5">matbench / alabos <tspan fill="var(--bar)" font-size="11" font-weight="600">{mb_m} / {al_m}</tspan></text>',
        f'<text x="14" y="94" fill="var(--ink)" font-size="12.5">emmet <tspan fill="var(--bar)" font-size="11" font-weight="600">{em_m}</tspan></text>',
        f'<text x="14" y="116" fill="var(--ink)" font-size="12.5">pymatgen / jobflow <tspan fill="var(--bar)" font-size="11" font-weight="600">{pmg_m} / {jf_m}</tspan></text>',
        "</g>",
        # Arrow 3
        '<path d="M 650 119 L 670 119 M 665 114 L 671 119 L 665 124" '
        'fill="none" stroke="var(--muted)" stroke-width="1.5" stroke-linecap="round"/>',
        # Col 4: Open Data
        '<g transform="translate(676, 52)">',
        '<rect x="0" y="0" width="156" height="134" rx="8" fill="var(--page)" stroke="var(--line)"/>',
        '<text x="14" y="24" fill="var(--muted)" font-size="10.5" font-weight="600" letter-spacing="0.6">OPEN DATA</text>',
        '<text x="14" y="56" fill="var(--ink)" font-size="22" font-weight="600">29,615</text>',
        '<text x="14" y="74" fill="var(--muted)" font-size="11.5">MP phonon crystals</text>',
        '<line x1="14" y1="86" x2="142" y2="86" stroke="var(--line)"/>',
        '<text x="14" y="106" fill="var(--ink)" font-size="11.5">Zenodo v1.2 (124 GB)</text>',
        '<text x="14" y="122" fill="var(--muted)" font-size="10.5">mp-api &amp; MP website</text>',
        "</g>",
        "</svg>",
    ]
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    gh_merged, gh_open, gh_quarters = collect_github()
    gl_merged, gl_open, gl_quarters = collect_gitlab()

    merged = gh_merged + gl_merged
    open_by_repo = gh_open + gl_open
    quarters = gh_quarters + gl_quarters

    with open("stats.svg", "w", encoding="utf-8") as f:
        f.write(build_stats_svg(merged, sum(open_by_repo.values()), quarters, set(GITLAB_PROJECTS)))

    with open("ecosystem.svg", "w", encoding="utf-8") as f:
        f.write(build_ecosystem_svg(merged, open_by_repo))
