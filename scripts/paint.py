"""Render the contribution calendar being painted by a rainbow brush, as animated SVGs (light and dark)."""
import json
import os
import sys
import urllib.request
from datetime import date

USER = os.environ.get("GH_USER", "analiaacostaok")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "dist"

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{weeks{contributionDays{date weekday contributionLevel}}}}}}"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
weeks = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

# Theme colors are placeholders, filled in per theme when writing the files.
THEMES = {
    "paint.svg": {"__BG__": "#FFFFFF", "__EMPTY__": "#EBEDF0", "__LABEL__": "#57606A"},
    "paint-dark.svg": {"__BG__": "#0D1117", "__EMPTY__": "#161B22", "__LABEL__": "#8B949E"},
}
EMPTY = "__EMPTY__"
LEVELS = {
    "FIRST_QUARTILE": "#54A0FF",
    "SECOND_QUARTILE": "#1DD1A1",
    "THIRD_QUARTILE": "#FECA57",
    "FOURTH_QUARTILE": "#FF5C5C",
}
RAINBOW = ["#FF5C5C", "#FF9F43", "#FECA57", "#1DD1A1", "#54A0FF", "#A66BFF"]

CELL, GAP = 11, 2
STEP = CELL + GAP
PAD_X, GRID_Y = 14, 40
W = 716
H = GRID_Y + 7 * STEP + 40

CYCLE = 20  # seconds per loop
PAINT_END = 60  # % of the cycle when the brush reaches the end
HOLD_END = 90  # % of the cycle when the painting starts fading for the next loop

n = len(weeks)
grid_w = n * STEP - GAP
x0 = PAD_X + (W - 2 * PAD_X - grid_w) / 2


def column_x(i):
    return x0 + i * STEP


