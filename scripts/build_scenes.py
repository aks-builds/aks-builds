from compose import process

BASE = "C:/NashTech/aks-builds-profile/assets/scenes/"

sections = [
    dict(
        src=BASE + "gojo-hero.webp", out=BASE + "final-1-hero.webp",
        layout="titlecard",
        accent=(56, 96, 214),
        headline=["ADITYA KUMAR", "SINGH"],
        subtitle="SDET . CLOUD NATIVE QUALITY ENGINEER",
        headline_pos=(30, 40), head_size=52,
        stat=("41", "PUBLIC REPOS"),
        links_line="GITHUB.COM/AKS-BUILDS  .  LINKEDIN.COM/IN/ITS-AKS",
    ),
    dict(
        src=BASE + "choso-awesome.webp", out=BASE + "final-2-awesome.webp",
        layout="evidenceboard",
        accent=(196, 120, 40),
        headline=["THE CATALOGUE"],
        subtitle="10 curated lists: classical AI theory + exam prep + OWASP security",
        kanji_char="\u8840",
        badges=["SEARCH\nALGOS", "CASE-BASED\nREASONING", "FUZZY\nLOGIC", "OWASP\nSECURITY"],
        scatter_positions=[(340, 60, -5), (980, 100, 7), (340, 470, 6), (960, 500, -8)],
        stat_pos=(20, 574), stat=("4X+", "STARRED"),
    ),
    dict(
        src=BASE + "sukuna-skills.webp", out=BASE + "final-3-skills.webp",
        layout="rpgsheet",
        accent=(220, 38, 38),
        headline=["SKILL", "ARSENAL"],
        badges=["107 QA\nSKILLS", "91 HEALTH-\nCARE SKILLS", "MCP\nREADY", "2 AGENT\nPACKS"],
        stat=("198", "TOTAL SKILLS SHIPPED FOR AI AGENTS"),
        links_line="quality-skills . healthcareskills",
    ),
    dict(
        src=BASE + "itadori-contact.webp", out=BASE + "final-4-contact.webp",
        layout="outro",
        accent=(219, 84, 40),
        headline=["LET'S BUILD SOMETHING"],
        head_size=40,
        subtitle="41 repos . 4,237 contributions this year . open to remote & relocation",
        badges=["ISTQB CTFL", "ISTQB CT-AI v2.0"],
        links_line="GITHUB.COM/AKS-BUILDS   \u2022   LINKEDIN.COM/IN/ITS-AKS",
    ),
]

for cfg in sections:
    src = cfg.pop("src")
    out = cfg.pop("out")
    process(src, out, cfg)
