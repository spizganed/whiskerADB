"""Writes the pp block into AGENTS.md and CLAUDE.md of the current folder. Run it again to update the block."""
import os
import re

BEGIN, END = "<!-- whiskerADB: begin -->", "<!-- whiskerADB: end -->"
BLOCK = f"""{BEGIN}
## Android UI checks

To run, tap or check an app on the phone, use `pp`. Run `pp` alone for the commands. Set `PP_PKG` to the app id. Use `pp texts` and `pp audit` before `pp shot`.
{END}
"""

for name in ("AGENTS.md", "CLAUDE.md"):
    text = open(name).read() if os.path.exists(name) else ""
    if BEGIN in text:
        text = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", lambda _: BLOCK, text, flags=re.S)
    else:
        text = text.rstrip("\n") + ("\n\n" if text else "") + BLOCK
    open(name, "w").write(text)
    print("wrote", name)
