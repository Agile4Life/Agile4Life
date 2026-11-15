"""Wide neofetch-style banner: animated colored-ASCII avatar (left) + info panel over matrix rain (right).
Regenerate after changing the GitHub avatar (macOS, no dependencies):
  curl -sL -o avatar.png "https://github.com/Agile4Life.png?size=460"
  sips -s format bmp -z 52 96 avatar.png --out small.bmp      # 52 rows x 96 columns of characters
  python3 scripts/ascii_avatar.py small.bmp assets/neofetch.svg"""
import random, struct, sys
from xml.sax.saxutils import escape

src, out = sys.argv[1], sys.argv[2]
d = open(src, "rb").read()
off, = struct.unpack_from("<I", d, 10)
w, h = struct.unpack_from("<ii", d, 18)
assert struct.unpack_from("<H", d, 28)[0] == 24 and h < 0, "expect 24-bit top-down BMP"
h = -h
stride = (w * 3 + 3) & ~3
px = [[tuple(d[off + y * stride + x * 3 + c] for c in (2, 1, 0)) for x in range(w)] for y in range(h)]

GROUPS = [" ", ".`'", ",:-", ";~^", "i!l/", "1t+?", "fcvx", "LCJY", "GOZX", "08&%", "@#WM"]
FRAMES = 3
CW, CH, FS = 6, 10.5, 10
PAD, BAR, GAP, PANEL = 20, 34, 28, 440
AW, AH = w * CW, h * CH                      # avatar block size
W, H = PAD + AW + GAP + PANEL + PAD, BAR + PAD * 2 + AH
PX = PAD + AW + GAP                          # panel x
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

