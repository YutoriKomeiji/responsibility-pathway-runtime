#!/usr/bin/env python3
"""Normalize a Python sdist tar.gz for byte-for-byte reproducible auditing."""
from __future__ import annotations

import argparse
import gzip
import io
import os
import tarfile
import tempfile
from pathlib import Path


def normalize_sdist(path: Path, *, source_date_epoch: int) -> None:
    if not path.name.endswith(".tar.gz"):
        raise ValueError(f"expected .tar.gz sdist: {path}")

    with tarfile.open(path, mode="r:gz") as source:
        members = sorted(source.getmembers(), key=lambda item: item.name)
        payloads: dict[str, bytes] = {}
        for member in members:
            if member.isfile():
                extracted = source.extractfile(member)
                if extracted is None:
                    raise ValueError(f"unable to read archive member: {member.name}")
                payloads[member.name] = extracted.read()

    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with temporary.open("wb") as raw:
            with gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=raw,
                compresslevel=9,
                mtime=source_date_epoch,
            ) as compressed:
                with tarfile.open(fileobj=compressed, mode="w", format=tarfile.GNU_FORMAT) as target:
                    for original in members:
                        normalized = tarfile.TarInfo(original.name)
                        normalized.type = original.type
                        normalized.mode = original.mode
                        normalized.mtime = source_date_epoch
                        normalized.uid = 0
                        normalized.gid = 0
                        normalized.uname = ""
                        normalized.gname = ""
                        normalized.linkname = original.linkname
                        normalized.devmajor = original.devmajor
                        normalized.devminor = original.devminor
                        normalized.pax_headers = {}
                        if original.isfile():
                            payload = payloads[original.name]
                            normalized.size = len(payload)
                            target.addfile(normalized, io.BytesIO(payload))
                        else:
                            normalized.size = 0
                            target.addfile(normalized)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sdist", type=Path)
    parser.add_argument("--source-date-epoch", type=int, required=True)
    args = parser.parse_args()
    normalize_sdist(args.sdist, source_date_epoch=args.source_date_epoch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
