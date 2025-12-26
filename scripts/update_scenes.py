"""
Refreshes the four profile-README scene WebPs with live GitHub data.

Static creative choices (headline text, tech stack list, character/layout
per section, skill totals) are NOT derived automatically - they live in the
per-section config below and are meant to be hand-edited when they actually
change. Only the numbers that genuinely drift on their own (repo count,
contribution count, top-stargazer shoutout) are pulled live.

Requires: pillow (pip), a GITHUB_TOKEN with public read access.
Run from the assets/sources -> assets/*.webp direction; never re-touches the
original character footage.
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from compose_scenes import process

TOKEN = os.environ.get("GITHUB_TOKEN", "")
USER = "aks-builds"
BASE = os.path.join(os.path.dirname(__file__), "..", "assets")
SOURCES = os.path.join(BASE, "sources")

AWESOME_LIST_REPOS = [
    "awesome-ai-search-algorithms", "awesome-case-based-reasoning",
    "awesome-fuzzy-logic", "awesome-procedural-reasoning",
    "awesome-deductive-classifiers", "awesome-rule-engines",
    "awesome-owasp-security-testing", "awesome-neet-ug",
    "awesome-upsc-cse", "awesome-istqb",
]


def api(path, is_graphql=False, query=None):
    url = "https://api.github.com/graphql" if is_graphql else f"https://api.github.com{path}"
    headers = {"Authorization": f"Bearer {TOKEN}", "User-Agent": USER}
    if is_graphql:
        req = urllib.request.Request(url, data=json.dumps({"query": query}).encode(), headers=headers, method="POST")
    else:
        req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_live_stats():
    profile = api(f"/users/{USER}")
    repo_count = profile["public_repos"]

    gql = api(None, is_graphql=True, query=f'''
    {{ user(login: "{USER}") {{
        contributionsCollection {{ contributionCalendar {{ totalContributions }} }}
    }} }}''')
    contributions = gql["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]

    # "catalogue_stars" = most repos in the awesome-list set starred by the
    # SAME person, not the highest single-repo star count - that's the fact
    # actually worth bragging about (one person following the whole series).
    tally = {}
    for repo in AWESOME_LIST_REPOS:
        try:
            stargazers = api(f"/repos/{USER}/{repo}/stargazers")
            for s in stargazers:
                login = s.get("login")
                if login:
                    tally[login] = tally.get(login, 0) + 1
        except Exception:
            continue
    max_repeat = max(tally.values()) if tally else 1

    return dict(repo_count=repo_count, contributions=contributions, catalogue_stars=max_repeat)


def build(stats):
    process(os.path.join(SOURCES, "gojo-hero.webp"), os.path.join(BASE, "scene-hero.webp"), dict(
        layout="titlecard", accent=(56, 96, 214),
        headline=["ADITYA KUMAR", "SINGH"],
        headline_pos=(30, 34), head_size=44,
        tech_stack=["TYPESCRIPT", "K6", "KUBERNETES", "gRPC", "GRAFANA", "KAFKA"],
        badge_col_width=340,
        stat=(str(stats["repo_count"]), "PUBLIC REPOS FORGED"),
        istqb_line="ISTQB CTFL + CT-AI v2.0",
        build_line="LET'S BUILD SOMETHING",
        links=["GITHUB.COM/AKS-BUILDS", "LINKEDIN.COM/IN/ITS-AKS"],
    ))

    process(os.path.join(SOURCES, "choso-awesome.webp"), os.path.join(BASE, "scene-awesome.webp"), dict(
        layout="evidenceboard", accent=(196, 120, 40),
        headline=["THE CATALOGUE"],
        subtitle="10 curated lists: classical AI theory + exam prep + OWASP security",
        kanji_char="血",
        badges=["SEARCH\nALGOS", "CASE-BASED\nREASONING", "FUZZY\nLOGIC", "OWASP\nSECURITY"],
        scatter_positions=[(340, 60, -5), (980, 100, 7), (340, 470, 6), (960, 500, -8)],
        stat_pos=(20, 552), stat=(f'{stats["catalogue_stars"]}X+', "STARRED"),
    ))

    process(os.path.join(SOURCES, "sukuna-skills.webp"), os.path.join(BASE, "scene-skills.webp"), dict(
        layout="rpgsheet", accent=(220, 38, 38),
        headline=["SKILL", "ARSENAL"],
        badges=["107 QA\nSKILLS", "91 HEALTH-\nCARE SKILLS", "MCP\nREADY", "2 AGENT\nPACKS"],
        stat=("198", "TOTAL SKILLS SHIPPED FOR AI AGENTS"),
        links_line="quality-skills . healthcareskills",
    ))

    process(os.path.join(SOURCES, "itadori-contact.webp"), os.path.join(BASE, "scene-contact.webp"), dict(
        layout="outro", accent=(219, 84, 40),
        headline=["LET'S BUILD SOMETHING"], head_size=40,
        subtitle=f'{stats["repo_count"]} repos . {stats["contributions"]:,} contributions this year . open to remote & relocation',
        badges=["ISTQB CTFL", "ISTQB CT-AI v2.0"],
        links_line="GITHUB.COM/AKS-BUILDS   •   LINKEDIN.COM/IN/ITS-AKS",
    ))


if __name__ == "__main__":
    stats = fetch_live_stats()
    print("live stats:", stats)
    build(stats)
