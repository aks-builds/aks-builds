#!/usr/bin/env python3
"""
generate_terminal_svg.py — Regenerates terminal-session.svg with live repo data.

Updates two dynamic sections inside the SVG:
  - Project rows (top 6 non-fork repos by push date)
  - Stack chips (languages aggregated across all repos)

Everything else (npm, talks, stats, fun fact) is static in the SVG.
Pure stdlib — no pip install required.
"""
import json, os, re, sys, urllib.error, urllib.request

USER  = "aks-builds"
ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG   = os.path.join(ROOT, "terminal-session.svg")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

SKIP_REPOS = {USER}  # skip the profile README repo itself

TAG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "C#": "#239120", "HTML": "#e34c26", "PowerShell": "#012456",
    "Shell": "#4EAA25", "Go": "#00ADD8", "Rust": "#DEA584",
}

# Map repo name → display tags
REPO_TAGS = {
    "cliproof":                       ["Python", "npm", "MCP"],
    "ai-test-failure-analyzer":       ["Python", "npm", "AI"],
    "openspecpm":                     ["JS", "npm", "BDD"],
    "Hitro":                          ["TypeScript", "Electron", "React"],
    "reqweave":                       ["TypeScript", "OpenAPI"],
    "quality-skills":                 ["Claude", "QA"],
    "healthcareskills":               ["Claude", "Healthcare"],
    "clausa":                         ["Python", "AI"],
    "playwright-userauth-api-suite":  ["TypeScript", "Playwright"],
    "awesome-owasp-security-testing": ["Security", "OWASP"],
    "workflows":                      ["PowerShell", "CI/CD"],
    "formula-sim-pro-unity":          ["C#", "Unity"],
}

CHIP_STROKE = "#1c1c1c"
MONO = "ui-monospace,'Cascadia Code','Source Code Pro',Menlo,Consolas,monospace"


def gh(path):
    req = urllib.request.Request("https://api.github.com" + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USER + "-profile-bot")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def tag_chip_svg(x, y, label, color="#a3a3a3"):
    """Renders a single tag chip at (x, y). Returns (svg_fragment, width_used)."""
    w = len(label) * 6 + 12
    rect = (f'<rect x="{x}" y="{y}" width="{w}" height="16" rx="2" '
            f'fill="none" stroke="{CHIP_STROKE}"/>')
    txt  = (f'<text x="{x+6}" y="{y+12}" '
            f'font-family="{MONO}" font-size="9" fill="{color}">{label}</text>')
    return rect + "\n  " + txt, w + 6  # 6px gap


def build_project_rows(repos):
    """Build SVG text for top-6 project rows starting at y=220."""
    top = [r for r in repos if r["name"] not in SKIP_REPOS][:6]
    ROW_H = 18
    Y0    = 220
    lines = []
    for i, r in enumerate(top):
        y   = Y0 + i * ROW_H
        name = r["name"]
        tags = REPO_TAGS.get(name, [r.get("language") or "—"])[:3]

        # permissions text
        lines.append(
            f'  <text x="20" y="{y}" '
            f'font-family="{MONO}" font-size="10" fill="#3f3f46">drwxr-xr-x</text>')
        # repo name
        lines.append(
            f'  <text x="120" y="{y}" '
            f'font-family="{MONO}" font-size="11" font-weight="600" '
            f'fill="#22c55e">{name}</text>')
        # tag chips
        name_w   = len(name) * 7  # rough char width at font-size 11
        tag_x    = 120 + name_w + 10
        for tag in tags:
            color = TAG_COLORS.get(tag, "#52525b")
            w = len(tag) * 6 + 12
            lines.append(
                f'  <rect x="{tag_x}" y="{y-11}" width="{w}" height="14" '
                f'rx="2" fill="none" stroke="#1c1c1c"/>')
            lines.append(
                f'  <text x="{tag_x+6}" y="{y}" '
                f'font-family="{MONO}" font-size="9" fill="#52525b">{tag}</text>')
            tag_x += w + 4

    lines.append(
        f'  <text x="20" y="{Y0 + 6*ROW_H + 4}" '
        f'font-family="{MONO}" font-size="10" fill="#3f3f46">'
        f'+{len(repos)-6} more → github.com/aks-builds</text>')
    return "\n".join(lines)


def build_stack_chips(repos):
    """Build SVG chip rows from aggregated languages, starting at y=618."""
    totals = {}
    for r in repos:
        try:
            langs = gh(f"/repos/{USER}/{r['name']}/languages")
        except urllib.error.HTTPError:
            continue
        for k, v in langs.items():
            totals[k] = totals.get(k, 0) + v

    # Always include these even if linguist misses them
    PINNED = ["Claude Code", "MCP", "Docker", "GitHub Actions", "Electron", "React", "Unity"]
    order = [k for k, _ in sorted(totals.items(), key=lambda x: -x[1]) if k not in PINNED][:8]
    order += [p for p in PINNED if p not in order]

    # Layout: wrap into rows of max ~760px
    ROW_W = 760
    rows, cur_x, cur_row = [[]], 20, 0
    for label in order:
        w = len(label) * 6 + 18
        if cur_x + w > ROW_W + 20 and rows[cur_row]:
            cur_row += 1
            rows.append([])
            cur_x = 20
        rows[cur_row].append((label, cur_x))
        cur_x += w + 6

    lines = []
    for ri, row in enumerate(rows):
        y = 618 + ri * 22
        for label, x in row:
            color = TAG_COLORS.get(label, "#a3a3a3")
            if label in ("Claude Code", "MCP"):
                color = "#22c55e"
            w = len(label) * 6 + 12
            lines.append(
                f'  <rect x="{x}" y="{y}" width="{w}" height="16" rx="2" '
                f'fill="none" stroke="#1c1c1c"/>')
            lines.append(
                f'  <text x="{x+6}" y="{y+12}" '
                f'font-family="{MONO}" font-size="9" fill="{color}">{label}</text>')
    return "\n".join(lines)


PROJ_START  = "<!-- PROJECTS_START -->"
PROJ_END    = "<!-- PROJECTS_END -->"
STACK_START = "<!-- STACK_START -->"
STACK_END   = "<!-- STACK_END -->"


def replace_block(text, start, end, content):
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pat.search(text):
        print(f"WARNING: markers {start}/{end} not found — skipping", file=sys.stderr)
        return text
    return pat.sub(f"{start}\n{content}\n{end}", text)


def main():
    repos = gh(f"/users/{USER}/repos?per_page=100&type=owner&sort=pushed")
    repos = [r for r in repos if not r.get("fork") and not r.get("archived")]

    with open(SVG, "r", encoding="utf-8") as f:
        svg = f.read()

    svg = replace_block(svg, PROJ_START,  PROJ_END,  build_project_rows(repos))
    svg = replace_block(svg, STACK_START, STACK_END, build_stack_chips(repos))

    with open(SVG, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"terminal-session.svg updated — {len(repos)} repos processed.")


if __name__ == "__main__":
    main()
