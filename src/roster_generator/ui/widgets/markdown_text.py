import re
import tkinter as tk
from tkinter import font as tkfont


def render_markdown_to_text(text_widget: tk.Text, md: str) -> None:
    """
    Very small Markdown renderer for tk.Text.
    Supports: headings (#/##/###), bullets (-/*), fenced code blocks,
              bold (**), inline code (`).
    """

    # Reset
    text_widget.configure(state="normal")
    text_widget.delete("1.0", "end")

    # Fonts
    base_font = tkfont.nametofont("TkDefaultFont")
    h1 = base_font.copy(); h1.configure(size=base_font.cget("size") + 6, weight="bold")
    h2 = base_font.copy(); h2.configure(size=base_font.cget("size") + 4, weight="bold")
    h3 = base_font.copy(); h3.configure(size=base_font.cget("size") + 2, weight="bold")
    bold = base_font.copy(); bold.configure(weight="bold")
    mono = tkfont.Font(family="TkFixedFont")

    # Tags
    text_widget.tag_configure("h1", font=h1, spacing3=6)
    text_widget.tag_configure("h2", font=h2, spacing3=4)
    text_widget.tag_configure("h3", font=h3, spacing3=2)
    text_widget.tag_configure("bold", font=bold)
    text_widget.tag_configure("code", font=mono, background="#f2f2f2")
    text_widget.tag_configure("bullet", lmargin1=18, lmargin2=36)
    text_widget.tag_configure("codeblock", font=mono, background="#f2f2f2", lmargin1=12, lmargin2=12)

    lines = (md or "").splitlines()
    in_codeblock = False

    def insert_inline(s: str) -> None:
        """
        Handles **bold** and `inline code` within a line.
        """
        # Split on inline code first
        parts = re.split(r"(`[^`]+`)", s)
        for part in parts:
            if part.startswith("`") and part.endswith("`") and len(part) >= 2:
                text_widget.insert("end", part[1:-1], ("code",))
            else:
                # Now handle bold inside non-code segments
                bparts = re.split(r"(\*\*[^*]+\*\*)", part)
                for bp in bparts:
                    if bp.startswith("**") and bp.endswith("**") and len(bp) >= 4:
                        text_widget.insert("end", bp[2:-2], ("bold",))
                    else:
                        text_widget.insert("end", bp)

    for line in lines:
        if line.strip().startswith("```"):
            in_codeblock = not in_codeblock
            # keep a blank line separation around code blocks
            text_widget.insert("end", "\n")
            continue

        if in_codeblock:
            text_widget.insert("end", line + "\n", ("codeblock",))
            continue

        # Headings
        if line.startswith("# "):
            text_widget.insert("end", line[2:].strip() + "\n", ("h1",))
            continue
        if line.startswith("## "):
            text_widget.insert("end", line[3:].strip() + "\n", ("h2",))
            continue
        if line.startswith("### "):
            text_widget.insert("end", line[4:].strip() + "\n", ("h3",))
            continue

        # Bullets
        m = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if m:
            text_widget.insert("end", "• ", ("bullet",))
            insert_inline(m.group(2))
            text_widget.insert("end", "\n", ("bullet",))
            continue

        # Normal line
        insert_inline(line)
        text_widget.insert("end", "\n")

    text_widget.configure(state="disabled")
