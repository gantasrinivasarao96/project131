"""Safely extract source-code ZIP archives for Project 131."""

import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath


DEFAULT_MAX_FILES = 5000
DEFAULT_MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024


def extract_source_zip(
    archive_path: Path,
    destination: Path,
    *,
    max_files: int = DEFAULT_MAX_FILES,
    max_uncompressed_bytes: int = DEFAULT_MAX_UNCOMPRESSED_BYTES,
) -> Path:
    """Validate and extract a ZIP archive into a dedicated directory."""
    archive_path = Path(archive_path).expanduser().resolve()
    destination = Path(destination).expanduser().resolve()

    if not archive_path.is_file():
        raise FileNotFoundError(f"ZIP archive not found: {archive_path}")

    if max_files < 1 or max_uncompressed_bytes < 1:
        raise ValueError("Archive limits must be positive.")

    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Extraction destination must be empty.")

    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()

    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()

            if len(entries) > max_files:
                raise ValueError(
                    f"Archive contains too many entries: {len(entries)}"
                )

            total_size = 0
            validated_entries = []
            seen_paths = set()
            file_paths = set()
            directory_paths = set()

            for entry in entries:
                name = entry.filename

                if not name or "\x00" in name or "\\" in name:
                    raise ValueError(f"Unsafe ZIP entry path: {name!r}")

                is_directory = entry.is_dir()
                normalized_name = (
                    name[:-1] if is_directory and name.endswith("/") else name
                )
                parts = normalized_name.split("/")
                relative_path = PurePosixPath(normalized_name)

                if (
                    not normalized_name
                    or relative_path.is_absolute()
                    or any(part in ("", ".", "..") for part in parts)
                    or (parts and ":" in parts[0])
                ):
                    raise ValueError(f"Unsafe ZIP entry path: {name!r}")

                if normalized_name in seen_paths:
                    raise ValueError(
                        f"Duplicate ZIP entry path: {name!r}"
                    )
                seen_paths.add(normalized_name)

                target = (root / Path(*relative_path.parts)).resolve()

                if target != root and root not in target.parents:
                    raise ValueError(
                        f"ZIP entry escapes extraction destination: {name!r}"
                    )

                mode = entry.external_attr >> 16

                if stat.S_ISLNK(mode):
                    raise ValueError(
                        f"Symbolic links are not allowed: {name!r}"
                    )

                if entry.file_size < 0:
                    raise ValueError(
                        f"Invalid file size for ZIP entry: {name!r}"
                    )

                total_size += entry.file_size
                if total_size > max_uncompressed_bytes:
                    raise ValueError(
                        "Archive exceeds the uncompressed size limit."
                    )

                if is_directory:
                    directory_paths.add(normalized_name)
                else:
                    file_paths.add(normalized_name)

                validated_entries.append((entry, target, normalized_name))

            for file_name in file_paths:
                prefix = file_name + "/"
                if any(name.startswith(prefix) for name in seen_paths):
                    raise ValueError(
                        f"ZIP file conflicts with a directory path: {file_name!r}"
                    )

            for directory_name in directory_paths:
                if directory_name in file_paths:
                    raise ValueError(
                        f"ZIP path is both a file and directory: {directory_name!r}"
                    )

            for entry, target, _ in validated_entries:
                if entry.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue

                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)

        return root

    except (zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise ValueError(
            "The supplied file is not a valid ZIP archive."
        ) from exc
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
