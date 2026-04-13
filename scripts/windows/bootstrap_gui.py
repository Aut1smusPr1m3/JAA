import os
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext


def build_bootstrap_command(
    repo_root: Path,
    install_dev: bool,
    install_open3d: bool,
    skip_tests: bool,
    venv_path: str,
    arcwelder_path: str,
    arcwelder_url: str,
) -> list[str]:
    script = repo_root / "scripts" / "windows" / "bootstrap.ps1"
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-VenvPath",
        venv_path or ".venv",
    ]

    if install_dev:
        cmd.append("-InstallDev")
    if not install_open3d:
        cmd.append("-InstallOpen3D:$false")
    if skip_tests:
        cmd.append("-SkipTests")

    if arcwelder_path.strip():
        cmd.extend(["-ArcWelderPath", arcwelder_path.strip()])
    elif arcwelder_url.strip():
        cmd.extend(["-ArcWelderUrl", arcwelder_url.strip()])

    return cmd


class BootstrapGui(tk.Tk):
    def __init__(self, repo_root: Path):
        super().__init__()
        self.repo_root = repo_root
        self.title("Ultra_Optimizer Windows Bootstrap GUI")
        self.geometry("920x620")

        self.install_dev = tk.BooleanVar(value=True)
        self.install_open3d = tk.BooleanVar(value=True)
        self.skip_tests = tk.BooleanVar(value=False)
        self.venv_path = tk.StringVar(value=".venv")
        self.arcwelder_path = tk.StringVar(value="")
        self.arcwelder_url = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self) -> None:
        frm = tk.Frame(self)
        frm.pack(fill=tk.X, padx=12, pady=8)

        tk.Checkbutton(frm, text="Install dev dependencies", variable=self.install_dev).grid(
            row=0, column=0, sticky="w"
        )
        tk.Checkbutton(frm, text="Install Open3D (optional Stage 2)", variable=self.install_open3d).grid(
            row=1, column=0, sticky="w"
        )
        tk.Checkbutton(frm, text="Skip tests", variable=self.skip_tests).grid(
            row=2, column=0, sticky="w"
        )

        tk.Label(frm, text="Venv path:").grid(row=3, column=0, sticky="w", pady=(8, 0))
        tk.Entry(frm, textvariable=self.venv_path, width=36).grid(row=3, column=1, sticky="w", pady=(8, 0))

        tk.Label(frm, text="ArcWelder local path (optional):").grid(row=4, column=0, sticky="w", pady=(8, 0))
        tk.Entry(frm, textvariable=self.arcwelder_path, width=60).grid(row=4, column=1, sticky="w", pady=(8, 0))
        tk.Button(frm, text="Browse", command=self._browse_arcwelder).grid(row=4, column=2, padx=6, pady=(8, 0))

        tk.Label(frm, text="ArcWelder URL (optional):").grid(row=5, column=0, sticky="w", pady=(8, 0))
        tk.Entry(frm, textvariable=self.arcwelder_url, width=60).grid(row=5, column=1, sticky="w", pady=(8, 0))

        action_row = tk.Frame(self)
        action_row.pack(fill=tk.X, padx=12, pady=6)
        tk.Button(action_row, text="Run bootstrap", command=self._run_bootstrap, bg="#0f766e", fg="white").pack(
            side=tk.LEFT
        )

        self.log = scrolledtext.ScrolledText(self, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self._write_log(f"Repo root: {self.repo_root}\n")

    def _browse_arcwelder(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select ArcWelder.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        )
        if file_path:
            self.arcwelder_path.set(file_path)

    def _write_log(self, text: str) -> None:
        self.log.insert(tk.END, text)
        self.log.see(tk.END)

    def _run_bootstrap(self) -> None:
        if self.arcwelder_path.get().strip() and self.arcwelder_url.get().strip():
            messagebox.showerror(
                "Invalid input",
                "Provide either ArcWelder path OR ArcWelder URL, not both.",
            )
            return

        cmd = build_bootstrap_command(
            repo_root=self.repo_root,
            install_dev=self.install_dev.get(),
            install_open3d=self.install_open3d.get(),
            skip_tests=self.skip_tests.get(),
            venv_path=self.venv_path.get(),
            arcwelder_path=self.arcwelder_path.get(),
            arcwelder_url=self.arcwelder_url.get(),
        )
        self._write_log("\n=== Running bootstrap ===\n")
        self._write_log("Command: " + " ".join(cmd) + "\n\n")

        thread = threading.Thread(target=self._run_process, args=(cmd,), daemon=True)
        thread.start()

    def _run_process(self, cmd: list[str]) -> None:
        proc = subprocess.Popen(
            cmd,
            cwd=str(self.repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        assert proc.stdout is not None
        for line in proc.stdout:
            self.after(0, self._write_log, line)

        code = proc.wait()
        if code == 0:
            self.after(0, self._write_log, "\n[SUCCESS] Bootstrap completed.\n")
        else:
            self.after(0, self._write_log, f"\n[FAILED] Bootstrap exited with code {code}.\n")


def main() -> None:
    if os.name != "nt":
        raise SystemExit("bootstrap_gui.py is intended for Windows hosts.")

    repo_root = Path(__file__).resolve().parents[2]
    app = BootstrapGui(repo_root=repo_root)
    app.mainloop()


if __name__ == "__main__":
    main()
