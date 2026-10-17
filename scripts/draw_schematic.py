#!/usr/bin/env python3
"""Draw the circuit schematic for the README.

Writes schematic/current_sense.svg and schematic/current_sense.png.
Usage:  python3 scripts/draw_schematic.py      (needs schemdraw, matplotlib)
"""
from pathlib import Path

import schemdraw
import schemdraw.elements as elm

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "schematic"

schemdraw.config(fontsize=13, lw=1.6, bgcolor="white", margin=0.4)

with schemdraw.Drawing(show=False) as d:
    # ---- Op-amp: non-inverting input on top ----
    # After flip(), in2 is the top (+) input and in1 the bottom (−) input.
    op = elm.Opamp(leads=True).flip().at((8, 0)).anchor("center")
    elm.Label().at((op.center[0] - 0.3, op.center[1] + 1.6)).label("U1  (0–5 V supply)")

    # ---- Sense node and shunt ----
    elm.Line().left(2.5).at(op.in2)
    sense = d.here
    elm.Dot().label("sense", loc="top")
    elm.Resistor().down(3).label(("Rsense", "0.1 Ω"), loc="bottom")
    elm.Ground()

    # ---- Load current source ----
    elm.Line().left(3).at(sense)
    elm.SourceI().down(3).reverse().label(("I1", "0–2 A load"), loc="top")
    elm.Ground()

    # ---- Feedback network on the inverting input ----
    elm.Line().left(0.75).at(op.in1)
    elm.Line().down(2.2)
    fb = d.here
    elm.Dot()
    elm.Resistor().down(2).label(("Rg", "1 kΩ"), loc="bottom")
    elm.Ground()
    elm.Resistor().right().at(fb).tox(op.out[0] + 1).label("Rf  9 kΩ", loc="bottom")
    elm.Line().up().toy(op.out)
    out = d.here
    elm.Dot()
    elm.Line().left().to(op.out)
    elm.Line().right(1.5).at(out)
    elm.Dot(open=True).label("Vout\n(1 V/A)", loc="right")

    d.save(str(OUT / "current_sense.svg"))
    d.save(str(OUT / "current_sense.png"), dpi=200)

# Flatten the PNG onto white so it stays readable in GitHub's dark theme
from PIL import Image

png = OUT / "current_sense.png"
img = Image.open(png).convert("RGBA")
flat = Image.new("RGB", img.size, "white")
flat.paste(img, mask=img.split()[3])
flat.save(png)

print("Wrote schematic/current_sense.svg and .png")
