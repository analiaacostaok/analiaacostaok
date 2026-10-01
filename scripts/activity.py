"""Render a monthly contributions chart (last 12 months) as an animated SVG."""
import json
import os
import sys
import urllib.request
from collections import OrderedDict
from datetime import date

USER = os.environ.get("GH_USER", "analiaacostaok")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist/activity.svg"

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]

# Only complete months: skip the current month and a partial first month.
days = [d for week in cal["weeks"] for d in week["contributionDays"]]
current = date.today().strftime("%Y-%m")
partial_first = days[0]["date"][:7] if not days[0]["date"].endswith("-01") else None
months = OrderedDict()
for day in days:
    key = day["date"][:7]
    if key in (current, partial_first):
        continue
    months[key] = months.get(key, 0) + day["contributionCount"]
months = list(months.items())[-12:]
total = sum(v for _, v in months)

RAINBOW = ["#FF5C5C", "#FF9F43", "#FECA57", "#1DD1A1", "#54A0FF", "#A66BFF"]

def mix(a, b, t):
    a, b = int(a[1:], 16), int(b[1:], 16)
    ch = [round(((a >> s) & 255) * (1 - t) + ((b >> s) & 255) * t) for s in (16, 8, 0)]
    return "#%02X%02X%02X" % tuple(ch)

def color(i, n):
    pos = i / max(n - 1, 1) * (len(RAINBOW) - 1)
    k = min(int(pos), len(RAINBOW) - 2)
    return mix(RAINBOW[k], RAINBOW[k + 1], pos - k)

W, H = 716, 300
top, base, left = 92, 250, 36
slot = (W - 2 * left) / len(months)
bw = slot * 0.62
peak = max(v for _, v in months) or 1

first, last = (date(int(k[:4]), int(k[5:]), 1) for k in (months[0][0], months[-1][0]))
label_range = f"{first:%b %Y} – {last:%b %Y}"

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
    f'aria-label="{total} contributions in the last year, by month">',
    "<style>.b{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);"
    "animation:g .9s cubic-bezier(.2,1,.3,1) forwards}@keyframes g{to{transform:scaleY(1)}}"
    ".v{opacity:0;animation:f .4s ease forwards}@keyframes f{to{opacity:1}}"
    '.h{font:700 18px "Segoe UI",Helvetica,Arial,sans-serif}.s{font:600 12px "Segoe UI",Helvetica,Arial,sans-serif}'
    "@media (prefers-reduced-motion:reduce){.b{animation:none;transform:none}.v{animation:none;opacity:1}}</style>",
    f'<rect width="{W}" height="{H}" rx="18" fill="#0d1117"/>',
    f'<text class="h" x="{left}" y="44" fill="#F0F6FC">Activity in the last 12 months</text>',
    f'<text class="s" x="{left}" y="66" fill="#8B949E">{total:,} contributions, including private work · {label_range}</text>',
]
for i, (key, value) in enumerate(months):
    h = (base - top) * value / peak
    x = left + i * slot + (slot - bw) / 2
    c = color(i, len(months))
    d = 0.06 * i
    label = date(int(key[:4]), int(key[5:]), 1).strftime("%b")
    parts.append(f'<rect class="b" style="animation-delay:{d:.2f}s" x="{x:.1f}" y="{base - h:.1f}" '
                 f'width="{bw:.1f}" height="{max(h, 2):.1f}" rx="6" fill="{c}"/>')
    parts.append(f'<text class="s v" style="animation-delay:{d + .5:.2f}s" x="{x + bw / 2:.1f}" y="{base - h - 8:.1f}" '
                 f'text-anchor="middle" fill="{c}">{value}</text>')
    parts.append(f'<text class="s" x="{x + bw / 2:.1f}" y="{base + 22}" text-anchor="middle" fill="#8B949E">{label}</text>')
parts.append("</svg>")

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w") as f:
    f.write("\n".join(parts))
print(f"wrote {OUT}: {total} contributions")
