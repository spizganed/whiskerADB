"""Reads a uiautomator dump on stdin and prints what the commands need.

find.py tap "label"   prints the centre "x y" of the first node whose text or content-desc equals the label
find.py has "text"    exit 0 when a node text contains the text
find.py texts         prints each visible text, one per line
"""
import html
import re
import sys

mode = sys.argv[1]
arg = sys.argv[2] if len(sys.argv) > 2 else ""
xml = sys.stdin.read()
nodes = []
for n in re.finditer(r"<node [^>]*>", xml):
    s = n.group(0)
    t = re.search(r' text="([^"]*)"', s)
    d = re.search(r'content-desc="([^"]*)"', s)
    b = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s)
    nodes.append((html.unescape(t.group(1)) if t else "", html.unescape(d.group(1)) if d else "", b.groups() if b else None))

if mode == "tap":
    for text, desc, b in nodes:
        if b and arg in (text, desc):
            x1, y1, x2, y2 = map(int, b)
            print((x1 + x2) // 2, (y1 + y2) // 2)
            break
elif mode == "has":
    sys.exit(0 if any(arg in text for text, _, _ in nodes) else 1)
elif mode == "texts":
    for text, desc, _ in nodes:
        if text or desc:
            print((text or desc).replace("\n", " / ")[:100])
