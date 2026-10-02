"""Build the animated tech-stack grid (light and dark) from simple-icons logos.

Run locally when the stack changes: python3 scripts/tech_stack.py
"""
import os
import re
import urllib.request

ROWS = [
    ("Frontend &amp; Backend", "#FF5C5C", "#C93C3C", "#FFFFFF",
     [("typescript", "TypeScript"), ("react", "React"), ("nextdotjs", "Next.js"), ("expo", "RN / Expo"), ("nodedotjs", "Node.js")]),
    ("Data &amp; APIs", "#FF9F43", "#C2650F", "#FFFFFF",
     [("postgresql", "PostgreSQL"), ("prisma", "Prisma"), ("drizzle", "Drizzle"), ("zod", "Zod"), ("openapiinitiative", "OpenAPI")]),
    ("Payments", "#F2B200", "#9A6B00", "#FFFFFF",
     [("stripe", "Stripe"), ("paypal", "PayPal"), (None, "Lightning")]),
    ("Quality &amp; DevOps", "#1DD1A1", "#0B8A68", "#FFFFFF",
     [("vitest", "Vitest"), ("jest", "Jest"), ("githubactions", "Actions"), ("vercel", "Vercel"), ("cloudflare", "Cloudflare"), ("amazonwebservices", "AWS")]),
    ("AI", "#54A0FF", "#1F6FD1", "#FFFFFF",
     [("claude", "Claude Code"), ("openai", "Codex"), ("modelcontextprotocol", "MCP")]),
    ("Tools", "#A66BFF", "#7A3FD9", "#FFFFFF",
     [("github", "GitHub"), ("linear", "Linear"), ("jira", "Jira"), ("notion", "Notion"), ("figma", "Figma")]),
]
# simple-icons has no Lightning Network logo ("lightning" is Lightning AI), so draw a bolt.
BOLT = "M13.5 1.5 4 13.5h6.5L9 22.5l10-12.5h-6.6z"
THEMES = {
    "tech-stack.svg": {"bg": "#FFFFFF", "dark": False},
    "tech-stack-dark.svg": {"bg": "#0D1117", "dark": True},
}
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")


def icon_path(slug):
    if slug is None:
        return BOLT
    url = f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{slug}.svg"
    svg = urllib.request.urlopen(url).read().decode()
    return re.search(r'<path d="([^"]+)"', svg).group(1)


paths = {slug: icon_path(slug) for *_, items in ROWS for slug, _ in items}

T, G, LX, TX, RH, TOP = 72, 12, 24, 200, 96, 28
W = TX + 6 * (T + G) + 12
H = TOP + len(ROWS) * RH + 8

for name, theme in THEMES.items():
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Tech stack">',
        "<style>.t{opacity:0;animation:pop .5s cubic-bezier(.2,1.4,.4,1) forwards}"
        "@keyframes pop{0%{opacity:0;transform:scale(.4)}100%{opacity:1;transform:scale(1)}}"
        '.r{font:700 15px "Segoe UI",Helvetica,Arial,sans-serif}'
        '.l{font:600 10px "Segoe UI",Helvetica,Arial,sans-serif;text-anchor:middle}'
        "@media (prefers-reduced-motion:reduce){.t{animation:none;opacity:1}}</style>",
        f'<rect width="{W}" height="{H}" rx="18" fill="{theme["bg"]}"/>',
    ]
    i = 0
    for r, (label, tile, text_on_light, fg, items) in enumerate(ROWS):
        y = TOP + r * RH
        out.append(f'<text class="r" x="{LX}" y="{y + T / 2 + 5}" fill="{tile if theme["dark"] else text_on_light}">{label}</text>')
        for c, (slug, name_label) in enumerate(items):
            x = TX + c * (T + G)
            out.append(
                f'<g transform="translate({x},{y})"><g class="t" style="animation-delay:{0.08 * i:.2f}s;transform-origin:{T / 2}px {T / 2}px">'
                f'<rect width="{T}" height="{T}" rx="16" fill="{tile}"/>'
                f'<svg x="{(T - 30) / 2}" y="11" width="30" height="30" viewBox="0 0 24 24"><path d="{paths[slug]}" fill="{fg}"/></svg>'
                f'<text class="l" x="{T / 2}" y="{T - 12}" fill="{fg}">{name_label}</text></g></g>'
            )
            i += 1
    out.append("</svg>")
    with open(os.path.join(OUT_DIR, name), "w") as f:
        f.write("\n".join(out))
    print(f"wrote assets/{name}")
