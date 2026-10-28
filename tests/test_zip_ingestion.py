import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from src.ingestion.zip_ingestion import extract_source_zip


def test_extracts_valid_zip():
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        archive_path = root / "source.zip"
        destination = root / "extracted"

        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("project/main.py", "print('hello')\n")
            archive.writestr("project/utils.py", "VALUE = 1\n")

        result = extract_source_zip(archive_path, destination)

        assert (result / "project/main.py").read_text() == "print('hello')\n"
        assert (result / "project/utils.py").read_text() == "VALUE = 1\n"

    print("PASS: Valid ZIP extracted.")


def test_rejects_path_traversal():
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        archive_path = root / "malicious.zip"
        destination = root / "extracted"
        outside_file = root / "outside.txt"

        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("../outside.txt", "unsafe")

        try:
            extract_source_zip(archive_path, destination)
        except ValueError as exc:
            assert "Unsafe ZIP entry path" in str(exc)
        else:
            raise AssertionError("Expected path traversal rejection.")

        assert not outside_file.exists()
        assert (
            not destination.exists()
            or not any(destination.iterdir())
        )

    print("PASS: Path traversal rejected.")


def test_rejects_invalid_zip():
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        archive_path = root / "invalid.zip"
        archive_path.write_text("not a ZIP archive")
        destination = root / "extracted"

        try:
            extract_source_zip(archive_path, destination)
        except ValueError as exc:
            assert "valid ZIP" in str(exc)
        else:
            raise AssertionError("Expected invalid ZIP rejection.")

    print("PASS: Invalid ZIP rejected.")


def test_enforces_entry_limit():
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        archive_path = root / "many.zip"

        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("a.py", "a")
            archive.writestr("b.py", "b")

        try:
            extract_source_zip(
                archive_path,
                root / "extracted",
                max_files=1,
            )
        except ValueError as exc:
            assert "too many entries" in str(exc)
        else:
            raise AssertionError("Expected entry-count limit.")

    print("PASS: ZIP entry-count limit enforced.")


def test_enforces_uncompressed_size_limit():
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        archive_path = root / "large.zip"

        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("large.txt", "x" * 100)

        try:
            extract_source_zip(
                archive_path,
                root / "extracted",
                max_uncompressed_bytes=10,
            )
        except ValueError as exc:
            assert "size limit" in str(exc)
        else:
            raise AssertionError("Expected uncompressed-size limit.")

    print("PASS: Uncompressed-size limit enforced.")




def test_rejects_symbolic_links():
    import stat

    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        archive_path = root / "symlink.zip"

        info = zipfile.ZipInfo("project/link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16

        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr(info, "../outside.txt")

        try:
            extract_source_zip(archive_path, root / "extracted")
        except ValueError as exc:
            assert "Symbolic links are not allowed" in str(exc)
        else:
            raise AssertionError("Expected symbolic link rejection.")

    print("PASS: Symbolic links rejected.")


def test_rejects_duplicate_file_paths():
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        archive_path = root / "duplicates.zip"

        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("project/main.py", "first")
            archive.writestr("project/main.py", "second")

        try:
            extract_source_zip(archive_path, root / "extracted")
        except ValueError as exc:
            assert "Duplicate ZIP entry path" in str(exc)
        else:
            raise AssertionError("Expected duplicate path rejection.")

    print("PASS: Duplicate file paths rejected.")




def test_accepts_explicit_directory_entries():
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        archive_path = root / "directories.zip"

        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("project/", "")
            archive.writestr("project/main.py", "print('hello')")

        extracted = extract_source_zip(archive_path, root / "extracted")
        assert (extracted / "project" / "main.py").is_file()

    print("PASS: Explicit directory entries accepted.")


def test_rejects_file_directory_conflict():
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        archive_path = root / "conflict.zip"

        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("project", "a file")
            archive.writestr("project/main.py", "a child file")

        try:
            extract_source_zip(archive_path, root / "extracted")
        except ValueError as exc:
            assert "conflicts" in str(exc) or "both a file and directory" in str(exc)
        else:
            raise AssertionError("Expected file/directory conflict rejection.")

    print("PASS: File/directory conflicts rejected.")


if __name__ == "__main__":
    test_extracts_valid_zip()
    test_rejects_path_traversal()
    test_rejects_invalid_zip()
    test_enforces_entry_limit()
    test_enforces_uncompressed_size_limit()
    test_rejects_symbolic_links()
    test_rejects_duplicate_file_paths()
    test_accepts_explicit_directory_entries()
    test_rejects_file_directory_conflict()

