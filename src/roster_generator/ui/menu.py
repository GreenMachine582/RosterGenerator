from __future__ import annotations

import tkinter as tk
from tkinter import messagebox


def build_menubar(app: tk.Tk, *, on_show_settings, on_check_updates) -> tk.Menu:
    """
    Returns a fully configured menubar.
    """
    menubar = tk.Menu(app)

    app_menu = tk.Menu(menubar, tearoff=0)
    app_menu.add_command(label="Settings", command=on_show_settings)
    app_menu.add_separator()
    app_menu.add_command(label="Exit", command=app.destroy)
    menubar.add_cascade(label="App", menu=app_menu)

    help_menu = tk.Menu(menubar, tearoff=0)

    def about() -> None:
        # Try to use app.meta if present, fallback to generic.
        meta = getattr(app, "meta", None)
        if meta:
            messagebox.showinfo(
                "About",
                f"{meta.name}\nVersion: {meta.version}\n\n"
                "engine designed to automatically assign employees to operational lines/shifts while respecting hard "
                "constraints, soft preferences, and scoring heuristics.",
            )
        else:
            messagebox.showinfo("About", "Roster Generator")

    help_menu.add_command(label="About", command=about)
    help_menu.add_command(label="Check for Updates…", command=on_check_updates)
    menubar.add_cascade(label="Help", menu=help_menu)

    return menubar
