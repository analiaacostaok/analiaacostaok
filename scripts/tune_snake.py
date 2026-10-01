"""Tune the generated snake: remove the progress bar, crop empty space, speed up the loop."""
import re
import sys

SPEED = 2  # 2 = the snake loop takes half the time

for path in sys.argv[1:]:
    svg = open(path).read()
    svg = re.sub(r'<rect class="u [^"]*"[^>]*/>', "", svg)

    old_box = re.search(r'viewBox="([^"]+)"', svg).group(1)
    vx, vy, vw, vh = (float(n) for n in old_box.split())
    bottom = max(float(y) for y in re.findall(r'<rect class="c[^"]*"[^>]*?y="([\d.]+)"', svg)) + 12
    new_h = bottom + 16 - vy
    svg = svg.replace(f'viewBox="{old_box}"', f'viewBox="{vx:g} {vy:g} {vw:g} {new_h:g}"', 1)
    svg = re.sub(r'(<svg[^>]*?)height="[\d.]+"', rf'\g<1>height="{new_h:g}"', svg, count=1)

    svg = re.sub(r"(\d+)ms", lambda m: f"{round(int(m.group(1)) / SPEED)}ms", svg)

    open(path, "w").write(svg)
    print(f"tuned {path}: height {vh:g} -> {new_h:g}, {SPEED}x speed")
