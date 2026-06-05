#!/usr/bin/env python3
"""
update_profile.py — Regenerate the dynamic sections of the profile README.

Sections kept up to date automatically (between HTML markers):
  * "What I'm shipping"  -> newest non-fork repos, one emoji each
  * "Things I code with" -> languages aggregated across all repos (new ones auto-appear)

The "Recent GitHub Activity" and contribution-snake sections are handled by their
own workflows and are NOT touched here.

Pure standard library (urllib). Reads GITHUB_TOKEN from the environment for a
higher rate limit (works unauthenticated too, just slower).
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

USER = "aks-builds"
SHIP_COUNT = 6                      # repos shown in "What I'm shipping" (keeps a 2x3 grid)
MAX_LANGS = 16                      # cap language badges
# Name substrings excluded from "What I'm shipping" (training/throwaway repos).
# Languages are still counted from these — only the showcase grid skips them.
SHIP_EXCLUDE = ("training", "assignment", "workshop", "-demo", "sandbox", "scratch")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

SHIP_START, SHIP_END = "<!-- SHIPPING:START -->", "<!-- SHIPPING:END -->"
LANG_START, LANG_END = "<!-- LANGS:START -->", "<!-- LANGS:END -->"
# Reuse the activity markers already in the README (previously fed by an action).
ACT_START, ACT_END = "<!--START_SECTION:activity-->", "<!--END_SECTION:activity-->"
ACT_COUNT = 10                      # lines in "Recent GitHub Activity"
NEW_REPO_DAYS = 30                  # how recently a repo counts as "just created"


def gh(path):
    req = urllib.request.Request("https://api.github.com" + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USER + "-profile-bot")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


# --- emoji selection -------------------------------------------------------

# Curated choices are preserved; anything new falls through to the heuristic.
EMOJI_OVERRIDES = {
    "ai-test-failure-analyzer": "🤖",
    "playwright-userauth-api-suite": "🎭",
    "hitro": "🔫",
    "awesome-owasp-security-testing": "🔐",
    "openspecpm": "📋",
    "quality-skills": "🏆",
    "clausa": "🛡️",
}
HEURISTIC = [
    (("insurance", "policy", "privacy", "security", "owasp", "secret", "vuln"), "🛡️"),
    (("ai", "llm", " ml", "agent", "gpt", "model", "mcp"), "🤖"),
    (("test", "playwright", "qa", "sdet", "automation", "cypress"), "🧪"),
    (("api", "client", "grpc", "graphql", "rest", "kafka"), "🔌"),
    (("deck", "slide", "ppt", "presentation"), "📊"),
    (("data", "analytics", "report", "dashboard"), "📈"),
    (("doc", "spec", "bdd", "skill", "awesome", "guide", "handbook"), "📚"),
    (("web", "ui", "frontend", "site", "portfolio"), "🖥️"),
    (("cli", "tool", "kit", "workflow", "action", "script"), "🛠️"),
    (("game", "unity", "godot"), "🎮"),
    (("health", "care", "med"), "🩺"),
]


def emoji_for(repo):
    name = repo["name"].lower()
    if name in EMOJI_OVERRIDES:
        return EMOJI_OVERRIDES[name]
    hay = " ".join(filter(None, [
        name, (repo.get("description") or ""), " ".join(repo.get("topics") or [])
    ])).lower()
    for kws, em in HEURISTIC:
        if any(k in hay for k in kws):
            return em
    return "🚀"


# --- language badges -------------------------------------------------------

# label, color, shields logo, logoColor
LANG_BADGE = {
    "HTML": ("HTML", "E34F26", "html5", "white"),
    "CSS": ("CSS", "1572B6", "css3", "white"),
    "JavaScript": ("JavaScript", "F7DF1E", "javascript", "black"),
    "TypeScript": ("TypeScript", "3178C6", "typescript", "white"),
    "Python": ("Python", "3776AB", "python", "white"),
    "C#": ("C%23", "512BD4", "csharp", "white"),
    "Shell": ("Bash", "4EAA25", "gnubash", "white"),
    "PowerShell": ("PowerShell", "5391FE", "powershell", "white"),
    "Go": ("Go", "00ADD8", "go", "white"),
    "Rust": ("Rust", "000000", "rust", "white"),
    "Java": ("Java", "007396", "openjdk", "white"),
    "Ruby": ("Ruby", "CC342D", "ruby", "white"),
    "C": ("C", "A8B9CC", "c", "black"),
    "C++": ("C%2B%2B", "00599C", "cplusplus", "white"),
    "Dockerfile": ("Docker", "2496ED", "docker", "white"),
    "Jupyter Notebook": ("Jupyter", "F37626", "jupyter", "white"),
    "Vue": ("Vue", "4FC08D", "vuedotjs", "white"),
    "Kotlin": ("Kotlin", "7F52FF", "kotlin", "white"),
    "Swift": ("Swift", "F05138", "swift", "white"),
    "PHP": ("PHP", "777BB4", "php", "white"),
    "Go Module": ("Go", "00ADD8", "go", "white"),
}
# Skills/tools that linguist won't report as a "language" but should always show.
EXTRA_BADGE = {"Unity": ("Unity", "FFFFFF", "unity", "black")}
PINNED_EXTRAS = ["Unity"]


def badge(lang):
    spec = LANG_BADGE.get(lang) or EXTRA_BADGE.get(lang)
    if spec:
        label, color, logo, lc = spec
        return (f"![{lang}](https://img.shields.io/badge/{label}-{color}"
                f"?style=for-the-badge&logo={logo}&logoColor={lc})")
    # Generic badge for a brand-new, unmapped language — auto-highlighted.
    safe = lang.replace("-", "--").replace(" ", "_").replace("#", "%23").replace("+", "%2B")
    return f"![{lang}](https://img.shields.io/badge/{safe}-58A6FF?style=for-the-badge)"


# --- rendering -------------------------------------------------------------

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_shipping(repos):
    cells = []
    for r in repos[:SHIP_COUNT]:
        desc = (r.get("description") or "").strip() or "—"
        cells.append(
            '    <td width="50%" valign="top">\n'
            f'      <h4>{emoji_for(r)} <a href="{r["html_url"]}">{esc(r["name"])}</a></h4>\n'
            f'      {esc(desc)}\n'
            '    </td>'
        )
    out = ["<table>"]
    for i in range(0, len(cells), 2):
        out.append("  <tr>")
        out.extend(cells[i:i + 2])
        out.append("  </tr>")
    out.append("</table>")
    return "\n".join(out)


def build_langs(repos):
    totals = {}
    for r in repos:
        try:
            langs = gh(f"/repos/{USER}/{r['name']}/languages")
        except urllib.error.HTTPError:
            continue
        for k, v in langs.items():
            totals[k] = totals.get(k, 0) + v
    order = sorted(totals, key=lambda k: (-totals[k], k))[:MAX_LANGS]
    for ex in PINNED_EXTRAS:
        if ex not in order:
            order.append(ex)
    return "\n".join(badge(lang) for lang in order)


# --- recent activity (includes pushes + new repos, unlike the old action) ----

def _ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def _repo_link(full_name):
    return f"[{full_name}](https://github.com/{full_name})"


def build_activity(repos, events):
    """Merge recently-created repos with the public events feed into a single
    'what I've been up to' list. New repos are sourced from the repos API (the
    events feed lags for fresh pushes), so a just-shipped repo always appears."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC to match _ts()
    cutoff = now - timedelta(days=NEW_REPO_DAYS)
    entries = []  # (datetime, text)

    # 1) Freshly created repos — reliable, catches brand-new repos immediately.
    for r in repos:
        ca = r.get("created_at")
        if ca and _ts(ca) >= cutoff:
            entries.append((_ts(ca), f"🎉 Created repository {_repo_link(r['full_name'])}"))

    # 2) Public events (newest first).
    for e in events:
        try:
            t = _ts(e["created_at"])
        except Exception:
            continue
        typ, repo, pl = e.get("type"), e["repo"]["name"], e.get("payload", {})
        txt = None
        if typ == "PushEvent":
            txt = f"⬆️ Pushed to {_repo_link(repo)}"
        elif typ == "PullRequestEvent":
            n = pl.get("number")
            pr = pl.get("pull_request") or {}
            url = pr.get("html_url") or f"https://github.com/{repo}/pull/{n}"
            act = pl.get("action")
            if act == "opened":
                txt = f"💪 Opened PR [#{n}]({url}) in {_repo_link(repo)}"
            elif act == "closed" and pr.get("merged"):
                txt = f"🎉 Merged PR [#{n}]({url}) in {_repo_link(repo)}"
            elif act == "closed":
                txt = f"🔒 Closed PR [#{n}]({url}) in {_repo_link(repo)}"
        elif typ == "IssuesEvent":
            iss = pl.get("issue") or {}
            n, url, act = iss.get("number"), iss.get("html_url"), pl.get("action")
            if act == "opened":
                txt = f"🐛 Opened issue [#{n}]({url}) in {_repo_link(repo)}"
            elif act == "closed":
                txt = f"🔒 Closed issue [#{n}]({url}) in {_repo_link(repo)}"
        elif typ == "ReleaseEvent":
            rel = pl.get("release") or {}
            txt = f"🏷️ Released {rel.get('tag_name', '')} in {_repo_link(repo)}"
        elif typ == "ForkEvent":
            txt = f"🍴 Forked {_repo_link(repo)}"
        elif typ == "CreateEvent" and pl.get("ref_type") == "repository":
            txt = f"🎉 Created repository {_repo_link(repo)}"
        if txt:
            entries.append((t, txt))

    # newest first, drop duplicate texts (collapses repeated pushes to one line)
    entries.sort(key=lambda x: x[0], reverse=True)
    seen, lines = set(), []
    for _t, txt in entries:
        if txt in seen:
            continue
        seen.add(txt)
        lines.append(f"{len(lines) + 1}. {txt}")
        if len(lines) >= ACT_COUNT:
            break
    return "\n".join(lines)


def replace_block(text, start, end, content):
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pat.search(text):
        sys.exit(f"ERROR: markers {start} / {end} not found in README.md")
    return pat.sub(lambda _m: f"{start}\n{content}\n{end}", text)


def main():
    repos = gh(f"/users/{USER}/repos?per_page=100&type=owner&sort=pushed")
    repos = [r for r in repos
             if not r.get("fork") and not r.get("archived") and r["name"] != USER]

    with open(README, "r", encoding="utf-8") as f:
        text = f.read()

    ship_repos = [r for r in repos
                  if not any(s in r["name"].lower() for s in SHIP_EXCLUDE)]
    text = replace_block(text, SHIP_START, SHIP_END, build_shipping(ship_repos))
    text = replace_block(text, LANG_START, LANG_END, build_langs(repos))

    try:
        events = gh(f"/users/{USER}/events/public?per_page=100")
    except urllib.error.HTTPError:
        events = []
    text = replace_block(text, ACT_START, ACT_END, build_activity(repos, events))

    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"Updated README.md: {min(len(ship_repos), SHIP_COUNT)} shipping repos, "
          f"{len(repos)} repos scanned for languages, activity from "
          f"{len(events)} events + new repos.")


if __name__ == "__main__":
    main()
