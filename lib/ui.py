"""Image and UI-tree checks for pp. Needs python3 with PIL for compare and sheet.

ui.py audit DENSITY          reads a uiautomator dump on stdin: small targets and unlabeled controls
ui.py compare A.png B.png    prints the regions that differ (a 24 px grid)
ui.py sheet OUT.png IMG...   joins screenshots side by side, scaled to 360 px wide
"""
import html
import re
import sys

MIN_DP = 48


def nodes(xml):
    for n in re.finditer(r"<node [^>]*>", xml):
        s = n.group(0)
        g = lambda k: html.unescape((re.search(r' %s="([^"]*)"' % k, s) or [0, ""])[1])
        b = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s)
        if b:
            yield g("text"), g("content-desc"), g("class"), g("clickable") == "true", tuple(map(int, b.groups()))


def label(node):
    """The text of a control: its own, else the first text of a child that is not a control itself.
    Compose puts the text of a button on a child node; TalkBack reads it as the label of the button."""
    own = node.get("text") or node.get("content-desc")
    if own:
        return own
    for child in node:
        if child.get("clickable") != "true":
            t = label(child)
            if t:
                return t
    return ""


def audit(density):
    import xml.etree.ElementTree as ET
    scale = density / 160
    raw = sys.stdin.read()
    # A display dump is a fragment (one block per window): wrap it in one root.
    root = ET.fromstring("<r>" + re.sub(r"<\?xml[^>]*\?>", "", raw).strip() + "</r>")
    found = 0
    for n in root.iter("node"):
        if n.get("clickable") != "true":
            continue
        b = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", n.get("bounds", ""))
        if not b:
            continue
        x1, y1, x2, y2 = map(int, b.groups())
        w, h = (x2 - x1) / scale, (y2 - y1) / scale
        name = label(n)
        if w < MIN_DP or h < MIN_DP:
            print("small  %dx%d dp  %s  at %d,%d" % (w, h, (name or "(no label)")[:40], (x1 + x2) // 2, (y1 + y2) // 2))
            found += 1
        if not name:
            print("nolabel  %dx%d dp  %s  at %d,%d" % (w, h, n.get("class", "").rsplit(".", 1)[-1], (x1 + x2) // 2, (y1 + y2) // 2))
            found += 1
    print("%d finding(s)" % found)


def load(path):
    from PIL import Image
    return Image.open(path).convert("RGB")


def compare(a, b, cell=24):
    from PIL import ImageChops
    ia, ib = load(a), load(b)
    if ia.size != ib.size:
        print("sizes differ: %dx%d vs %dx%d" % (ia.size + ib.size))
        return
    box = ImageChops.difference(ia, ib).convert("L").point(lambda v: 255 if v > 24 else 0)
    w, h = ia.size
    hits = [(x, y) for y in range(0, h, cell) for x in range(0, w, cell)
            if box.crop((x, y, x + cell, y + cell)).getbbox()]
    if not hits:
        print("same")
        return
    xs, ys = [p[0] for p in hits], [p[1] for p in hits]
    print("%.1f%% of the grid changed" % (100 * len(hits) * cell * cell / (w * h)))
    print("changed area: x %d-%d, y %d-%d" % (min(xs), max(xs) + cell, min(ys), max(ys) + cell))


def sheet(out, paths, width=360):
    from PIL import Image
    ims = []
    for p in paths:
        im = load(p)
        ims.append(im.resize((width, im.height * width // im.width)))
    canvas = Image.new("RGB", (width * len(ims) + 8 * (len(ims) - 1), max(i.height for i in ims)), (128, 128, 128))
    for k, im in enumerate(ims):
        canvas.paste(im, (k * (width + 8), 0))
    canvas.save(out)
    print(out)


if __name__ == "__main__":
    m = sys.argv[1]
    if m == "audit":
        audit(int(sys.argv[2]))
    elif m == "compare":
        compare(sys.argv[2], sys.argv[3])
    elif m == "sheet":
        sheet(sys.argv[2], sys.argv[3:])
