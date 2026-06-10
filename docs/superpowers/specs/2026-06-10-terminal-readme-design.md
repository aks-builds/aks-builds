# Terminal README — Design Spec
**Date:** 2026-06-10  
**Status:** Approved

---

## Goal
Replace the current split README (SVG header + markdown sections) with a single
immersive terminal-session SVG. Everything — identity, projects, npm, talks,
stack, stats, fun fact — appears as animated command + output inside one macOS
terminal window. The contribution snake renders flush below with no separator.

---

## Files

| File | Action | Purpose |
|---|---|---|
| `terminal-session.svg` | Create | The full animated terminal SVG |
| `scripts/generate_terminal_svg.py` | Create | Regenerates SVG from live GitHub data |
| `.github/workflows/profile-sections.yml` | Update | Calls generate_terminal_svg.py |
| `README.md` | Simplify | 2 img tags: SVG + snake |
| `terminal-header.svg` | Delete | Superseded |

---

## SVG spec

**Dimensions:** 820 × 980 px  
**Font:** `ui-monospace,'Cascadia Code','Source Code Pro',Menlo,Consolas,monospace`  
**Colors:** bg `#0a0a0a` · surface `#111` · border `#1c1c1c` · green `#22c55e` ·
text `#fafafa` · muted `#52525b` · amber `#f59e0b`

### Window chrome
- Rounded rect (r=10), `#0a0a0a` fill, `#1c1c1c` 1px stroke
- Title bar 36px: `#111111`, dots red/amber/green at cx 18/36/54
- Title text: `aditya@github — zsh — 120×40`, centered, `#3f3f46`

### Animation sequence (SMIL, no JS)

Each command uses `<clipPath>` + animated `<rect width 0→N>` to reveal text
left-to-right. Output blocks use `opacity 0→1` with `begin` delay. All
`fill="freeze"` so final state persists. Cursor blinks `repeatCount="indefinite"`.

| t (begin) | Command | Output |
|---|---|---|
| 0.3s | `~ whoami` | Name 28px bold · role · ● HIREABLE · 3 links |
| 3.0s | `~ ls -la ./projects/` | 6 repo rows: `drwxr-xr-x name [tags]` — **dynamic** |
| 6.5s | `~ cat ./npm/install.sh` | Bordered box with 3 `$ npm i …` lines |
| 9.0s | `~ ls ./talks/` | 4 rows: year · title · venue (upcoming in amber) |
| 11.5s | `~ cat ./stack.txt` | Chip row — **dynamic** |
| 13.5s | `~ gh stats` | 4 stat cols: repos · npm · skills · talks |
| 15.5s | `~ echo $FUN_FACT` | Fun fact in muted italic |
| 17.0s | `~ ▌` | Blinking green cursor, stays |

### Dynamic sections
`generate_terminal_svg.py` replaces only the text inside:
- `<!-- PROJECTS_ROWS -->` — repo name + language tags (top 6 non-fork repos by push date)
- `<!-- STACK_CHIPS -->` — language chips aggregated across repos (same logic as update_profile.py)

Static sections (npm, talks, stats, fun fact) are hardcoded strings in the script.

---

## generate_terminal_svg.py

- Pure stdlib (urllib, re) — no pip install needed in CI
- Reads `GITHUB_TOKEN` from env for higher rate limit
- Fetches `/users/aks-builds/repos?per_page=100&sort=pushed`
- Builds project rows (top 6) + stack chips
- Reads `terminal-session.svg`, replaces marker comments, writes back
- If no SVG exists yet, writes from a full embedded template string
- Same commit guard as `update_profile.py` (workflow checks git diff)

---

## README.md (final form)

```markdown
<div align="center">
<img src="./terminal-session.svg" width="100%" alt="Aditya S. — terminal session"/>
<img src="https://raw.githubusercontent.com/aks-builds/aks-builds/output/github-contribution-grid-snake-dark.svg" alt="contribution snake"/>
</div>
```

No HR, no badges, no tables outside the SVG.

---

## Workflow change

`profile-sections.yml` step change:
```yaml
- name: Regenerate terminal SVG
  run: python scripts/generate_terminal_svg.py
```
Replaces the old `python scripts/update_profile.py` step.
Trigger, checkout, commit-if-changed logic unchanged.

---

## Out of scope
- YouTube thumbnails inside SVG (GitHub sanitises external images)  
- npm live version badges inside SVG (no network calls in SVG)  
- Dark/light mode variants  
- Multiple terminal tabs
