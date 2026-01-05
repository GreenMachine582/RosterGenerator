from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def apply_theme(root: tk.Tk) -> None:
    """
    Conservative cross-platform ttk styling.
    """
    style = ttk.Style(root)
    try:
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("Heading.TLabel", font=("TkDefaultFont", 14, "bold"))
    style.configure("Sidebar.TFrame", padding=12)
    style.configure("Sidebar.TButton", anchor="w")
    style.configure("SidebarHeading.TLabel", font=("TkDefaultFont", 11, "bold"))
