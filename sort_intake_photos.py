#!/usr/bin/env python3
"""
EAK Intake Sorter
==================
Takes the flat batch of photos the phone capture tool downloaded
(named like 197555416698_1.jpg, 197555416698_2.jpg, ...) and sorts
them into intake/<barcode>/ folders automatically. Run this once
after transferring a batch from your phone to the laptop.

USAGE
-----
    python3 sort_intake_photos.py <downloaded_photos_folder> <intake_folder>

Example:
    python3 sort_intake_photos.py ~/Downloads eak-catalog/intake

Only touches files matching the "<barcode>_<number>.<ext>" pattern —
anything else in the source folder is left alone and never moved, so
it's safe to point at a real Downloads folder with unrelated files in it.

Also handles two phone quirks automatically:
- Browser duplicate renames like "197555416698_1 (1).jpg" are
  recognized and sorted correctly instead of being skipped.
- iPhone HEIC/HEIF photos are sorted like any other image, and a note
  is printed listing them, since some downstream tools prefer JPEG
  (Claude Code can convert them if needed).
"""

import re
import shutil
import sys
from pathlib import Path

# barcode _ number [optional " (n)" browser-duplicate suffix] . extension
PATTERN = re.compile(
    r"^(.+?)_(\d+)(?:\s*\(\d+\))?\.(jpg|jpeg|png|webp|heic|heif)$",
    re.IGNORECASE,
)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    source = Path(sys.argv[1])
    intake = Path(sys.argv[2])

    if not source.is_dir():
        print(f"Not a folder: {source}")
        sys.exit(1)
    intake.mkdir(parents=True, exist_ok=True)

    moved = {}
    skipped = 0
    heic_files = []

    for f in sorted(source.iterdir()):
        if not f.is_file():
            continue
        m = PATTERN.match(f.name)
        if not m:
            skipped += 1
            continue

        barcode, num, ext = m.groups()
        ext = ext.lower()
        dest_dir = intake / barcode
        dest_dir.mkdir(exist_ok=True)

        # Never clobber: find the next free photo number in the folder,
        # counting every image already there regardless of extension.
        existing = [p for p in dest_dir.iterdir()
                    if p.is_file() and PATTERN_EXT.match(p.name)]
        next_num = len(existing) + 1
        dest_path = dest_dir / f"photo{next_num}.{ext}"
        while dest_path.exists():
            next_num += 1
            dest_path = dest_dir / f"photo{next_num}.{ext}"

        shutil.move(str(f), str(dest_path))
        moved[barcode] = moved.get(barcode, 0) + 1
        if ext in ("heic", "heif"):
            heic_files.append(str(dest_path))

    print(f"Sorted {sum(moved.values())} photo(s) into {len(moved)} product folder(s):\n")
    for barcode, count in sorted(moved.items()):
        print(f"  {barcode} — {count} photo(s)")
    if skipped:
        print(f"\n{skipped} file(s) in the source folder didn't match the "
              f"barcode_number.ext pattern and were left untouched.")
    if heic_files:
        print(f"\nNote: {len(heic_files)} photo(s) are HEIC/HEIF (iPhone format). "
              f"They sorted fine, but if any downstream tool can't read them, "
              f"ask Claude Code to convert them to JPEG:")
        for p in heic_files:
            print(f"  {p}")


# matches photoN.<any supported image extension> inside a destination folder
PATTERN_EXT = re.compile(r"^photo\d+\.(jpg|jpeg|png|webp|heic|heif)$", re.IGNORECASE)


if __name__ == "__main__":
    main()
