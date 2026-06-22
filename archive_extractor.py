#!/usr/bin/env python3
"""Extract archives selected by filename filters."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ARCHIVE_EXTENSIONS = (".rar", ".zip", ".7z")


def parse_filter(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract archives whose filenames contain chosen text."
    )
    parser.add_argument("source", nargs="?", default=".", type=Path)
    parser.add_argument(
        "-f",
        "--filter",
        action="append",
        default=[],
        help="Required filename text. Can be repeated or comma-separated.",
    )
    parser.add_argument(
        "-p",
        "--password",
        default="",
        help="Optional password to use for every matching archive.",
    )
    parser.add_argument("-o", "--output-dir", default=None, type=Path)
    parser.add_argument("-r", "--recursive", action="store_true")
    parser.add_argument("--flat", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--delete-after", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def find_extractor() -> str:
    for executable in ("7z", "7zz", "7za", "unar", "unrar"):
        path = shutil.which(executable)
        if path:
            return path

    for path in (
        Path("C:/Program Files/7-Zip/7z.exe"),
        Path("C:/Program Files (x86)/7-Zip/7z.exe"),
    ):
        if path.exists():
            return str(path)

    raise RuntimeError(
        "No supported extractor found. Install 7-Zip, or add 7z.exe to PATH."
    )


def is_supported_archive(path: Path) -> bool:
    return path.is_file() and path.name.lower().endswith(ARCHIVE_EXTENSIONS)


def filename_matches(path: Path, filters: list[str], match_all: bool = True) -> bool:
    if not filters:
        return True

    filename = path.name.casefold()
    normalized_filters = [item.casefold() for item in filters]
    if match_all:
        return all(item in filename for item in normalized_filters)
    return any(item in filename for item in normalized_filters)


def is_matching_archive(path: Path, filters: list[str], match_all: bool = True) -> bool:
    return is_supported_archive(path) and filename_matches(path, filters, match_all)


def iter_archives(
    source: Path,
    filters: list[str],
    recursive: bool,
    match_all: bool = True,
) -> list[Path]:
    if source.is_file():
        return [source] if is_matching_archive(source, filters, match_all) else []
    if not source.is_dir():
        raise FileNotFoundError(f"Source does not exist: {source}")

    pattern = "**/*" if recursive else "*"
    return sorted(
        path for path in source.glob(pattern) if is_matching_archive(path, filters, match_all)
    )


def output_path_for(archive: Path, output_dir: Path | None, flat: bool) -> Path:
    if output_dir is None:
        return archive.parent
    return output_dir if flat else output_dir / archive.stem


def extraction_command(
    extractor: str,
    archive: Path,
    destination: Path,
    password: str,
    overwrite: bool,
) -> list[str]:
    executable = Path(extractor).name.lower()
    if executable.endswith(".exe"):
        executable = executable[:-4]

    if executable in {"7z", "7zz", "7za"}:
        overwrite_mode = "-aoa" if overwrite else "-aos"
        command = [
            extractor,
            "x",
            str(archive),
            "-y",
            overwrite_mode,
            f"-o{destination}",
        ]
        if password:
            command.insert(3, f"-p{password}")
        return command

    if executable == "unar":
        command = [extractor, "-output-directory", str(destination)]
        if password:
            command[1:1] = ["-password", password]
        command.append("-force-overwrite" if overwrite else "-skip")
        command.append(str(archive))
        return command

    if executable == "unrar":
        overwrite_mode = "-o+" if overwrite else "-o-"
        command = [extractor, "x", overwrite_mode]
        if password:
            command.append(f"-p{password}")
        command.extend([str(archive), str(destination)])
        return command

    raise RuntimeError(f"Unsupported extractor: {extractor}")


def extract_archive(
    extractor: str,
    archive: Path,
    destination: Path,
    password: str,
    overwrite: bool,
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    command = extraction_command(extractor, archive, destination, password, overwrite)
    completed = subprocess.run(command, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Extraction failed for {archive} with exit code {completed.returncode}")


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve() if args.output_dir else None
    filters = [item for value in args.filter for item in parse_filter(value)]
    archives = iter_archives(source, filters, args.recursive)

    if not archives:
        print(f"No matching archives found in {source}")
        return 0

    print("Matching archives:")
    for archive in archives:
        print(f"  {archive}")

    if args.dry_run:
        return 0

    extractor = find_extractor()
    print(f"Using extractor: {extractor}")

    for archive in archives:
        destination = output_path_for(archive, output_dir, args.flat)
        print(f"Extracting {archive.name} -> {destination}")
        extract_archive(extractor, archive, destination, args.password, args.overwrite)
        if args.delete_after:
            archive.unlink()
            print(f"Deleted {archive}")

    print("Done.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
