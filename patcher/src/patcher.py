"""Accessible installer and updater for AdVenture Capitalist Access."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

import wx

try:
    from accessible_output2.outputs.auto import Auto
    SPEAKER = Auto()
except Exception:
    SPEAKER = None


APP_NAME = "AdVenture Capitalist Access Patcher"
PATCHER_VERSION = "1.2.4.9"
GITHUB_LATEST = "https://api.github.com/repos/ShotgunSpoon/adCapAccess/releases/latest"
MOD_MANIFEST = "https://raw.githubusercontent.com/ShotgunSpoon/adcap_patch/main/manifest.json"
README_URL = "https://raw.githubusercontent.com/ShotgunSpoon/adCapAccess/main/readme.txt"
README_MAX_BYTES = 1024 * 1024
DEFAULT_GAME_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\AdVenture Capitalist")
GAME_EXE = "adventure-capitalist.exe"
MANAGED_RELATIVE = Path("adventure-capitalist_Data") / "Managed"
BACKUP_RELATIVE = Path("_AdCapAccessBackup") / "patcher-original"


def speak(text: str, interrupt: bool = False) -> None:
    if SPEAKER is not None:
        try:
            SPEAKER.speak(text, interrupt=interrupt)
        except Exception:
            pass


def version_tuple(value: str) -> tuple[int, ...]:
    result = []
    for part in value.lstrip("vV").split("."):
        digits = "".join(c for c in part if c.isdigit())
        result.append(int(digits or 0))
    return tuple(result)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().lower()


def request_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": f"adCapAccess/{PATCHER_VERSION}"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def download(url: str, destination: Path, progress=None) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": f"adCapAccess/{PATCHER_VERSION}"})
    with urllib.request.urlopen(request, timeout=30) as response, destination.open("wb") as output:
        total = int(response.headers.get("Content-Length", "-1"))
        received = 0
        while True:
            block = response.read(1024 * 128)
            if not block:
                break
            output.write(block)
            received += len(block)
            if progress:
                progress(received, total)


def find_release_asset(release: dict, name: str) -> dict | None:
    return next((asset for asset in release.get("assets", []) if asset.get("name") == name), None)


def validate_readme(data: bytes) -> bytes:
    if len(data) > README_MAX_BYTES:
        raise RuntimeError("The README response is larger than expected.")
    text = data.decode("utf-8-sig")
    if not text.startswith("AdVenture Capitalist Access\n") and not text.startswith("AdVenture Capitalist Access\r\n"):
        raise RuntimeError("The server did not return the gameplay README.")
    if "\x00" in text:
        raise RuntimeError("The README response is not a plain text file.")
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")


def request_readme() -> bytes:
    request = urllib.request.Request(README_URL, headers={
        "Accept": "text/plain", "Cache-Control": "no-cache",
        "User-Agent": f"adCapAccess/{PATCHER_VERSION}",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        return validate_readme(response.read(README_MAX_BYTES + 1))


def bundled_readme() -> bytes:
    root = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
    return validate_readme((root / "readme.txt").read_bytes())


def save_readme(destination: Path, data: bytes) -> None:
    # Stage beside the destination so a failed download/write preserves any old file.
    data = validate_readme(data)
    staged = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".adcap-readme-", suffix=".tmp", dir=destination.parent, delete=False) as output:
            staged = Path(output.name)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(staged, destination)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


class Installer:
    def __init__(self, game_dir: Path, log, progress):
        self.game_dir = game_dir
        self.log = log
        self.progress = progress

    @property
    def managed_dir(self) -> Path:
        return self.game_dir / MANAGED_RELATIVE

    @property
    def assembly_path(self) -> Path:
        return self.managed_dir / "Assembly-CSharp.dll"

    @property
    def backup_path(self) -> Path:
        return self.game_dir / BACKUP_RELATIVE / "Assembly-CSharp.dll"

    def validate_game(self) -> None:
        if not (self.game_dir / GAME_EXE).is_file():
            raise RuntimeError(f"{GAME_EXE} was not found in {self.game_dir}")
        if not self.assembly_path.is_file():
            raise RuntimeError("The managed game assembly was not found. Verify the selected game folder.")

    def ensure_game_closed(self) -> None:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {GAME_EXE}", "/NH"],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if GAME_EXE.lower() in result.stdout.lower():
            raise RuntimeError("AdVenture Capitalist is running. Close the game before installing or repairing.")

    def status(self, manifest: dict) -> str:
        runtime = self.managed_dir / "AdCap.UnityMCP.dll"
        version_file = self.game_dir / ".adcap-access-version"
        if not runtime.is_file():
            return "not installed"
        installed = version_file.read_text(encoding="utf-8").strip() if version_file.is_file() else "unknown"
        if installed == manifest["version"]:
            return f"up to date, version {installed}"
        return f"version {installed} installed; version {manifest['version']} is available"

    def install(self, manifest: dict) -> None:
        self.validate_game()
        self.ensure_game_closed()
        files = manifest.get("files", [])
        if not files:
            raise RuntimeError("The update manifest contains no files.")

        assembly_entry = next((item for item in files if item.get("target", "").endswith("Assembly-CSharp.dll")), None)
        if assembly_entry is None:
            raise RuntimeError("The update does not contain the required game assembly patch.")

        current_hash = sha256(self.assembly_path)
        allowed = {value.lower() for value in assembly_entry.get("accepted_installed_sha256", [])}
        if current_hash not in allowed:
            raise RuntimeError(
                "This game build is not supported, so no files were changed. "
                "Steam may have updated the game; wait for a compatible mod release."
            )

        if not self.backup_path.exists():
            self.backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.assembly_path, self.backup_path)
            self.log(f"Backed up the original game assembly to {self.backup_path}")

        with tempfile.TemporaryDirectory(prefix="adcap_access_") as temp_name:
            temp_dir = Path(temp_name)
            downloaded = []
            for index, item in enumerate(files, 1):
                name = item["name"]
                local = temp_dir / name
                self.log(f"Downloading {name}")
                download(item["url"], local)
                actual = sha256(local)
                if actual != item["sha256"].lower():
                    raise RuntimeError(f"Integrity check failed for {name}. No update was installed.")
                downloaded.append((item, local))
                self.progress(int(index / len(files) * 70))

            staged = []
            try:
                for item, local in downloaded:
                    target = self.game_dir / Path(item["target"])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    replacement = target.with_suffix(target.suffix + ".adcap-new")
                    shutil.copy2(local, replacement)
                    staged.append((target, replacement))
                for target, replacement in staged:
                    os.replace(replacement, target)
            finally:
                for _, replacement in staged:
                    replacement.unlink(missing_ok=True)

        (self.game_dir / ".adcap-access-version").write_text(manifest["version"], encoding="utf-8")
        self.progress(100)

    def restore(self) -> None:
        self.validate_game()
        self.ensure_game_closed()
        if not self.backup_path.is_file():
            raise RuntimeError("No patcher-created original-game backup was found.")
        os.replace(self.assembly_path, self.assembly_path.with_suffix(".dll.adcap-disabled"))
        shutil.copy2(self.backup_path, self.assembly_path)
        for target in (
            self.managed_dir / "AdCap.UnityMCP.dll",
            self.game_dir / "nvdaControllerClient32.dll",
            self.game_dir / ".adcap-access-version",
        ):
            target.unlink(missing_ok=True)


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title=APP_NAME, size=(720, 500))
        self.manifest = None
        self.path_check = None
        self.check_generation = 0
        self.readme_busy = False
        self.self_update_offered = False
        self.updating_patcher = False
        self.installing = False
        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)

        heading = wx.StaticText(panel, label="AdVenture Capitalist Access")
        font = heading.GetFont()
        font.SetPointSize(font.GetPointSize() + 4)
        font.MakeBold()
        heading.SetFont(font)
        layout.Add(heading, 0, wx.ALL, 12)

        layout.Add(wx.StaticText(panel, label="Game folder"), 0, wx.LEFT | wx.RIGHT, 12)
        folder_row = wx.BoxSizer(wx.HORIZONTAL)
        self.folder = wx.TextCtrl(panel, value=str(DEFAULT_GAME_DIR), name="AdVenture Capitalist game folder")
        self.folder.Bind(wx.EVT_TEXT, self.on_folder_changed)
        browse = wx.Button(panel, label="Browse...", name="Browse for the AdVenture Capitalist game folder")
        browse.Bind(wx.EVT_BUTTON, self.on_browse)
        folder_row.Add(self.folder, 1, wx.EXPAND | wx.RIGHT, 8)
        folder_row.Add(browse)
        layout.Add(folder_row, 0, wx.EXPAND | wx.ALL, 12)

        self.status = wx.StaticText(panel, label="Checking for updates...", name="Update status")
        layout.Add(self.status, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        button_row = wx.BoxSizer(wx.HORIZONTAL)
        self.install_button = wx.Button(panel, label="Install or Update", name="Install or update the accessibility mod")
        self.repair_button = wx.Button(panel, label="Repair", name="Repair the installed accessibility mod")
        self.restore_button = wx.Button(panel, label="Restore Original Game", name="Remove the accessibility mod and restore the original game assembly")
        exit_button = wx.Button(panel, label="Exit")
        self.install_button.Bind(wx.EVT_BUTTON, lambda event: self.start_install())
        self.repair_button.Bind(wx.EVT_BUTTON, lambda event: self.start_install())
        self.restore_button.Bind(wx.EVT_BUTTON, self.on_restore)
        exit_button.Bind(wx.EVT_BUTTON, lambda event: self.Close())
        for button in (self.install_button, self.repair_button, self.restore_button, exit_button):
            button_row.Add(button, 0, wx.RIGHT, 8)
        layout.Add(button_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.readme_button = wx.Button(panel, label="Download &README...", name="Download README and choose where to save it")
        self.readme_button.Bind(wx.EVT_BUTTON, self.on_download_readme)
        layout.Add(self.readme_button, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.gauge = wx.Gauge(panel, range=100, name="Download and installation progress")
        layout.Add(self.gauge, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        self.log = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, name="Installation log")
        layout.Add(self.log, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        panel.SetSizer(layout)
        self.Centre()
        wx.CallAfter(self.check_updates)

    def announce(self, message: str) -> None:
        self.status.SetLabel(message)
        self.log.AppendText(message + "\n")
        speak(message, interrupt=True)

    def set_busy(self, busy: bool) -> None:
        # Documentation stays available during update checks and with an invalid game folder.
        for control in (self.install_button, self.repair_button, self.restore_button, self.folder):
            control.Enable(not (busy or self.updating_patcher))

    def on_download_readme(self, _event=None) -> None:
        if self.readme_busy or self.updating_patcher:
            return
        with wx.FileDialog(
            self, "Save the gameplay README", defaultFile="readme.txt",
            wildcard="Text files (*.txt)|*.txt", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                return
            destination = Path(dialog.GetPath())
        self.readme_busy = True
        self.readme_button.Disable()
        self.announce("Downloading the gameplay README...")
        threading.Thread(target=self._readme_worker, args=(destination,), daemon=True).start()

    def _readme_worker(self, destination: Path, included: bool = False) -> None:
        try:
            data = bundled_readme() if included else request_readme()
        except Exception as error:
            if included:
                wx.CallAfter(self._readme_done, f"Could not read the included README: {error}")
            else:
                wx.CallAfter(self._offer_included_readme, destination, str(error))
            return
        try:
            save_readme(destination, data)
            source = "Included README" if included else "README"
            wx.CallAfter(self._readme_done, f"{source} saved to {destination}.")
        except Exception as error:
            wx.CallAfter(self._readme_done, f"Could not save the README: {error}. Choose another location and try again.")

    def _offer_included_readme(self, destination: Path, error: str) -> None:
        if wx.MessageBox(
            f"The gameplay README could not be downloaded: {error}\n\n"
            "Save the copy included with this patcher instead? It may be older than the online guide.",
            "Save included README", wx.YES_NO | wx.ICON_QUESTION, self,
        ) == wx.YES:
            threading.Thread(target=self._readme_worker, args=(destination, True), daemon=True).start()
        else:
            self._readme_done("README download canceled. No file was saved.")

    def _readme_done(self, message: str) -> None:
        self.readme_busy = False
        self.readme_button.Enable()
        self.announce(message)

    def on_browse(self, _event) -> None:
        dialog = wx.DirDialog(self, "Select the AdVenture Capitalist install folder", self.folder.GetValue())
        if dialog.ShowModal() == wx.ID_OK:
            self.folder.SetValue(dialog.GetPath())
        dialog.Destroy()

    def on_folder_changed(self, _event) -> None:
        self.manifest = None
        self.check_generation += 1
        generation = self.check_generation
        if self.path_check is not None:
            self.path_check.Stop()
        self.status.SetLabel("Game folder changed. Checking the selected folder...")
        self.path_check = wx.CallLater(350, self.check_updates, generation)

    def check_updates(self, generation: int | None = None) -> None:
        if generation is None:
            self.check_generation += 1
            generation = self.check_generation
        elif generation != self.check_generation:
            return
        game_dir = Path(self.folder.GetValue().strip())
        self.path_check = None
        self.set_busy(True)
        threading.Thread(target=self._check_worker, args=(game_dir, generation), daemon=True).start()

    def _check_worker(self, game_dir: Path, generation: int) -> None:
        try:
            self._check_self_update()
            manifest = request_json(MOD_MANIFEST)
            installer = Installer(game_dir, lambda text: None, lambda value: None)
            installer.validate_game()
            result = installer.status(manifest)
            wx.CallAfter(self._check_done, generation, manifest, f"Mod status: {result}.")
        except Exception as error:
            wx.CallAfter(self._check_done, generation, None, f"Update check failed: {error}")

    def _check_self_update(self) -> None:
        try:
            release = request_json(GITHUB_LATEST)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return
            raise
        remote = release.get("tag_name", "0")
        if version_tuple(remote) <= version_tuple(PATCHER_VERSION):
            return
        if not getattr(sys, "frozen", False):
            wx.CallAfter(self.announce, f"Patcher {remote} is available. Run the released patcher to update automatically.")
            return
        asset = find_release_asset(release, "AdCapAccessPatcher.exe")
        digest = asset.get("digest", "") if asset else ""
        if not asset or not digest.startswith("sha256:"):
            raise RuntimeError("A patcher update exists but its verified release file is incomplete.")
        # Opening the patcher to obtain the guide must not require an executable download.
        wx.CallAfter(self._offer_self_update, remote, asset)

    def _offer_self_update(self, remote: str, asset: dict) -> None:
        if self.self_update_offered:
            return
        if self.readme_busy or self.installing:
            wx.CallLater(500, self._offer_self_update, remote, asset)
            return
        self.self_update_offered = True
        if wx.MessageBox(
            f"Patcher {remote} is available. Download it and restart the patcher now?\n\n"
            "Choose No to continue using this patcher, including Download README.",
            "Patcher update", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self,
        ) == wx.YES:
            self.updating_patcher = True
            self.set_busy(True)
            self.readme_button.Disable()
            threading.Thread(target=self._self_update_worker, args=(asset,), daemon=True).start()

    def _self_update_worker(self, asset: dict) -> None:
        try:
            self._download_self_update(asset)
        except Exception as error:
            wx.CallAfter(self._self_update_failed, str(error))

    def _self_update_failed(self, error: str) -> None:
        self.updating_patcher = False
        self.set_busy(False)
        if not self.readme_busy:
            self.readme_button.Enable()
        self.announce(f"Patcher update failed: {error}")

    def _download_self_update(self, asset: dict) -> None:
        digest = asset["digest"]
        temp = Path(sys.executable + ".update")
        download(asset["browser_download_url"], temp)
        expected = digest.removeprefix("sha256:").lower()
        if sha256(temp) != expected:
            temp.unlink(missing_ok=True)
            raise RuntimeError("The patcher update failed its integrity check.")
        batch = Path(tempfile.gettempdir()) / "adcap_access_update.cmd"
        batch.write_text(
            "@echo off\r\n"
            "ping 127.0.0.1 -n 3 >nul\r\n"
            f'move /y "{temp}" "{sys.executable}" >nul\r\n'
            f'start "" "{sys.executable}"\r\n'
            'del "%~f0"\r\n',
            encoding="utf-8",
        )
        restart_env = os.environ.copy()
        restart_env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
        subprocess.Popen(
            ["cmd", "/c", str(batch)],
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=restart_env,
        )
        os._exit(0)

    def _check_done(self, generation: int, manifest: dict | None, message: str) -> None:
        if generation != self.check_generation:
            return
        self.manifest = manifest
        self.set_busy(False)
        self.announce(message)

    def start_install(self) -> None:
        if self.manifest is None:
            self.announce("No verified mod manifest is available. Select the game folder and wait for it to be checked.")
            return
        game_dir = Path(self.folder.GetValue().strip())
        manifest = self.manifest
        self.installing = True
        self.set_busy(True)
        self.gauge.SetValue(0)
        threading.Thread(target=self._install_worker, args=(game_dir, manifest), daemon=True).start()

    def _install_worker(self, game_dir: Path, manifest: dict) -> None:
        installer = Installer(
            game_dir,
            lambda text: wx.CallAfter(self.log.AppendText, text + "\n"),
            lambda value: wx.CallAfter(self.gauge.SetValue, value),
        )
        try:
            installer.install(manifest)
            wx.CallAfter(self._operation_done, "Installation complete. The accessibility mod is up to date.", True)
        except Exception as error:
            wx.CallAfter(self._operation_done, f"Installation failed: {error}")

    def on_restore(self, _event) -> None:
        if wx.MessageBox(
            "Restore the original game assembly and remove the accessibility mod?",
            APP_NAME,
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        ) != wx.YES:
            return
        game_dir = Path(self.folder.GetValue().strip())
        self.installing = True
        self.set_busy(True)
        threading.Thread(target=self._restore_worker, args=(game_dir,), daemon=True).start()

    def _restore_worker(self, game_dir: Path) -> None:
        installer = Installer(game_dir, lambda text: None, lambda value: None)
        try:
            installer.restore()
            wx.CallAfter(self._operation_done, "The original game files were restored.")
        except Exception as error:
            wx.CallAfter(self._operation_done, f"Restore failed: {error}")

    def _operation_done(self, message: str, offer_readme: bool = False) -> None:
        self.installing = False
        self.set_busy(False)
        self.announce(message)
        if offer_readme and not self.readme_busy and wx.MessageBox(
            "Would you like to save the gameplay README with the keyboard commands, screens, and event guide?",
            "Save gameplay README", wx.YES_NO | wx.ICON_QUESTION, self,
        ) == wx.YES:
            self.on_download_readme()


def main() -> None:
    app = wx.App(redirect=False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
