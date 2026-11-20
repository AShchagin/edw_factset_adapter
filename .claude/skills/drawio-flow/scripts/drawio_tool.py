#!/usr/bin/env python3
"""Build and inspect draw.io (.drawio) diagrams in the team's flow style.

  python3 drawio_tool.py build SPEC.json OUT.drawio [--allow-overlap]
  python3 drawio_tool.py inspect FILE.drawio

Build turns a small JSON spec into an uncompressed .drawio file with the team
style and the standard A4 page, then checks it. Inspect lists the boxes and
connectors of a .drawio file, including files whose diagram data is compressed.
Python standard library only.
"""
import argparse
import base64
import html
import itertools
import json
import math
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zlib

NODE_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;arcSize=22;fillColor=#E6F1FB;strokeColor=#B5D4F4;"
    "fontColor=#0C447C;fontStyle=1;fontSize=13;fontFamily=Segoe UI;"
)
DASHED_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;arcSize=22;fillColor=#F5FAFE;strokeColor=#B5D4F4;"
    "dashed=1;dashPattern=4 3;fontColor=#0C447C;fontStyle=1;fontSize=13;fontFamily=Segoe UI;"
)
EDGE_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;endSize=6;"
    "strokeColor=#8B95A1;strokeWidth=1;"
)
EDGE_LABEL_STYLE = (
    "fontSize=11;fontFamily=Segoe UI;fontColor=#44546A;labelBackgroundColor=#FFFFFF;"
    "labelBorderColor=#CFD6DD;"
)
A4_PORTRAIT = (827, 1169)
DEFAULT_BOX = (200, 60)


def fmt(value):
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "diagram"


def build(spec, allow_overlap=False):
    problems = []
    page = spec.get("page", {})
    page_w = page.get("width", A4_PORTRAIT[0])
    page_h = page.get("height", A4_PORTRAIT[1])
    name = spec.get("name", "Diagram")

    nodes = spec.get("nodes", [])
    edges = spec.get("edges", [])
    ids = [n.get("id") for n in nodes]
    if len(set(ids)) != len(ids):
        problems.append("node ids are not unique")
    boxes = {}
    for n in nodes:
        for key in ("id", "label", "x", "y"):
            if key not in n:
                problems.append("node %r is missing %r" % (n.get("id"), key))
        w = n.get("w", DEFAULT_BOX[0])
        h = n.get("h", DEFAULT_BOX[1])
        if "x" in n and "y" in n:
            boxes[n.get("id")] = (n["x"], n["y"], w, h)
    for i, e in enumerate(edges, 1):
        for end in ("from", "to"):
            if e.get(end) not in boxes:
                problems.append("edge %d: %r is not a node" % (i, e.get(end)))
    if not allow_overlap:
        for a, b in itertools.combinations(boxes, 2):
            ax, ay, aw, ah = boxes[a]
            bx, by, bw, bh = boxes[b]
            if not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay):
                problems.append("boxes %s and %s overlap" % (a, b))
    if problems:
        return None, problems

    mxfile = ET.Element(
        "mxfile", {"host": "app.diagrams.net", "agent": "AI contributor", "version": "24.0.0"}
    )
    diagram = ET.SubElement(mxfile, "diagram", {"name": name, "id": slug(name)})
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1400", "dy": "600", "grid": "1", "gridSize": "10", "guides": "1",
            "tooltips": "1", "connect": "1", "arrows": "1", "fold": "1", "page": "1",
            "pageScale": "1", "pageWidth": fmt(page_w), "pageHeight": fmt(page_h),
            "math": "0", "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    for n in nodes:
        cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": n["id"],
                "value": n["label"],
                "style": DASHED_STYLE if n.get("dashed") else NODE_STYLE,
                "vertex": "1",
                "parent": "1",
            },
        )
        x, y, w, h = boxes[n["id"]]
        ET.SubElement(
            cell, "mxGeometry",
            {"x": fmt(x), "y": fmt(y), "width": fmt(w), "height": fmt(h), "as": "geometry"},
        )

    for i, e in enumerate(edges, 1):
        exit_x, exit_y = e.get("exit", [1, 0.5])
        entry_x, entry_y = e.get("entry", [0, 0.5])
        label = e.get("label", "")
        style = EDGE_STYLE + (EDGE_LABEL_STYLE if label else "")
        style += "exitX=%s;exitY=%s;entryX=%s;entryY=%s;" % (
            fmt(exit_x), fmt(exit_y), fmt(entry_x), fmt(entry_y))
        cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": e.get("id", "e%d" % i),
                "value": label,
                "style": style,
                "edge": "1",
                "parent": "1",
                "source": e["from"],
                "target": e["to"],
            },
        )
        geometry = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
        if e.get("points"):
            array = ET.SubElement(geometry, "Array", {"as": "points"})
            for px, py in e["points"]:
                ET.SubElement(array, "mxPoint", {"x": fmt(px), "y": fmt(py)})

    ET.indent(mxfile, space="  ")
    xml = ET.tostring(mxfile, encoding="unicode") + "\n"

    right = max(b[0] + b[2] for b in boxes.values())
    bottom = max(b[1] + b[3] for b in boxes.values())
    for e in edges:
        for px, py in e.get("points", []):
            right, bottom = max(right, px), max(bottom, py)
    cols = math.ceil(right / page_w)
    rows = math.ceil(bottom / page_h)
    report = (
        "%d boxes, %d connectors | content %s x %s | page %s x %s | spans %d x %d pages"
        % (len(nodes), len(edges), fmt(right), fmt(bottom), fmt(page_w), fmt(page_h), cols, rows)
    )
    return (xml, report), []


