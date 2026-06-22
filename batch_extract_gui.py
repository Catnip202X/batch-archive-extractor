#!/usr/bin/env python3
"""GUI and drag-target wrapper for batch archive extraction."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

from archive_extractor import (
    extract_archive,
    filename_matches,
    find_extractor,
    is_supported_archive,
    parse_filter,
)


APP_TITLE = "Batch Archive Extractor"


def extract_and_delete(
    archives: list[Path],
    filters: list[str],
    password: str,
    log: callable | None = None,
) -> tuple[int, list[str]]:
    messages: list[str] = []
    success_count = 0

    def write(message: str) -> None:
        messages.append(message)
        if log:
            log(message)

    if not password:
        raise ValueError("Enter a password before extracting.")

    extractor = find_extractor()
    write(f"Using extractor: {extractor}")

    for archive in archives:
        archive = archive.expanduser().resolve()
        if not is_supported_archive(archive):
            write(f"Skipped unsupported file: {archive}")
            continue
        if not filename_matches(archive, filters):
            write(f"Skipped by filename filter: {archive}")
            continue

        destination = archive.parent
        write(f"Extracting: {archive.name}")
        extract_archive(
            extractor=extractor,
            archive=archive,
            destination=destination,
            password=password,
            overwrite=False,
        )
        archive.unlink()
        success_count += 1
        write(f"Extracted to {destination} and deleted {archive.name}")

    return success_count, messages


def show_result(success_count: int, messages: list[str]) -> None:
    detail = "\n".join(messages)
    if success_count:
        messagebox.showinfo(APP_TITLE, f"Finished {success_count} archive(s).\n\n{detail}")
    else:
        messagebox.showwarning(APP_TITLE, f"No archives were extracted.\n\n{detail}")


def run_dropped_files(paths: list[str]) -> int:
    root = tk.Tk()
    root.withdraw()

    app = DropSettingsDialog(root)
    root.wait_window(app.window)
    if not app.confirmed:
        return 0

    try:
        success_count, messages = extract_and_delete(
            [Path(path) for path in paths],
            app.filters,
            app.password,
        )
    except Exception as exc:
        messagebox.showerror(APP_TITLE, str(exc))
        return 1

    show_result(success_count, messages)
    return 0


class DropSettingsDialog:
    def __init__(self, root: tk.Tk) -> None:
        self.confirmed = False
        self.filters: list[str] = []
        self.password = ""

        self.window = tk.Toplevel(root)
        self.window.title(APP_TITLE)
        self.window.geometry("420x190")
        self.window.resizable(False, False)
        self.window.grab_set()

        frame = tk.Frame(self.window, padx=16, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Filename text to require, comma-separated:").pack(anchor="w")
        self.filter_entry = tk.Entry(frame)
        self.filter_entry.pack(fill=tk.X, pady=(4, 12))

        tk.Label(frame, text="Archive password:").pack(anchor="w")
        self.password_entry = tk.Entry(frame, show="*")
        self.password_entry.pack(fill=tk.X, pady=(4, 12))

        buttons = tk.Frame(frame)
        buttons.pack(fill=tk.X)
        tk.Button(buttons, text="Extract", command=self.accept).pack(side=tk.RIGHT)
        tk.Button(buttons, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=(0, 8))

        self.password_entry.focus_set()

    def accept(self) -> None:
        self.filters = parse_filter(self.filter_entry.get())
        self.password = self.password_entry.get()
        if not self.password:
            messagebox.showerror(APP_TITLE, "Enter an archive password.")
            return
        self.confirmed = True
        self.window.destroy()


class ExtractorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("680x430")
        self.root.minsize(560, 360)

        frame = tk.Frame(root, padx=16, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(
            frame,
            text="Select archives, enter filename filters, and reuse one password.",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        title.pack(fill=tk.X)

        settings = tk.Frame(frame)
        settings.pack(fill=tk.X, pady=(12, 10))

        tk.Label(settings, text="Filename contains:").grid(row=0, column=0, sticky="w")
        self.filter_entry = tk.Entry(settings)
        self.filter_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0))

        tk.Label(settings, text="Password:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.password_entry = tk.Entry(settings, show="*")
        self.password_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(8, 0))
        settings.columnconfigure(1, weight=1)

        button_frame = tk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(0, 12))

        tk.Button(button_frame, text="Select Archives", command=self.select_archives).pack(side=tk.LEFT)
        tk.Button(button_frame, text="Quit", command=root.destroy).pack(side=tk.LEFT, padx=(8, 0))

        self.log_box = scrolledtext.ScrolledText(frame, height=12, state=tk.DISABLED)
        self.log_box.pack(fill=tk.BOTH, expand=True)

    def log(self, message: str) -> None:
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.configure(state=tk.DISABLED)
        self.log_box.see(tk.END)
        self.root.update_idletasks()

    def select_archives(self) -> None:
        filenames = filedialog.askopenfilenames(
            title="Select archives",
            filetypes=(("Supported archives", "*.rar *.zip *.7z"), ("All files", "*.*")),
        )
        if not filenames:
            return

        try:
            success_count, messages = extract_and_delete(
                [Path(filename) for filename in filenames],
                parse_filter(self.filter_entry.get()),
                self.password_entry.get(),
                log=self.log,
            )
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))
            return

        show_result(success_count, messages)


def main() -> int:
    if len(sys.argv) > 1:
        return run_dropped_files(sys.argv[1:])

    root = tk.Tk()
    ExtractorApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