random.seed(16)
palette = {}
lums = sorted((0.299 * r + 0.587 * g + 0.114 * b) / 255 for row in px for r, g, b in row)
LO, HI = lums[len(lums) // 20], lums[-len(lums) // 20]   # 5th/95th percentile: stretch contrast

def norm(rgb):
    r, g, b = rgb
    return min(1, max(0, ((0.299 * r + 0.587 * g + 0.114 * b) / 255 - LO) / (HI - LO)))

def color(rgb):
    k = (0.38 + 0.62 * norm(rgb)) * 255 / max(max(rgb), 1)
    q = tuple(min(255, round(c * k / 24) * 24) for c in rgb)
    return palette.setdefault(q, f"c{len(palette)}")

GLITCH = set(random.sample(range(h), 7))     # rows that jump sideways now and then

def frame():
    rows = []
    for y, row in enumerate(px):
        runs, cur, buf = [], None, ""
        for rgb in row:
            ch = random.choice(GROUPS[min(len(GROUPS) - 1, int(norm(rgb) * len(GROUPS)))])
            cls = color(rgb)
            if cls != cur and buf:
                runs.append(f'<tspan class="{cur}">{escape(buf)}</tspan>'); buf = ""
            cur = cls; buf += ch
        runs.append(f'<tspan class="{cur}">{escape(buf)}</tspan>')
        ty = BAR + PAD + (y + 0.8) * CH
        fx = (f'class="gl" style="animation-delay:{random.uniform(0, 5):.1f}s"' if y in GLITCH
              else f'class="wv" style="animation-delay:{y * -0.07:.2f}s"')
        rows.append(f'<text {fx} x="{PAD}" y="{ty:.1f}" textLength="{AW}" lengthAdjust="spacingAndGlyphs">{"".join(runs)}</text>')
    return "".join(rows)

frames = "".join(f'<g class="f f{i}">{frame()}</g>' for i in range(FRAMES))
css_colors = "".join(f".{n}{{fill:#{r:02x}{g:02x}{b:02x}}}" for (r, g, b), n in palette.items())
dur = 0.9
delays = "".join(f".f{i}{{animation-delay:{i * dur / FRAMES:.2f}s}}" for i in range(FRAMES))

# matrix rain behind the info panel: each column is drawn twice so translating by its height loops
RAIN = "01{}<>/=;#$%*+ｱｲｳｴｵｶｷｸｹｺ"
rain = []
for cx in range(PX, PX + PANEL, 16):
    n = int((H - BAR) / 14) + 1
    col = [random.choice(RAIN) for _ in range(n)]
    spans = "".join(f'<tspan x="{cx}" dy="14">{escape(c)}</tspan>' for c in col + col)
    rain.append(f'<text class="rain" y="{BAR - n * 14}" style="animation-duration:{random.uniform(5, 12):.1f}s;'
                f'animation-delay:-{random.uniform(0, 8):.1f}s;opacity:{random.uniform(.14, .34):.2f}">{spans}</text>')
RAIN_SHIFT = (int((H - BAR) / 14) + 1) * 14

INFO = [
    ("", "phong@github", "head"),
    ("", "-" * 30, "dim"),
    ("whoami", "Phong", ""),
    ("role", "Full-Stack Web Developer in progress", ""),
    ("focus", "practical features, clean UI", ""),
    ("loop", "build -> test -> iterate", ""),
    ("", "", ""),
    ("frontend", "React · TypeScript · Next.js", ""),
    ("backend", "Java · Node.js · Express", ""),
    ("database", "PostgreSQL · Supabase · MySQL", ""),
    ("testing", "Vitest · k6", ""),
    ("deploy", "Vercel · Docker · GitHub Actions", ""),
    ("ai", "Codex · Gemini · Claude", ""),
]
info, y0 = [], BAR + PAD + 60
for i, (k, v, cls) in enumerate(INFO):
    y = y0 + i * 30
    body = (f'<tspan class="key">{escape(k)}</tspan><tspan class="dim">: </tspan>{escape(v)}' if k else escape(v))
    info.append(f'<text class="info {cls}" x="{PX + 14}" y="{y}" style="animation-delay:{0.6 + i * 0.22:.2f}s">{body}</text>')
sw_y = y0 + len(INFO) * 30
swatches = "".join(
    f'<rect class="sw" x="{PX + 14 + i * 30}" y="{sw_y}" width="26" height="16" rx="3" fill="{c}" style="animation-delay:{i * .15:.2f}s"/>'
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f", "#36bcf7", "#8e75b2", "#f89820", "#2dd4bf", "#e6f4ff"]))
cur_y = sw_y + 44

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}" width="{W}" height="{H:.0f}" role="img" aria-label="Phong's avatar drawn in animated ASCII next to a terminal-style profile summary">
  <defs>
    <clipPath id="reveal"><rect x="0" y="{BAR}" width="{PAD + AW + GAP // 2}" height="0">
      <animate attributeName="height" dur="2.6s" calcMode="discrete" keyTimes="{";".join(f"{i / h:.4f}" for i in range(h + 1))}" values="{";".join(f"{PAD + (i + 1) * CH:.1f}" for i in range(h))};{H:.0f}" fill="freeze"/>
    </rect></clipPath>
    <clipPath id="frame"><rect width="{W}" height="{H:.0f}" rx="14"/></clipPath>
    <clipPath id="avatar"><rect x="0" y="{BAR}" width="{PAD + AW + GAP // 2}" height="{H:.0f}"/></clipPath>
    <clipPath id="panel"><rect x="{PX - GAP // 2}" y="{BAR}" width="{PANEL + PAD + GAP // 2}" height="{H:.0f}"/></clipPath>
    <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#36bcf7" stop-opacity="0"/><stop offset="1" stop-color="#36bcf7" stop-opacity=".22"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" x2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="fadeL" x1="0" x2="1">
      <stop offset="0" stop-color="#0b1220" stop-opacity=".0"/><stop offset=".25" stop-color="#0b1220" stop-opacity=".6"/><stop offset="1" stop-color="#0b1220" stop-opacity=".6"/>
    </linearGradient>
  </defs>
  <style>
    text{{font:{FS}px {MONO};white-space:pre}}
    .f{{opacity:0;animation:fr {dur}s steps(1) infinite}}
    @keyframes fr{{0%{{opacity:1}}{100 / FRAMES + .1:.1f}%{{opacity:0}}}}
    {delays}
    .wv{{animation:wv 4.2s ease-in-out infinite}}
    @keyframes wv{{0%,100%{{transform:translateX(-2.5px)}}50%{{transform:translateX(2.5px)}}}}
    .gl{{animation:gl 5s steps(1) infinite}}
    @keyframes gl{{0%,100%{{transform:none}}90%{{transform:translateX(-12px)}}93%{{transform:translateX(9px)}}96%{{transform:translateX(-4px)}}}}
    .beam{{animation:scan 4s linear infinite}}
    @keyframes scan{{from{{transform:translateY(-60px)}}to{{transform:translateY({H:.0f}px)}}}}
    .shine{{animation:shine 5.5s ease-in-out infinite}}
    @keyframes shine{{0%,35%{{transform:translateX(-260px) skewX(-18deg)}}100%{{transform:translateX({PAD + AW + 200}px) skewX(-18deg)}}}}
    .pulse{{animation:pulse 3.5s ease-in-out infinite}}
    @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.82}}}}
    .rain{{font:13px {MONO};fill:#36bcf7;animation:rain linear infinite}}
    @keyframes rain{{from{{transform:translateY(0)}}to{{transform:translateY({RAIN_SHIFT}px)}}}}
    .info{{font:14px {MONO};fill:#e6f4ff;opacity:0;animation:type .35s ease-out forwards}}
    @keyframes type{{from{{opacity:0;transform:translateX(-10px)}}to{{opacity:1;transform:none}}}}
    .head{{font-weight:700;font-size:18px;fill:#36bcf7}}
    .key{{fill:#f89820;font-weight:700}}
    .dim{{fill:#5b6b7f}}
    .sw{{animation:sw 2.4s ease-in-out infinite}}
    @keyframes sw{{0%,100%{{opacity:.55}}50%{{opacity:1}}}}
    .cursor{{animation:blink 1s steps(1) infinite}}
    @keyframes blink{{50%{{opacity:0}}}}
    .bar{{font:600 12px {MONO};fill:#8b949e}}
    {css_colors}
    @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.f0,.info{{opacity:1}}}}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H:.0f}" fill="#0b1220"/>
    <g clip-path="url(#panel)">{"".join(rain)}</g>
    <rect x="{PX - GAP // 2}" y="{BAR}" width="{PANEL + PAD + GAP // 2}" height="{H:.0f}" fill="url(#fadeL)"/>
    <g clip-path="url(#avatar)">
      <g class="pulse" clip-path="url(#reveal)">{frames}</g>
      <rect class="shine" x="0" y="{BAR}" width="180" height="{H:.0f}" fill="url(#shine)"/>
    </g>
    <line x1="{PX - GAP // 2}" y1="{BAR + 14}" x2="{PX - GAP // 2}" y2="{H - 14:.0f}" stroke="#36bcf7" stroke-opacity=".2"/>
    {"".join(info)}
    {swatches}
    <text class="info" x="{PX + 14}" y="{cur_y}" style="animation-delay:{0.6 + len(INFO) * 0.22:.2f}s"><tspan class="key">$</tspan> _</text>
    <rect class="beam" x="0" y="0" width="{W}" height="60" fill="url(#beam)"/>
    <rect width="{W}" height="{BAR}" fill="#161b22"/>
    <circle cx="20" cy="17" r="6" fill="#ff5f56"/><circle cx="40" cy="17" r="6" fill="#ffbd2e"/><circle cx="60" cy="17" r="6" fill="#27c93f"/>
    <text class="bar" x="84" y="21">phong@github:~$ ./avatar --ascii --neofetch</text>
    <rect class="cursor" x="402" y="10" width="7" height="14" fill="#36bcf7"/>
  </g>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1:.0f}" rx="14" fill="none" stroke="#36bcf7" stroke-opacity=".3"/>
</svg>
'''
open(out, "w", encoding="utf-8").write(svg)
print(f"{W}x{H:.0f}, {len(palette)} colors, {len(svg) // 1024} KB")
