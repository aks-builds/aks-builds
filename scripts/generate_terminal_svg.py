#!/usr/bin/env python3
"""
generate_terminal_svg.py — Regenerates terminal-session.svg with live repo/npm data.

Updates three dynamic sections inside the SVG:
  - Project rows (top 6 non-fork repos by push date)
  - Stack chips (languages aggregated across all repos)
  - npm install box + stats section (packages from npm registry, auto-resizes SVG height)

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
    """Build SVG text for top-6 project rows starting at y=238."""
    top = [r for r in repos if r["name"] not in SKIP_REPOS][:6]
    ROW_H     = 18
    Y0        = 238
    T_START   = 3.15   # ls command finishes typing at ~3.04s
    T_CASCADE = 0.06   # stagger between rows
    lines = []
    for i, r in enumerate(top):
        y    = Y0 + i * ROW_H
        t    = round(T_START + i * T_CASCADE, 3)
        anim = (f'<animate attributeName="opacity" from="0" to="1" '
                f'dur="0.05s" begin="{t}s" fill="freeze"/>')
        name = r["name"]
        tags = REPO_TAGS.get(name, [r.get("language") or "—"])[:3]

        lines.append(
            f'  <text x="20" y="{y}" opacity="0" '
            f'font-family="{MONO}" font-size="10" fill="#3f3f46">drwxr-xr-x{anim}</text>')
        lines.append(
            f'  <text x="120" y="{y}" opacity="0" '
            f'font-family="{MONO}" font-size="11" font-weight="600" '
            f'fill="#22c55e">{name}{anim}</text>')
        name_w = len(name) * 7
        tag_x  = 120 + name_w + 10
        for tag in tags:
            color = TAG_COLORS.get(tag, "#52525b")
            w     = len(tag) * 6 + 12
            lines.append(
                f'  <rect x="{tag_x}" y="{y-11}" width="{w}" height="14" '
                f'rx="2" fill="none" stroke="#1c1c1c" opacity="0">{anim}</rect>')
            lines.append(
                f'  <text x="{tag_x+6}" y="{y}" opacity="0" '
                f'font-family="{MONO}" font-size="9" fill="{color}">{tag}{anim}</text>')
            tag_x += w + 4

    t_more    = round(T_START + 6 * T_CASCADE, 3)
    anim_more = (f'<animate attributeName="opacity" from="0" to="1" '
                 f'dur="0.05s" begin="{t_more}s" fill="freeze"/>')
    lines.append(
        f'  <text x="20" y="{Y0 + 6*ROW_H + 4}" opacity="0" '
        f'font-family="{MONO}" font-size="10" fill="#3f3f46">'
        f'+{{len(repos)-6}} more → github.com/aks-builds{anim_more}</text>')
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


PROJ_START = "<!-- PROJECTS_START -->"
PROJ_END   = "<!-- PROJECTS_END -->"
STACK_START = "<!-- STACK_START -->"
STACK_END   = "<!-- STACK_END -->"
NPM_START  = "<!-- NPM_START -->"
NPM_END    = "<!-- NPM_END -->"

# ── npm section constants ──────────────────────────────────────────────────────
NPM_BOX_Y    = 440
NPM_FIRST_Y  = 464   # y of first install line (24px below box top)
NPM_LINE_H   = 24
NPM_BOT_PAD  = 20
SEP_GAP      = 24    # gap from box bottom to separator
CMD_OFFSET   = 28    # separator → command baseline
NUM_OFFSET   = 40    # command → stat number baseline
LBL_OFFSET   = 18    # number → label baseline
FSEP_OFFSET  = 24    # label → final separator
FPROMPT_OFF  = 28    # final separator → prompt baseline
CURSOR_ABOVE = 14    # prompt baseline − cursor rect top
SVG_BTM_PAD  = 20    # cursor bottom → SVG edge

NPM_DESCRIPTIONS = {
    "ai-test-failure-analyzer": "AI-powered test root-cause",
    "cliproof":                  "terminal screenshot proof tool",
    "har-to-slo":                "convert HAR files to SLO metrics",
    "openspecpm":                "BDD project management for AI agents",
}


def fetch_npm_packages():
    url = f"https://registry.npmjs.org/-/v1/search?text=maintainer:{USER}&size=50"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", f"{USER}-profile-bot")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    pkgs = [o["package"] for o in data.get("objects", [])]
    return sorted(pkgs, key=lambda p: p["name"])


def build_npm_section(packages):
    """Return (svg_fragment, total_svg_height) for the NPM_START…NPM_END block."""
    n = len(packages)
    box_h      = (NPM_FIRST_Y - NPM_BOX_Y) + (n - 1) * NPM_LINE_H + NPM_BOT_PAD
    box_bot    = NPM_BOX_Y + box_h
    sep_y      = box_bot + SEP_GAP
    cmd_y      = sep_y + CMD_OFFSET
    num_y      = cmd_y + NUM_OFFSET
    lbl_y      = num_y + LBL_OFFSET
    fsep_y     = lbl_y + FSEP_OFFSET
    fprompt_y  = fsep_y + FPROMPT_OFF
    cursor_y   = fprompt_y - CURSOR_ABOVE
    svg_h      = cursor_y + 16 + SVG_BTM_PAD

    L = []
    # npm install box
    L.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.25s" begin="6.2s" fill="freeze"/>')
    L.append(f'<rect x="20" y="{NPM_BOX_Y}" width="780" height="{box_h}" rx="4" fill="none" stroke="#1c1c1c"/>')
    for i, pkg in enumerate(packages):
        y    = NPM_FIRST_Y + i * NPM_LINE_H
        name = pkg["name"]
        desc = NPM_DESCRIPTIONS.get(name) or (pkg.get("description") or "npm package")
        L.append(f'<text x="34" y="{y}" font-family="{MONO}" font-size="11" fill="#22c55e">$</text>')
        L.append(f'<text x="48" y="{y}" font-family="{MONO}" font-size="11" fill="#e2e8f0">npm install -g {name}</text>')
        L.append(f'<text x="440" y="{y}" font-family="{MONO}" font-size="10" fill="#2d2d2d">&#x2192; {desc}</text>')
    L.append('</g>')

    # separator before §4
    L.append(f'<rect x="20" y="{sep_y}" width="780" height="1" fill="#1c1c1c" opacity="0">')
    L.append(f'  <animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="7.0s" fill="freeze"/>')
    L.append(f'</rect>')

    # §4 gh stats — command with typing animation
    L.append(f'<!-- §4 gh stats -->')
    L.append(f'<text x="20" y="{cmd_y}" opacity="0" font-family="{MONO}" font-size="12" fill="#22c55e">~'
             f'<animate attributeName="opacity" from="0" to="1" dur="0.1s" begin="7.1s" fill="freeze"/></text>')
    typing = "gh stats --user aks-builds"
    tspans = []
    for j, ch in enumerate(typing):
        t    = round(7.2 + j * 0.055, 3)
        safe = ch.replace("&", "&amp;").replace("<", "&lt;")
        tspans.append(f'<tspan opacity="0">'
                      f'<animate attributeName="opacity" from="0" to="1" dur="0.01s" begin="{t}s" fill="freeze"/>'
                      f'{safe}</tspan>')
    L.append(f'<text x="52" y="{cmd_y}" font-family="{MONO}" font-size="12" fill="#e2e8f0">{"".join(tspans)}</text>')

    # stat counters
    for x, val, lbl, t in [
        (20,  "16",  "REPOSITORIES", "8.7s"),
        (140, "5+",  "NPM PACKAGES", "8.9s"),
        (280, "50+", "AGENT SKILLS", "9.1s"),
        (430, "3",   "CONF TALKS",   "9.3s"),
    ]:
        L.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.2s" begin="{t}" fill="freeze"/>')
        L.append(f'<text x="{x}" y="{num_y}" font-family="{MONO}" font-size="30" font-weight="600" fill="#22c55e">{val}</text>')
        L.append(f'<text x="{x}" y="{lbl_y}" font-family="{MONO}" font-size="9" fill="#3f3f46" letter-spacing="0.08em">{lbl}</text>')
        L.append('</g>')

    # final separator
    L.append(f'<rect x="20" y="{fsep_y}" width="780" height="1" fill="#1c1c1c" opacity="0">')
    L.append(f'  <animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="9.7s" fill="freeze"/>')
    L.append(f'</rect>')

    # final prompt
    L.append(f'<text x="20" y="{fprompt_y}" opacity="0" font-family="{MONO}" font-size="12" fill="#22c55e">~')
    L.append(f'  <animate attributeName="opacity" from="0" to="1" dur="0.1s" begin="9.9s" fill="freeze"/>')
    L.append(f'</text>')

    # blinking cursor
    L.append(f'<rect x="52" y="{cursor_y}" width="8" height="16" fill="#22c55e" opacity="0">')
    L.append(f'  <animate attributeName="opacity" from="0" to="1" dur="0.1s" begin="10.0s" fill="freeze"/>')
    L.append(f'  <animate attributeName="opacity" values="1;0;1" dur="1s" begin="10.1s" repeatCount="indefinite"/>')
    L.append(f'</rect>')

    return "\n".join(L), svg_h


def update_svg_height(svg, h):
    """Patch the four height references in the SVG element and child rects."""
    svg = re.sub(r'(<svg[^>]*\bheight=")[^"]*(")', rf'\g<1>{h}\g<2>', svg)
    svg = re.sub(r'(<svg[^>]*viewBox="0 0 820 )[^"]*(")', rf'\g<1>{h}\g<2>', svg)
    svg = re.sub(r'(<clipPath[^>]*><rect[^>]+height=")[^"]*(")', rf'\g<1>{h - 38}\g<2>', svg)
    svg = re.sub(r'(<rect width="820" height=")[^"]*(" rx="10" fill="#0a0a0a")', rf'\g<1>{h}\g<2>', svg)
    svg = re.sub(r'(<rect width="820" height=")[^"]*(" rx="10" fill="none")', rf'\g<1>{h}\g<2>', svg)
    return svg


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

    svg = replace_block(svg, PROJ_START, PROJ_END, build_project_rows(repos))
    svg = replace_block(svg, STACK_START, STACK_END, build_stack_chips(repos))

    try:
        packages = fetch_npm_packages()
    except Exception as e:
        print(f"WARNING: npm fetch failed ({e}) — skipping npm section", file=sys.stderr)
        packages = []

    if packages:
        npm_block, svg_h = build_npm_section(packages)
        svg = replace_block(svg, NPM_START, NPM_END, npm_block)
        svg = update_svg_height(svg, svg_h)
        print(f"npm section: {len(packages)} package(s), SVG height → {svg_h}px.")

    with open(SVG, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"terminal-session.svg updated — {len(repos)} repos processed.")


if __name__ == "__main__":
    main()
