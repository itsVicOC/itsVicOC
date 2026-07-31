#!/usr/bin/env python3
"""Generate deterministic, repository-local SVG cards from GitHub public data."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from html import escape
from pathlib import Path


API_ROOT = "https://api.github.com"
CARD_WIDTH = 495
CARD_HEIGHT = 180

LANGUAGE_COLORS = {
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Python": "#3572a5",
    "Swift": "#f05138",
    "Vue": "#41b883",
    "HTML": "#e34c26",
    "CSS": "#663399",
    "Java": "#b07219",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Go": "#00add8",
    "Rust": "#dea584",
    "Shell": "#89e051",
    "Dart": "#00b4ab",
    "Kotlin": "#a97bff",
}

FALLBACK_COLORS = (
    "#70d6c9",
    "#ef8f91",
    "#f4d35e",
    "#8fa8cf",
    "#c792ea",
    "#82aaff",
)


def github_json(path: str, token: str | None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "itsVicOC-profile-stats",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(f"{API_ROOT}{path}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach GitHub API: {exc.reason}") from exc


def fetch_public_repositories(username: str, token: str | None) -> list[dict[str, object]]:
    repositories: list[dict[str, object]] = []
    encoded_username = urllib.parse.quote(username, safe="")

    for page in range(1, 11):
        result = github_json(
            f"/users/{encoded_username}/repos?type=owner&sort=updated&per_page=100&page={page}",
            token,
        )
        if not isinstance(result, list):
            raise RuntimeError("GitHub repositories response was not a list")

        repositories.extend(repo for repo in result if isinstance(repo, dict))
        if len(result) < 100:
            break
    else:
        raise RuntimeError("Repository pagination exceeded the supported limit")

    return repositories


def color_for_language(language: str, index: int) -> str:
    return LANGUAGE_COLORS.get(language, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])


def shorten(value: str, limit: int = 13) -> str:
    return value if len(value) <= limit else f"{value[: limit - 1]}..."


def svg_shell(title: str, corner_label: str, body: str, description: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(title)}</title>
  <desc id="desc">{escape(description)}</desc>
  <defs>
    <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#1a1b27"/>
      <stop offset="1" stop-color="#20333e"/>
    </linearGradient>
    <pattern id="grid" width="22" height="22" patternUnits="userSpaceOnUse">
      <path d="M22 0H0V22" fill="none" stroke="#ffffff" stroke-opacity=".025"/>
    </pattern>
    <clipPath id="bar-clip"><rect x="24" y="67" width="447" height="14" rx="7"/></clipPath>
  </defs>
  <rect x="1" y="1" width="493" height="178" rx="8" fill="url(#panel)" stroke="#3b4057" stroke-width="2"/>
  <rect x="1" y="1" width="493" height="178" rx="8" fill="url(#grid)"/>
  <g font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace">
    <text x="24" y="34" fill="#70d6c9" font-size="15" font-weight="700" letter-spacing="2">{escape(title)}</text>
    <text x="469" y="34" fill="#657089" font-size="12" text-anchor="end">{escape(corner_label)}</text>
    <path d="M24 49H471" stroke="#3b4057"/>
{body}
  </g>
</svg>
'''


def render_player_stats(username: str, public_count: int, original_count: int, language_count: int) -> str:
    body = f'''    <g text-anchor="middle">
      <text x="90" y="100" fill="#f7f7fb" font-size="36" font-weight="800">{public_count}</text>
      <text x="90" y="124" fill="#aab2c8" font-size="11" letter-spacing="1">PUBLIC REPOS</text>
      <text x="248" y="100" fill="#f4d35e" font-size="36" font-weight="800">{original_count}</text>
      <text x="248" y="124" fill="#aab2c8" font-size="11" letter-spacing="1">ORIGINAL BUILDS</text>
      <text x="405" y="100" fill="#ef8f91" font-size="36" font-weight="800">{language_count}</text>
      <text x="405" y="124" fill="#aab2c8" font-size="11" letter-spacing="1">MAIN LANGS</text>
    </g>
    <path d="M169 68V132M326 68V132" stroke="#3b4057"/>
    <text x="24" y="157" fill="#657089" font-size="11">PLAYSTYLE</text>
    <circle cx="94" cy="153" r="4" fill="#70d6c9"/>
    <text x="106" y="157" fill="#c9d1df" font-size="11">curious / practical / playful</text>'''
    description = (
        f"{username} has {public_count} public repositories, {original_count} original builds, "
        f"and {language_count} primary languages"
    )
    return svg_shell("LIVE PLAYER STATS", username, body, description)


def render_languages(language_counts: Counter[str]) -> str:
    top_languages = language_counts.most_common(6)
    total = sum(count for _, count in top_languages)

    if not top_languages:
        body = '''    <text x="247" y="105" text-anchor="middle" fill="#aab2c8" font-size="13">No language data yet</text>
    <text x="24" y="163" fill="#657089" font-size="10">Primary language across original public repositories</text>'''
        return svg_shell("LIVE LOADOUT", "original projects", body, "No language data available")

    bar_parts = ['    <g clip-path="url(#bar-clip)">']
    current_x = 24.0
    bar_width = 447.0
    for index, (language, count) in enumerate(top_languages):
        width = bar_width * count / total
        color = color_for_language(language, index)
        bar_parts.append(
            f'      <rect x="{current_x:.2f}" y="67" width="{width:.2f}" height="14" fill="{color}"/>'
        )
        current_x += width
    bar_parts.append("    </g>")

    legend_parts: list[str] = []
    for index, (language, count) in enumerate(top_languages):
        column = index % 3
        row = index // 3
        x = 24 + column * 155
        y = 107 + row * 31
        color = color_for_language(language, index)
        count_x = x + 118
        legend_parts.extend(
            [
                f'    <circle cx="{x + 6}" cy="{y - 4}" r="5" fill="{color}"/>',
                f'    <text x="{x + 19}" y="{y}" fill="#f7f7fb" font-size="12">{escape(shorten(language))}</text>',
                f'    <text x="{count_x}" y="{y}" fill="#8d96ad" font-size="11">{count}</text>',
            ]
        )

    body = "\n".join(
        bar_parts
        + legend_parts
        + [
            '    <text x="24" y="163" fill="#657089" font-size="10">Primary language across original public repositories</text>'
        ]
    )
    summary = ", ".join(f"{language}: {count}" for language, count in top_languages)
    return svg_shell("LIVE LOADOUT", "original projects", body, summary)


def write_if_changed(path: Path, content: str) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        print(f"unchanged: {path}")
        return
    path.write_text(content, encoding="utf-8")
    print(f"updated: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="itsVicOC")
    parser.add_argument("--output-dir", type=Path, default=Path("assets"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", args.username):
        raise SystemExit("Invalid GitHub username")

    token = os.environ.get("GITHUB_TOKEN")
    repositories = fetch_public_repositories(args.username, token)
    originals = [
        repo
        for repo in repositories
        if not bool(repo.get("fork")) and str(repo.get("name", "")).lower() != args.username.lower()
    ]
    language_counts: Counter[str] = Counter(
        str(repo["language"]) for repo in originals if repo.get("language")
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_if_changed(
        args.output_dir / "player-stats.svg",
        render_player_stats(args.username, len(repositories), len(originals), len(language_counts)),
    )
    write_if_changed(args.output_dir / "main-loadout.svg", render_languages(language_counts))


if __name__ == "__main__":
    main()
