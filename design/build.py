"""Build the Hark-style profile artwork (light + dark SVGs) into assets/.

Design system: SixthSense docs/design (Hark-inspired) - soft sky atmosphere,
Instrument Serif wordmark, Geist text, Geist Mono data, dark pills,
big rounded cards, borders over shadows, colour only for meaning.

Fonts are subset per SVG and embedded, because GitHub serves README images
without access to external fonts.  Run:  python3 design/build.py
"""
import base64, io, os
from html import escape
from fontTools.ttLib import TTFont
from fontTools import subset

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "..", "assets")
FONT_FILES = {
    "serif": "instrument-serif-latin-400-normal.woff2",
    "serif-i": "instrument-serif-latin-400-italic.woff2",
    "sans": "geist-sans-latin-400-normal.woff2",
    "sans-m": "geist-sans-latin-500-normal.woff2",
    "mono": "geist-mono-latin-400-normal.woff2",
}
FAMILY = {"serif": ("Instrument Serif", "normal", 400), "serif-i": ("Instrument Serif", "italic", 400),
          "sans": ("Geist", "normal", 400), "sans-m": ("Geist", "normal", 500), "mono": ("Geist Mono", "normal", 400)}
FONTS = {k: TTFont(os.path.join(ROOT, "fonts", v)) for k, v in FONT_FILES.items()}

T = {  # tokens from sixthsense/docs/design/tokens.json
    "light": dict(ground="#f9f9fa", surface="#ffffff", sunk="#efefec", ink="#141414", muted="#5c6273",
                  hairline="#e3e4e8", sky100="#f3f5fa", sky300="#c9d4e6", slate="#636e86", onink="#ffffff",
                  pill="#141414", truth="#1f7a55", deep="#3f6c9f", mid="#8fb0d3", haze="#dfe8f1",
                  dusk1="#e9a77c", dusk2="#f6e1cf", lav1="#8e86c4", lav2="#e4e0f3",
                  glass="rgba(255,255,255,0.72)", hero_text="#ffffff", panel_text="#141414"),
    "dark": dict(ground="#0f1012", surface="#17181b", sunk="#1e1f24", ink="#f3f4f6", muted="#9aa2b4",
                 hairline="#2a2c33", sky100="#151a25", sky300="#2a3550", slate="#8994aa", onink="#141414",
                 pill="#f3f4f6", truth="#4fcf98", deep="#1b2c44", mid="#2a4060", haze="#151a25",
                 dusk1="#7a4a33", dusk2="#2e231d", lav1="#3c3762", lav2="#1f1d30",
                 glass="rgba(23,24,27,0.72)", hero_text="#f3f4f6", panel_text="#f3f4f6"),
}


def width(text, font, size, tracking=0.0):
    f = FONTS[font]
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    w = sum(hmtx[cmap.get(ord(c), cmap.get(32))][0] for c in text)
    return w * size / upm + tracking * size * max(len(text) - 1, 0)


def wrap(text, font, size, maxw):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if width(trial, font, size) > maxw and cur:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur] if cur else lines


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title, self.parts, self.used, self.css = w, h, title, [], {}, ""

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, font, size, fill, anchor="start", tracking=0, opacity=1, cls=""):
        self.used.setdefault(font, set()).update(s)
        fam, style, weight = FAMILY[font]
        ls = f' letter-spacing="{tracking * size:.2f}"' if tracking else ""
        op = f' opacity="{opacity}"' if opacity != 1 else ""
        c = f' class="{cls}"' if cls else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-style="{style}" font-weight="{weight}" '
                 f'font-size="{size}" fill="{fill}" text-anchor="{anchor}"{ls}{op}{c}>{escape(s)}</text>')

    def runs(self, x, y, runs, size, fill, anchor="start"):
        """Mixed upright/italic serif on one line, e.g. wordmarks."""
        total = sum(width(t, f, size) for t, f in runs)
        cx = x - total / 2 if anchor == "middle" else x
        for t, f in runs:
            self.text(cx, y, t, f, size, fill)
            cx += width(t, f, size)

    def render(self):
        faces = []
        for font, chars in self.used.items():
            opts = subset.Options()
            opts.flavor, opts.layout_features, opts.name_IDs = "woff2", ["kern", "liga"], ["*"]
            sub = subset.Subsetter(opts)
            sub.populate(text="".join(sorted(chars)) + " ")
            f = TTFont(os.path.join(ROOT, "fonts", FONT_FILES[font]))
            sub.subset(f)
            buf = io.BytesIO()
            f.flavor = "woff2"
            f.save(buf)
            fam, style, weight = FAMILY[font]
            faces.append(f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
                         f"src:url(data:font/woff2;base64,{base64.b64encode(buf.getvalue()).decode()}) format('woff2');}}")
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
                f'role="img" aria-label="{escape(self.title)}"><title>{escape(self.title)}</title>'
                f'<style>{"".join(faces)}{self.css}</style>{"".join(self.parts)}</svg>')


