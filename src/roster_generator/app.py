from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk, messagebox

from roster_generator.version import __version__
from roster_generator.ui.theme import apply_theme
from roster_generator.ui.menu import build_menubar
from roster_generator.ui.sidebar import build_sidebar
from roster_generator.ui.screens.settings_screen import SettingsScreen


@dataclass(frozen=True)
class AppMeta:
    name: str = "Roster Generator"
    version: str = __version__


class App(tk.Tk):
    """
    Thin app shell:
      - theme
      - menu
      - sidebar
      - screen container + navigation
      - status bar
    """

    def __init__(self, meta: AppMeta) -> None:
        super().__init__()
        self.meta = meta

        self.title(f"{self.meta.name} — v{self.meta.version}")
        self.minsize(1100, 700)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        apply_theme(self)
        self._build_root()
        self._build_menu()

        self.show_screen("settings")

    def _build_menu(self) -> None:
        menubar = build_menubar(
            self,
            on_show_settings=lambda: self.show_screen("settings"),
            on_check_updates=self._check_for_updates,
        )
        self.config(menu=menubar)

    def _build_root(self) -> None:
        root = ttk.Frame(self)
        root.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ttk.Frame(root, style="Sidebar.TFrame")
        self.sidebar.grid(row=0, column=0, sticky="ns")
        build_sidebar(
            self.sidebar,
            app_name=self.meta.name,
            app_version=self.meta.version,
            on_show_settings=lambda: self.show_screen("settings"),
            on_exit=self.destroy,
        )

        # Screens container
        self.container = ttk.Frame(root, padding=12)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)

        self.screens: dict[str, ttk.Frame] = {
            "settings": SettingsScreen(self.container, self),
        }

        for frame in self.screens.values():
            frame.grid(row=0, column=0, sticky="nsew")

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self, textvariable=self.status_var, anchor="w", padding=(10, 6))
        status.grid(row=1, column=0, sticky="ew")

    def show_screen(self, name: str) -> None:
        frame = self.screens.get(name)
        if not frame:
            messagebox.showerror("Navigation Error", f"Screen not found: {name!r}")
            return

        frame.tkraise()
        self.status_var.set(f"Viewing: {name.capitalize()}")

        refresh = getattr(frame, "on_show", None)
        if callable(refresh):
            refresh()

    def _check_for_updates(self) -> None:
        self.show_screen("settings")
        frame = self.screens.get("settings")
        if frame and hasattr(frame, "start_update_check"):
            frame.start_update_check()  # type: ignore[attr-defined]


def main() -> int:
    meta = AppMeta()
    app = App(meta)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
