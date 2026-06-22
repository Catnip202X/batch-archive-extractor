# Batch Archive Extractor

A small Windows-friendly extractor for password-protected `.rar`, `.zip`, and
`.7z` archives.

The user enters:

- one or more pieces of filename text to target specific archives
- one shared password to try for every matching archive

Matching archives are extracted into their current directory. The original
archive is deleted only after extraction succeeds.

## Requirements

- Python 3.10 or newer
- 7-Zip installed on Windows
- PyInstaller, only when building the `.exe`

The app looks for 7-Zip at:

```text
C:\Program Files\7-Zip\7z.exe
C:\Program Files (x86)\7-Zip\7z.exe
```

It also works if `7z.exe` is on `PATH`.

## Run From Source

```powershell
python batch_extract_gui.py
```

You can select archives from the GUI, or pass archive paths directly:

```powershell
python batch_extract_gui.py .\example_001.rar .\example_002.rar
```

When files are passed directly, the app prompts for filters and password before
extracting.

## Command-Line Batch Mode

```powershell
python archive_extractor.py . -f example -p "shared-password" --delete-after
```

Use multiple filters when filenames must contain more than one piece of text:

```powershell
python archive_extractor.py . -f example -f 2026 -p "shared-password" --delete-after
```

## Build Windows EXE

```powershell
python -m pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File .\build_windows_exe.ps1
```

The executable is created at:

```text
dist\BatchArchiveExtractor.exe
```

Drag matching archives onto `BatchArchiveExtractor.exe` to extract them in
place. The app will ask for filters and password first.

## Safety Notes

- Non-matching filenames are skipped.
- Archives are deleted only after the extractor exits successfully.
- Existing extracted files are skipped by default.
