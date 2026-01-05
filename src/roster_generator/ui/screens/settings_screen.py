from __future__ import annotations

import os
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox

from roster_generator.services.update_service import (
    UpdateError,
    download_asset,
    fetch_latest_release,
    install_and_relaunch,
    is_newer,
    select_asset,
)
from roster_generator.ui.widgets.markdown_text import render_markdown_to_text
from roster_generator.version import UPDATE_GITHUB_OWNER, UPDATE_GITHUB_REPO


class SettingsScreen(ttk.Frame):
    """
    Settings screen focused on self-update functionality:
      - Check latest GitHub release
      - Show release notes
      - Download asset with progress
      - Install & relaunch (portable-style when possible)
    """

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent)
        self.app = app

        self.latest_release = None
        self.latest_asset = None
        self.downloaded_path: str | None = None

        # Layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        title = ttk.Label(self, text="Settings", style="Heading.TLabel")
        title.grid(row=0, column=0, sticky="w")

        # --- Update panel ----------------------------------------------------
        panel = ttk.LabelFrame(self, text="Updates", padding=12)
        panel.grid(row=1, column=0, sticky="ew", pady=(12, 12))
        panel.columnconfigure(1, weight=1)

        ttk.Label(panel, text="Current version:").grid(row=0, column=0, sticky="w")
        ttk.Label(panel, text=f"v{self.app.meta.version}").grid(row=0, column=1, sticky="w")

        ttk.Label(panel, text="Latest version:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.latest_version_var = tk.StringVar(value="—")
        ttk.Label(panel, textvariable=self.latest_version_var).grid(row=1, column=1, sticky="w", pady=(6, 0))

        ttk.Label(panel, text="Release:").grid(row=2, column=0, sticky="w", pady=(6, 0))

        self.release_url_var = tk.StringVar(value="—")
        self.release_url_lbl = ttk.Label(panel, textvariable=self.release_url_var)
        self.release_url_lbl.grid(row=2, column=1, sticky="w", pady=(6, 0))

        self.open_release_btn = ttk.Button(
            panel,
            text="Open release in browser",
            command=self.open_release_in_browser,
            state="disabled",
        )
        self.open_release_btn.grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))


        btns = ttk.Frame(panel)
        btns.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))

        self.check_btn = ttk.Button(btns, text="Check for updates", command=self.start_update_check)
        self.check_btn.pack(side="left")

        self.download_btn = ttk.Button(btns, text="Download", command=self.download_update, state="disabled")
        self.download_btn.pack(side="left", padx=(8, 0))

        self.install_btn = ttk.Button(btns, text="Install & relaunch", command=self.install_update, state="disabled")
        self.install_btn.pack(side="left", padx=(8, 0))

        # Progress
        self.progress_var = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(panel, mode="determinate", maximum=100, variable=self.progress_var, length=420)
        self.progress.grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(panel, textvariable=self.status_var).grid(row=6, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # --- Release notes ---------------------------------------------------
        notes = ttk.LabelFrame(self, text="Release notes", padding=12)
        notes.grid(row=2, column=0, sticky="nsew")
        notes.columnconfigure(0, weight=1)
        notes.rowconfigure(0, weight=1)

        self.notes_txt = tk.Text(notes, height=14, wrap="word")
        self.notes_txt.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(notes, orient="vertical", command=self.notes_txt.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.notes_txt.configure(yscrollcommand=scroll.set)

        self._set_notes("Release notes will appear here after checking for updates.")

    def on_show(self) -> None:
        self.app.status_var.set("Viewing: Settings")

    def _set_notes(self, text: str) -> None:
        render_markdown_to_text(self.notes_txt, text or "")

    # --- Update logic --------------------------------------------------------

    def start_update_check(self) -> None:
        self.check_btn.configure(state="disabled")
        self.download_btn.configure(state="disabled")
        self.install_btn.configure(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("Checking GitHub Releases…")
        self.latest_version_var.set("—")
        self.release_url_var.set("—")
        self.open_release_btn.configure(state="disabled")
        self._set_notes("Checking for updates…")

        self.after(50, self._do_update_check)

    def _do_update_check(self) -> None:
        try:
            release = fetch_latest_release(UPDATE_GITHUB_OWNER, UPDATE_GITHUB_REPO)
        except Exception as e:
            self.status_var.set("Update check failed.")
            self._set_notes(f"Could not contact GitHub.\n\n{e}")
            self.check_btn.configure(state="normal")
            return

        self.latest_release = release
        self.latest_asset = select_asset(release)
        # Populate link
        if release.html_url:
            self.release_url_var.set(release.html_url)
            self.open_release_btn.configure(state="normal")
        else:
            self.release_url_var.set("—")
            self.open_release_btn.configure(state="disabled")


        self.latest_version_var.set(release.tag or "—")
        notes = (release.body or "").strip() or "(No release notes provided.)"
        self._set_notes(notes)

        if not release.tag:
            self.status_var.set("No release information found.")
            self.check_btn.configure(state="normal")
            return

        if not is_newer(release.tag, self.app.meta.version):
            self.status_var.set("You are up to date.")
            self.check_btn.configure(state="normal")
            return

        if not self.latest_asset:
            self.status_var.set("Update available, but no compatible asset found for this OS.")
            self.check_btn.configure(state="normal")
            return

        self.status_var.set(f"Update available: {release.tag} ({self.latest_asset.name})")
        self.download_btn.configure(state="normal")
        self.check_btn.configure(state="normal")

    def open_release_in_browser(self) -> None:
        if not self.latest_release or not getattr(self.latest_release, "html_url", ""):
            messagebox.showinfo("Release", "No release link available yet. Check for updates first.")
            return

        try:
            webbrowser.open(self.latest_release.html_url)
        except Exception as e:
            messagebox.showerror("Open release failed", str(e))

    def download_update(self) -> None:
        if not self.latest_release or not self.latest_asset:
            messagebox.showinfo("Download", "Check for updates first.")
            return

        self.download_btn.configure(state="disabled")
        self.install_btn.configure(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("Downloading update…")

        def on_progress(downloaded: int, total: int) -> None:
            if total <= 0:
                self.progress.configure(mode="indeterminate")
                self.progress.start(12)
                return
            self.progress.configure(mode="determinate", maximum=100)
            pct = int((downloaded / total) * 100)
            self.progress_var.set(max(0, min(100, pct)))
            self.update_idletasks()

        try:
            path = download_asset(self.latest_asset, progress=on_progress)
            self.downloaded_path = path
        except Exception as e:
            self.status_var.set("Download failed.")
            messagebox.showerror("Download failed", str(e))
            self.download_btn.configure(state="normal")
            try:
                self.progress.stop()
            except Exception:
                pass
            self.progress.configure(mode="determinate")
            return

        try:
            self.progress.stop()
        except Exception:
            pass
        self.progress.configure(mode="determinate")
        self.progress_var.set(100)

        self.status_var.set(f"Downloaded: {os.path.basename(self.downloaded_path)}")
        self.install_btn.configure(state="normal")

    def install_update(self) -> None:
        if not self.downloaded_path:
            messagebox.showinfo("Install", "Download the update first.")
            return

        if not messagebox.askyesno(
            "Install update",
            "The app will launch the updated version and close this instance.\n\nContinue?",
        ):
            return

        try:
            install_and_relaunch(self.downloaded_path)
        except UpdateError as e:
            messagebox.showwarning("Manual step required", str(e))
            self.status_var.set("Opened update package (manual install required).")
            return
        except Exception as e:
            messagebox.showerror("Install failed", str(e))
            self.status_var.set("Install failed.")
            return

        self.app.destroy()
