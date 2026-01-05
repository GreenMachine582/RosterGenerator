from __future__ import annotations

from tkinter import ttk


def build_sidebar(parent: ttk.Frame, *, app_name: str, app_version: str, on_show_settings, on_exit) -> None:
    ttk.Label(parent, text=app_name, style="SidebarHeading.TLabel").pack(anchor="w")
    ttk.Label(parent, text=f"v{app_version}").pack(anchor="w", pady=(0, 12))

    ttk.Button(
        parent, text="Settings", style="Sidebar.TButton",
        command=on_show_settings
    ).pack(fill="x", pady=2)

    ttk.Separator(parent).pack(fill="x", pady=12)

    ttk.Button(parent, text="Exit", style="Sidebar.TButton", command=on_exit).pack(fill="x", pady=2)
