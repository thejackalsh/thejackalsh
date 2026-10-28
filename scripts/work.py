#!/usr/bin/env python3
"""
Render the Selected Work table as animated SVGs (README markdown tables can't animate):
assets/work-dark.svg + assets/work-light.svg. Icons are reused from assets/stack-dark.svg.
Stdlib only. Edit WORK below, then:  python3 scripts/work.py
"""
import os
import re
import textwrap
from xml.sax.saxutils import escape

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
A = os.path.join(ROOT, "assets")

# (name, kind, about, stack)
WORK = [
    ("Transport ERP", "Freelance",
     "Replaces a legacy Windows app for a freight company: waybills, invoicing, general journal and ledger, "
     "vehicle expenses, spare parts, driver commissions, role-based access per module",
     ["Laravel", "MySQL", "Leaflet"]),
    ("Driver App", "Freelance",
     "Android app for tracking, waybills, targets, commissions and balances, synced with the web system",
     ["React Native", "Expo"]),
    ("Quiz Maker LMS", "Contract, led team of 3",
     "Teachers upload materials, AI generates exam questions, AI summarizes each student's understanding",
     ["Next.js", "shadcn", "Go", "FastAPI", "Figma", "PostgreSQL", "Supabase"]),
    ("Sales & Finance ERP", "Contract",
     "Master data, role management, installment payments with history, sales and financial reports",
     ["Laravel", "MySQL"]),
    ("Elior", "Open source",
     "Assistive app for visually impaired users: money, object and read modes. "
     "On-device rupiah recognition, OCR, cloud vision",
     ["React Native", "Expo", "Go", "Gin", "PostgreSQL", "FastAPI", "Docker"]),
    ("Prita Bali Nanny", "Client",
     "Bilingual EN/ID marketing site, bookings go straight to WhatsApp",
     ["Next.js", "React", "TypeScript"]),
]

THEMES = {
    "dark":  {"fg": "#ffffff", "mute": "#8b949e", "line": "#30363d"},
    "light": {"fg": "#000000", "mute": "#57606a", "line": "#d0d7de"},
}
W = 800
PX, AX, SX = 40, 260, 590     # column x: project / about / stack
FONT = "Consolas, 'Courier New', monospace"
# ponytail: wrap by char count, assumes ~7.8px/char mono at 13px; overflows if viewer falls back to a wide font
ABOUT_CH, STACK_CH = 40, 26


def icons():
    s = open(os.path.join(A, "stack-dark.svg"), encoding="utf-8").read()
    return {name: d for d, name in re.findall(r'<path [^>]*d="([^"]+)"[^>]*/><text[^>]*>([^<]+)</text>', s)}


def render(theme, icon):
    th = THEMES[theme]
    css = (f".lbl{{fill:{th['mute']};font-size:12px;letter-spacing:2px}}"
           f".name{{fill:{th['fg']};font-size:15px;font-weight:700}}"
           f".kind{{fill:{th['mute']};font-size:11px;letter-spacing:1px}}"
           f".about{{fill:{th['fg']};font-size:13px}}"
           f".st{{fill:{th['mute']};font-size:11px}}"
           f".ln{{stroke:{th['line']};stroke-width:1}}"
           # same pop-in as stack.svg: each piece one by one, left->right, top->bottom
           ".a{opacity:0;animation:drop .35s cubic-bezier(.2,.8,.2,1) both}"
           "@keyframes drop{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:none}}"
           "@media (prefers-reduced-motion:reduce){.a{animation:none!important;opacity:1!important;transform:none!important}}")
    items = [f'<text class="lbl" x="{PX}" y="20">PROJECT</text>', f'<text class="lbl" x="{AX}" y="20">ABOUT</text>',
             f'<text class="lbl" x="{SX}" y="20">STACK</text>', f'<line class="ln" x1="{PX}" x2="{W - PX}" y1="34" y2="34"/>']
    y = 34
    for name, kind, about, stack in WORK:
        top = y + 18
        about_l = textwrap.wrap(about, ABOUT_CH, break_on_hyphens=False)
        stack_l = textwrap.wrap(" · ".join(stack), STACK_CH)
        items.append(f'<text class="name" x="{PX}" y="{top + 14}">{escape(name)}</text>'
                     f'<text class="kind" x="{PX}" y="{top + 34}">{escape(kind.upper())}</text>')
        items.append("".join(f'<text class="about" x="{AX}" y="{top + 13 + j*19}">{escape(l)}</text>'
                             for j, l in enumerate(about_l)))
        ix = SX
        for s in stack:
            if s in icon:  # no icon (shadcn, Gin) -> name only, listed below
                items.append(f'<path transform="translate({ix} {top}) scale(0.75)" d="{icon[s]}" fill="{th["fg"]}"><title>{s}</title></path>')
                ix += 24
        items.append("".join(f'<text class="st" x="{SX}" y="{top + 36 + j*15}">{escape(l)}</text>'
                             for j, l in enumerate(stack_l)))
        y = top + max(34, 13 + 19 * (len(about_l) - 1), 36 + 15 * (len(stack_l) - 1)) + 18
        items.append(f'<line class="ln" x1="{PX}" x2="{W - PX}" y1="{y}" y2="{y}"/>')
    body = [f'<g class="a" style="animation-delay:{n*0.04:.2f}s">{it}</g>' for n, it in enumerate(items)]
    h = y + 4
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" '
            f'aria-label="Selected work: {escape(", ".join(w[0] for w in WORK))}" font-family="{FONT}">'
            f"<title>Selected work</title><style>{css}</style>" + "".join(body) + "</svg>")


if __name__ == "__main__":
    icon = icons()
    missing = {s for w in WORK for s in w[3]} - icon.keys()
    for t in THEMES:
        with open(os.path.join(A, f"work-{t}.svg"), "w", encoding="utf-8") as f:
            f.write(render(t, icon))
    print(f"wrote work-dark.svg + work-light.svg (no icon: {', '.join(sorted(missing)) or '-'})")
