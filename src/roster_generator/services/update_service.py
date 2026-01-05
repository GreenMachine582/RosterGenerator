from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional


ProgressCallback = Callable[[int, int], None]  # (downloaded_bytes, total_bytes)


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    download_url: str
    size: int


@dataclass(frozen=True)
class ReleaseInfo:
    tag: str
    name: str
    body: str
    html_url: str
    assets: list[ReleaseAsset]


class UpdateError(RuntimeError):
    pass


def parse_semver(tag: str) -> tuple[int, int, int]:
    """
    Accepts tags like:
      v1.2.3
      1.2.3
      1.2
      1
    Missing parts default to 0.
    """
    t = (tag or "").strip()
    if t.lower().startswith("v"):
        t = t[1:]

    # Extract only numeric dot parts to be tolerant of "1.2.3-beta"
    m = re.match(r"^\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?", t)
    if not m:
        return 0, 0, 0

    major = int(m.group(1) or 0)
    minor = int(m.group(2) or 0)
    patch = int(m.group(3) or 0)
    return major, minor, patch


def is_newer(remote_tag: str, local_version: str) -> bool:
    return parse_semver(remote_tag) > parse_semver(local_version)


def fetch_latest_release(owner: str, repo: str, timeout_s: int = 15) -> ReleaseInfo:
    api = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    req = urllib.request.Request(
        api,
        headers={
            "Accept": "application/vnd.github+json",
            # GitHub can rate-limit anonymous clients; a UA helps.
            "User-Agent": f"{repo}-updater",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    assets: list[ReleaseAsset] = []
    for a in data.get("assets", []):
        assets.append(
            ReleaseAsset(
                name=a.get("name", ""),
                download_url=a.get("browser_download_url", ""),
                size=int(a.get("size", 0) or 0),
            )
        )

    return ReleaseInfo(
        tag=data.get("tag_name", "") or "",
        name=data.get("name", "") or "",
        body=data.get("body", "") or "",
        html_url=data.get("html_url", "") or "",
        assets=assets,
    )


def _platform_key() -> str:
    sysname = platform.system().lower()

    if "windows" in sysname:
        return "windows"
    if "darwin" in sysname or "mac" in sysname:
        return "macos"
    return "linux"


def select_asset(release: ReleaseInfo) -> Optional[ReleaseAsset]:
    """
    Selection rules for a *simple* updater:
    - Windows: prefer a portable .exe
    - macOS: prefer a zipped .app or a .dmg (we can open dmg, but launching the app inside is manual)
    - Linux: prefer AppImage
    Adjust these rules to match your release naming.
    """
    key = _platform_key()
    names = [a.name.lower() for a in release.assets]

    if key == "windows":
        # Prefer installer assets first
        installers = [
            a for a in release.assets
            if a.name.lower().endswith(".exe") and ("setup" in a.name.lower() or "installer" in a.name.lower())
        ]
        if installers:
            return installers[0]

        msis = [a for a in release.assets if a.name.lower().endswith(".msi")]
        if msis:
            return msis[0]

        # Fallback: portable exe
        portable = [a for a in release.assets if a.name.lower().endswith(".exe") and "portable" in a.name.lower()]
        if portable:
            return portable[0]
        exes = [a for a in release.assets if a.name.lower().endswith(".exe")]
        return exes[0] if exes else None

    if key == "macos":
        # If you publish a zip containing the .app, that can be unzipped and launched by us.
        zips = [a for a in release.assets if a.name.lower().endswith(".zip")]
        if zips:
            return zips[0]
        dmgs = [a for a in release.assets if a.name.lower().endswith(".dmg")]
        return dmgs[0] if dmgs else None

    # linux
    appimages = [a for a in release.assets if a.name.lower().endswith(".appimage")]
    if appimages:
        return appimages[0]
    tarballs = [a for a in release.assets if a.name.lower().endswith((".tar.gz", ".tgz"))]
    return tarballs[0] if tarballs else None


def download_asset(
    asset: ReleaseAsset,
    *,
    progress: ProgressCallback | None = None,
    timeout_s: int = 60,
) -> str:
    """
    Downloads asset to a temp folder. Returns the downloaded file path.
    """
    tmp_dir = tempfile.mkdtemp(prefix="roster_update_")
    dest_path = os.path.join(tmp_dir, asset.name)

    req = urllib.request.Request(
        asset.download_url,
        headers={"User-Agent": "roster-updater", "Accept": "application/octet-stream"},
    )

    with urllib.request.urlopen(req, timeout=timeout_s) as resp, open(dest_path, "wb") as f:
        total = int(resp.headers.get("Content-Length") or asset.size or 0)
        downloaded = 0
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if progress:
                progress(downloaded, total)

    return dest_path


def _open_file(path: str) -> None:
    key = _platform_key()
    if key == "windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif key == "macos":
        subprocess.Popen(["open", path], close_fds=True)
    else:
        subprocess.Popen(["xdg-open", path], close_fds=True)


def install_and_relaunch(downloaded_path: str) -> None:
    """
    Simple "install + relaunch" strategy:
      - If the downloaded asset is directly executable (portable exe/AppImage), run it and exit current app.
      - If it's a zip/dmg/tarball, open it and raise an error telling the user what to do next.

    This keeps the updater robust and avoids in-place replacement complexity.
    """
    key = _platform_key()
    lower = downloaded_path.lower()

    if key == "windows" and lower.endswith(".exe"):
        base = os.path.basename(lower)
        is_installer = ("setup" in base) or ("installer" in base)

        if is_installer:
            # Inno Setup silent switches
            args = [
                downloaded_path,
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                "/SP-",
            ]
            subprocess.Popen(args, close_fds=True)
            return

        # Otherwise treat as portable exe
        subprocess.Popen([downloaded_path], close_fds=True)
        return

    if key == "linux" and lower.endswith(".appimage"):
        # Ensure executable bit (best-effort) then run.
        try:
            st = os.stat(downloaded_path)
            os.chmod(downloaded_path, st.st_mode | 0o111)
        except Exception:
            pass
        subprocess.Popen([downloaded_path], close_fds=True)
        return

    if key == "macos" and lower.endswith(".zip"):
        # Unzip then try to locate an .app and open it.
        extract_dir = tempfile.mkdtemp(prefix="roster_update_extract_")
        shutil.unpack_archive(downloaded_path, extract_dir)

        # Find first .app bundle
        app_bundle = None
        for root, dirs, _files in os.walk(extract_dir):
            for d in dirs:
                if d.lower().endswith(".app"):
                    app_bundle = os.path.join(root, d)
                    break
            if app_bundle:
                break

        if app_bundle:
            subprocess.Popen(["open", app_bundle], close_fds=True)
            return

        # If no .app, open the extracted directory
        _open_file(extract_dir)
        raise UpdateError("Downloaded zip did not contain an .app bundle. Opened folder instead.")

    # Fallback: open file and tell user to install manually
    _open_file(downloaded_path)
    raise UpdateError(
        f"Downloaded update is not directly launchable ({os.path.basename(downloaded_path)}). "
        f"It has been opened. Please install/update manually, then relaunch the app."
    )