def load_models(path):
    """Return the mxGraphModel elements of a .drawio file, decoding compressed ones."""
    root = ET.parse(path).getroot()
    diagrams = [root] if root.tag == "mxGraphModel" else root.findall("diagram")
    models = []
    for d in diagrams:
        if d.tag == "mxGraphModel":
            models.append(("", d))
            continue
        model = d.find("mxGraphModel")
        if model is None and (d.text or "").strip():
            raw = base64.b64decode(d.text.strip())
            text = zlib.decompress(raw, -15).decode("utf-8")
            model = ET.fromstring(urllib.parse.unquote(text))
        if model is not None:
            models.append((d.get("name", ""), model))
    return models


def plain(value):
    value = re.sub(r"<br\s*/?>", " / ", value or "", flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def inspect(path):
    for name, model in load_models(path):
        print("diagram: %s | page %s x %s" % (name or "(unnamed)", model.get("pageWidth"), model.get("pageHeight")))
        cells = model.findall(".//mxCell")
        labels = {}
        for c in cells:
            if c.get("vertex") == "1":
                g = c.find("mxGeometry")
                style = c.get("style") or ""
                labels[c.get("id")] = plain(c.get("value"))
                print("  box  %-10s %s | x=%s y=%s w=%s h=%s%s" % (
                    c.get("id"), plain(c.get("value")), g.get("x"), g.get("y"),
                    g.get("width"), g.get("height"), " | dashed" if "dashed=1" in style else ""))
        for c in cells:
            if c.get("edge") == "1":
                src, dst = c.get("source"), c.get("target")
                print("  link %-10s %s -> %s%s" % (
                    c.get("id"), labels.get(src, src), labels.get(dst, dst),
                    " | " + plain(c.get("value")) if plain(c.get("value")) else ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="build a .drawio file from a JSON spec")
    b.add_argument("spec")
    b.add_argument("out")
    b.add_argument("--allow-overlap", action="store_true")
    i = sub.add_parser("inspect", help="list the boxes and connectors of a .drawio file")
    i.add_argument("file")
    args = parser.parse_args()

    if args.command == "build":
        with open(args.spec, encoding="utf-8") as f:
            spec = json.load(f)
        result, problems = build(spec, args.allow_overlap)
        if problems:
            for p in problems:
                print("error: " + p, file=sys.stderr)
            return 1
        xml, report = result
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(xml)
        print("wrote %s\n%s" % (args.out, report))
    else:
        inspect(args.file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