def save(name, theme, svg):
    with open(os.path.join(OUT, f"{name}-{theme}.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg.render())


def pill(s, x, y, label, c, kind="hairline", font="sans-m", size=13, h=30, pad=14, dot=None, tracking=0.0):
    w = width(label, font, size, tracking) + pad * 2 + (14 if dot else 0)
    fill = {"ink": c["pill"], "glass": c["glass"], "hairline": "none", "sunk": c["sunk"]}[kind]
    stroke = f' stroke="{c["hairline"]}"' if kind in ("hairline", "sunk") else ""
    s.add(f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{fill}"{stroke}/>')
    tx = x + pad
    if dot:
        s.add(f'<circle cx="{x + pad + 3}" cy="{y + h / 2}" r="3.5" fill="{dot}"/>')
        tx += 14
    s.text(tx, y + h / 2 + size * 0.36, label, font, size, c["onink"] if kind == "ink" else c["ink"], tracking=tracking)
    return w


def atmosphere(s, gid, top, mid, bottom, x, y, w, h, r):
    s.add(f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
          f'<stop offset="0.55" stop-color="{mid}"/><stop offset="1" stop-color="{bottom}"/></linearGradient></defs>'
          f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#{gid})"/>')


# ---------------------------------------------------------------- components
def hero(theme):
    c = T[theme]
    s = Svg(880, 330, "Dinesh Potluru - Applied AI and Forward Deployed Engineer, London")
    atmosphere(s, "sky", c["deep"], c["mid"], c["haze"], 0, 0, 880, 330, 26)
    sun, op = (c["dusk2"], 0.55) if theme == "light" else (c["dusk1"], 0.35)
    s.add(f'<defs><radialGradient id="sun" cx="0.82" cy="1.05" r="0.55"><stop offset="0" stop-color="{sun}" stop-opacity="{op}"/>'
          f'<stop offset="1" stop-color="{sun}" stop-opacity="0"/></radialGradient></defs>'
          f'<rect width="880" height="330" rx="26" fill="url(#sun)"/>')
    pill(s, 40, 34, "OPEN TO APPLIED AI AND FDE ROLES", c, "glass", size=11.5, h=28, dot=c["truth"], tracking=0.04)
    s.runs(40, 152, [("Dinesh ", "serif"), ("Potluru", "serif-i")], 78, c["hero_text"])
    lines = ["I put AI agents into real products.",
             "I sit with the customer, find the real problem, and ship the fix.",
             "LangChain, LangGraph, RAG and evals, from spec to production.",
             "Aerospace engineer turned CTO turned Applied AI engineer."]
    n, dur = len(lines), 4.5
    s.css = (f"@keyframes fade{{0%{{opacity:0}}3%{{opacity:1}}{100 / n - 3:.1f}%{{opacity:1}}{100 / n:.1f}%{{opacity:0}}100%{{opacity:0}}}}"
             f".r{{opacity:0;animation:fade {n * dur}s ease-out infinite}}"
             + "".join(f".r{i}{{animation-delay:{i * dur}s}}" for i in range(n))
             + "@media (prefers-reduced-motion:reduce){.r{animation:none}.r0{opacity:1}}")
    for i, line in enumerate(lines):
        s.text(42, 196, line, "sans", 19, c["hero_text"], opacity=0.92, cls=f"r r{i}")
    x = 40
    for chip in ["Forward Deployed Engineering", "AI agents", "RAG and evals", "Next.js · TypeScript · Python", "London"]:
        x += pill(s, x, 264, chip, c, "glass", font="sans", size=13, h=32) + 8
    return s


def link_pill(theme, label, kind):
    c = T[theme]
    w = width(label, "sans-m", 14) + 36 + 18
    s = Svg(int(w) + 2, 42, label)
    if kind == "ink":
        s.add(f'<rect x="1" y="1" width="{w:.1f}" height="40" rx="20" fill="{c["pill"]}"/>')
        col = c["onink"]
    else:
        s.add(f'<rect x="1.5" y="1.5" width="{w - 1:.1f}" height="39" rx="19.5" fill="none" stroke="{c["hairline"]}" stroke-width="1"/>')
        col = c["ink"]
    s.text(19, 26, label, "sans-m", 14, col)
    ax = 19 + width(label, "sans-m", 14) + 8
    s.add(f'<path d="M{ax} 25 L{ax + 7} 18 M{ax + 2} 18 L{ax + 7} 18 L{ax + 7} 23" fill="none" stroke="{col}" '
          f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>')
    return s


def section(theme, num, kicker, title_runs):
    c = T[theme]
    s = Svg(880, 84, " ".join(t for t, _ in title_runs))
    s.text(0, 24, f"{num} · {kicker.upper()}", "sans-m", 12, c["muted"], tracking=0.08)
    s.runs(0, 70, title_runs, 40, c["ink"])
    return s


def card(s, c, x, y, w, h, r=26):
    s.add(f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" rx="{r}" fill="{c["surface"]}" stroke="{c["hairline"]}"/>')


STACK = [("Languages", ["TypeScript", "JavaScript", "Python", "Java", "SQL", "Bash"]),
         ("Frontend", ["React", "Next.js", "Tailwind CSS", "Vite"]),
         ("Backend and data", ["Node.js", "Express", "FastAPI", "Django", "PostgreSQL", "Redis", "Supabase"]),
         ("AI and agents", ["LangChain", "LangGraph", "Claude Code", "MCP", "RAG", "Evals", "Vercel AI SDK", "n8n"]),
         ("Cloud and tooling", ["Vercel", "Docker", "GitHub Actions", "Git", "Linux", "Obsidian"])]


def stack(theme):
    c = T[theme]
    rows, y = [], 26
    for label, items in STACK:  # lay out pills, wrapping inside the card
        x, line, placed = 212, 0, []
        for it in items:
            w = width(it, "sans", 13) + 26
            if x + w > 848:
                x, line = 212, line + 1
            placed.append((x, y + line * 38, it))
            x += w + 8
        rows.append((label, y, placed))
        y += 52 + line * 38
    s = Svg(880, y + 14, "Tech stack")
    card(s, c, 0, 0, 880, s.h)
    for i, (label, ry, placed) in enumerate(rows):
        s.text(32, ry + 20, label.upper(), "sans-m", 11.5, c["muted"], tracking=0.06)
        for x, py, it in placed:
            pill(s, x, py, it, c, "sunk" if label == "AI and agents" else "hairline", font="sans", size=13, h=30, pad=13)
        if i < len(rows) - 1:
            ny = rows[i + 1][1]
            s.add(f'<line x1="32" y1="{ny - 9}" x2="848" y2="{ny - 9}" stroke="{c["hairline"]}"/>')
    return s


PROJECTS = [
    ("sixthsense", "VIDEO AGENT · VAST HACK 2026", [("Sixth", "serif"), ("Sense", "serif-i")], "sky",
     "Every London bus, a second pair of eyes. It predicts what happens next on bus CCTV, grades itself on the next clip and flags near misses.",
     "Python · FastAPI · Next.js · YOLO11"),
    ("jev-tokensaver", "DEVELOPER TOOL · MCP", [("Jev ", "serif"), ("token saver", "serif-i")], "dusk",
     "AI coding agents waste tokens reading huge logs. Jev pre-reads them and hands over only the lines that matter. Fail-open and secrets-scrubbed.",
     "Python · MCP · CLI"),
    ("superteams", "AGENT WORKSPACE", [("Super", "serif"), ("teams", "serif-i")], "lav",
     "One multi-tenant workspace where small agencies run clients, tasks and notes, with AI agents built in.",
     "Next.js · TypeScript · React"),
    ("nextjs-agent-starter", "TEMPLATE", [("Agent ", "serif"), ("starter", "serif-i")], "slate",
     "Skip the boilerplate. Next.js 16 and React 19 with agent scaffolding, secrets management and provider switching, ready to go.",
     "Next.js · TypeScript · Tailwind"),
]


def project(theme, p):
    c = T[theme]
    repo, label, title, atmo, body, tech = p
    grads = {"sky": (c["deep"], c["mid"], c["haze"]), "dusk": (c["dusk1"], c["dusk1"], c["dusk2"]),
             "lav": (c["lav1"], c["lav1"], c["lav2"]), "slate": (c["slate"], c["sky300"], c["sky100"])}
    body_lines = wrap(body, "sans", 14.5, 370)
    h = 214 + 22 * 4 + 76
    s = Svg(430, h, f"{''.join(t for t, _ in title)} - {body}")
    card(s, c, 0, 0, 430, h)
    atmosphere(s, f"g{atmo}", *grads[atmo], 10, 10, 410, 190, 20)
    pill(s, 26, 28, label, c, "glass", size=11, h=26, pad=12, tracking=0.05)
    s.runs(28, 178, title, 46, c["panel_text"])
    for i, line in enumerate(body_lines):
        s.text(28, 234 + i * 22, line, "sans", 14.5, c["muted"])
    s.text(28, h - 44, tech, "mono", 12, c["muted"])
    w = width("View repo", "sans-m", 13) + 40
    s.add(f'<rect x="{402 - w:.1f}" y="{h - 63}" width="{w:.1f}" height="32" rx="16" fill="{c["pill"]}"/>')
    s.text(402 - w + 14, h - 42.5, "View repo", "sans-m", 13, c["onink"])
    ax = 402 - 14 - 8
    s.add(f'<path d="M{ax - 1} {h - 43} L{ax + 5} {h - 49} M{ax} {h - 49} L{ax + 5} {h - 49} L{ax + 5} {h - 44}" fill="none" '
          f'stroke="{c["onink"]}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>')
    return s


def steps(theme, title, items, loop_note=None, now_last=False):
    c = T[theme]
    n = len(items)
    colw = (880 - 64) / n
    s = Svg(880, 262 if loop_note else 232, title)
    card(s, c, 0, 0, 880, s.h)
    line_y = 82
    s.add(f'<line x1="{32 + 6}" y1="{line_y}" x2="{32 + colw * (n - 1) + 6}" y2="{line_y}" stroke="{c["hairline"]}" stroke-width="1.5"/>')
    for i, (kick, head, body) in enumerate(items):
        x = 32 + i * colw
        s.text(x, 52, kick, "mono", 12, c["muted"])
        last = now_last and i == n - 1
        if last:
            s.add(f'<circle cx="{x + 6}" cy="{line_y}" r="10" fill="none" stroke="{c["slate"]}" stroke-opacity="0.45"/>')
        s.add(f'<circle cx="{x + 6}" cy="{line_y}" r="5.5" fill="{c["ink"] if last else c["surface"]}" stroke="{c["ink"] if last else c["slate"]}" stroke-width="1.5"/>')
        s.runs(x, 130, [(head, "serif")], 27 if n > 5 else 25, c["ink"])
        for j, line in enumerate(wrap(body, "sans", 13, colw - 22)):
            s.text(x, 158 + j * 19, line, "sans", 13, c["muted"])
    if loop_note:
        x1, x2, y = 32 + colw * (n - 1) + 6, 32 + colw + 6, 222
        s.add(f'<path d="M{x1} {y - 14} Q{x1} {y + 6} {x1 - 24} {y + 6} L{x2 + 24} {y + 6} Q{x2} {y + 6} {x2} {y - 14}" fill="none" '
              f'stroke="{c["slate"]}" stroke-width="1.5" stroke-dasharray="4 5" stroke-linecap="round"/>'
              f'<path d="M{x2 - 5} {y - 8} L{x2} {y - 15} L{x2 + 5} {y - 8}" fill="none" stroke="{c["slate"]}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>')
        tw = width(loop_note, "mono", 12) + 20
        mx = (x1 + x2) / 2
        s.add(f'<rect x="{mx - tw / 2:.1f}" y="{y - 5}" width="{tw:.1f}" height="22" rx="11" fill="{c["surface"]}"/>')
        s.text(mx, y + 10, loop_note, "mono", 12, c["muted"], anchor="middle")
    return s


def footer(theme):
    c = T[theme]
    s = Svg(880, 270, "Building with AI agents? Let's talk. Email Dinesh")
    atmosphere(s, "dusk", c["dusk1"], c["dusk1"] if theme == "dark" else "#efc4a5", c["dusk2"], 0, 0, 880, 270, 26)
    s.runs(440, 102, [("Building with AI agents? ", "serif"), ("Let's talk.", "serif-i")], 44, c["panel_text"], anchor="middle")
    s.text(440, 140, "Calm, capable engineering, from the first customer call to production.", "sans", 16, c["panel_text"], anchor="middle", opacity=0.78)
    label = "dineshiitb.ae18@gmail.com"
    w = width(label, "sans-m", 14) + 40
    s.add(f'<rect x="{440 - w / 2:.1f}" y="170" width="{w:.1f}" height="42" rx="21" fill="{c["pill"]}"/>')
    s.text(440, 196, label, "sans-m", 14, c["onink"], anchor="middle")
    return s


SHIP = [("01", "Listen", "Sit with the user and find the real problem"),
        ("02", "Scope", "Write the spec and agree what success means"),
        ("03", "Build", "Agent, tools, RAG and the right context"),
        ("04", "Measure", "Evals and guardrails, so we know, not guess"),
        ("05", "Ship", "CI/CD, observability and a careful rollout"),
        ("06", "Learn", "Watch real usage, then go round again")]
JOURNEY = [("2011 - 2015", "IIT Bombay", "BTech Aerospace Engineering"),
           ("2015 - 2017", "TeachCoder", "Co-founder"),
           ("2017 - now", "PiAcademy", "CTO and full stack engineer, edtech, London"),
           ("2019 - 2020", "Middlesex", "MS Digital Marketing"),
           ("2026", "Applied AI", "Agents, hackathons and open source")]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for th in ("light", "dark"):
        save("hero", th, hero(th))
        save("stack", th, stack(th))
        save("ship", th, steps(th, "How I ship AI to customers", SHIP, loop_note="learn, then scope again"))
        save("journey", th, steps(th, "Journey", JOURNEY, now_last=True))
        save("footer", th, footer(th))
        for name, label, kind in [("link-portfolio", "Portfolio", "ink"), ("link-linkedin", "LinkedIn", "line"),
                                  ("link-x", "X", "line"), ("link-email", "Email", "line")]:
            save(name, th, link_pill(th, label, kind))
        for p in PROJECTS:
            save(f"project-{p[0]}", th, project(th, p))
        for num, kick, runs in [("01", "About", [("A little ", "serif"), ("about me", "serif-i")]),
                                ("02", "Stack", [("Tools I ", "serif"), ("reach for", "serif-i")]),
                                ("03", "Selected work", [("Things I've ", "serif"), ("shipped", "serif-i")]),
                                ("04", "Process", [("How I ship AI to ", "serif"), ("customers", "serif-i")]),
                                ("05", "Journey", [("How I ", "serif"), ("got here", "serif-i")]),
                                ("06", "By the numbers", [("Code, ", "serif"), ("measured", "serif-i")]),
                                ("07", "Recent activity", [("What I'm ", "serif"), ("working on", "serif-i")])]:
            save(f"section-{num}", th, section(th, num, kick, runs))
    print("\n".join(sorted(os.listdir(OUT))))