css = [
    f".p{{opacity:0;animation:none {CYCLE}s linear infinite}}",
    f".br{{animation:br {CYCLE}s linear infinite}}",
    f"@keyframes br{{0%{{transform:translateX(0);opacity:1}}{PAINT_END}%{{transform:translateX({grid_w + 8:.1f}px);opacity:1}}"
    f"{PAINT_END + 3}%,100%{{transform:translateX({grid_w + 8:.1f}px);opacity:0}}}}",
    '.m{font:600 11px "Segoe UI",Helvetica,Arial,sans-serif;fill:__LABEL__}',
    "@media (prefers-reduced-motion:reduce){.p{animation:none!important;opacity:1}.br{display:none}}",
]
body = []
for i, week in enumerate(weeks):
    at = PAINT_END * (i + 0.5) / n
    css.append(
        f"@keyframes k{i}{{0%,{at:.2f}%{{opacity:0}}{at + 0.6:.2f}%,{HOLD_END}%{{opacity:1}}100%{{opacity:0}}}}"
        f".k{i}{{animation-name:k{i}}}"
    )
    x = column_x(i)
    painted = []
    for day in week["contributionDays"]:
        y = GRID_Y + day["weekday"] * STEP
        body.append(f'<rect x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{EMPTY}"/>')
        color = LEVELS.get(day["contributionLevel"])
        if color:
            painted.append(f'<rect x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
    if painted:
        body.append(f'<g class="p k{i}">{"".join(painted)}</g>')

# Month labels on the week where each month starts, skipping labels too close to the next one.
starts = []
for i, week in enumerate(weeks):
    month = week["contributionDays"][0]["date"][:7]
    if not starts or starts[-1][1] != month:
        starts.append((i, month))
for k, (i, month) in enumerate(starts):
    next_i = starts[k + 1][0] if k + 1 < len(starts) else n
    if next_i - i >= 3:
        label = date(int(month[:4]), int(month[5:]), 1).strftime("%b")
        body.append(f'<text class="m" x="{column_x(i):.1f}" y="{GRID_Y - 10}">{label}</text>')

# Legend.
lx = W - PAD_X - 5 * STEP - 70
ly = GRID_Y + 7 * STEP + 14
legend = [f'<text class="m" x="{lx - 34}" y="{ly + 9}">Less</text>']
for k, color in enumerate([EMPTY, *LEVELS.values()]):
    legend.append(f'<rect x="{lx + k * STEP}" y="{ly}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
legend.append(f'<text class="m" x="{lx + 5 * STEP + 4}" y="{ly + 9}">More</text>')

# Brush: a flat paintbrush (rainbow bristles, metal ferrule, wooden handle) sweeping left to right.
# Drawn with the bristle tip at (0, 0), then mirrored so the handle leads and the bristles drag behind,
# painting the days as they pass over them.
hb = 7 * STEP / 2 + 6  # half the bristle height, a bit taller than the grid
bristle_lines = "".join(
    f'<line x1="-26" y1="{y:.1f}" x2="-1" y2="{y:.1f}" stroke="#0d1117" stroke-opacity=".25" stroke-width="1"/>'
    for y in [-hb + 8 + k * (2 * hb - 16) / 8 for k in range(9)]
)
brush = [
    "<defs>",
    '<linearGradient id="rb" x1="0" y1="0" x2="0" y2="1">',
    *[f'<stop offset="{k / (len(RAINBOW) - 1):.2f}" stop-color="{c}"/>' for k, c in enumerate(RAINBOW)],
    "</linearGradient>",
    '<linearGradient id="metal" x1="0" y1="0" x2="1" y2="0">'
    '<stop offset="0" stop-color="#8B949E"/><stop offset=".45" stop-color="#F0F6FC"/><stop offset="1" stop-color="#6E7681"/>'
    "</linearGradient>",
    '<linearGradient id="wood" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#D49A6A"/><stop offset=".5" stop-color="#B07A4F"/><stop offset="1" stop-color="#8A5A36"/>'
    "</linearGradient>",
    "</defs>",
    f'<g class="br"><g transform="translate({x0 - 24:.1f},{GRID_Y + 3.5 * STEP - GAP / 2:.1f}) scale(-1,1) rotate(-16)">',
    # Wooden handle with a hanging hole.
    f'<path d="M-44,{-hb + 6:.1f} C-62,{-hb + 6:.1f} -66,-13 -84,-13 L-156,-9 Q-166,0 -156,9 L-84,13 '
    f'C-66,13 -62,{hb - 6:.1f} -44,{hb - 6:.1f} Z" fill="url(#wood)"/>',
    '<circle cx="-150" cy="0" r="3" fill="__BG__"/>',
    # Metal ferrule with crimp lines.
    f'<rect x="-46" y="{-hb - 1:.1f}" width="21" height="{2 * hb + 2:.1f}" rx="3" fill="url(#metal)"/>',
    f'<line x1="-40" y1="{-hb + 1:.1f}" x2="-40" y2="{hb - 1:.1f}" stroke="#6E7681" stroke-width="1.5"/>',
    f'<line x1="-34" y1="{-hb + 1:.1f}" x2="-34" y2="{hb - 1:.1f}" stroke="#6E7681" stroke-width="1.5"/>',
    # Bristles dipped in rainbow paint, with a rounded flat tip.
    f'<path d="M-26,{-hb:.1f} L-7,{-hb + 2:.1f} Q2,{-hb + 6:.1f} 2,{-hb + 16:.1f} L2,{hb - 16:.1f} '
    f'Q2,{hb - 6:.1f} -7,{hb - 2:.1f} L-26,{hb:.1f} Z" fill="url(#rb)"/>',
    bristle_lines,
    "</g></g>",
]

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
    'aria-label="My contribution calendar being painted in rainbow colors">',
    f"<style>{''.join(css)}</style>",
    f'<rect width="{W}" height="{H}" rx="18" fill="__BG__"/>',
    *body,
    *legend,
    *brush,
    "</svg>",
]

os.makedirs(OUT_DIR, exist_ok=True)
for name, colors in THEMES.items():
    out = "\n".join(svg)
    for token, value in colors.items():
        out = out.replace(token, value)
    with open(os.path.join(OUT_DIR, name), "w") as f:
        f.write(out)
    print(f"wrote {OUT_DIR}/{name}: {n} weeks")
