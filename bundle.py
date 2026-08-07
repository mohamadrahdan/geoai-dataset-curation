from __future__ import annotations
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_ROOT / "project_bundle.txt"

INCLUDED_SUFFIXES = {
    ".py",
    ".md",
    ".toml",
    ".yml",
    ".yaml",
    ".json",
    ".txt",
}

INCLUDED_FILENAMES = {
    ".gitignore",
    ".env.example",
    "Dockerfile",
}

EXCLUDED_DIRECTORIES = {
    ".git",
    ".github",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
}

EXCLUDED_FILENAMES = {
    ".env",
    "project_bundle.txt",
}

EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".log",
    ".sqlite",
    ".db",
}


def should_include(path: Path) -> bool:
    relative_path = path.relative_to(PROJECT_ROOT)
    if any(
        part.startswith(".venv")
        for part in relative_path.parts
    ):
        return False

    if any(
        part in EXCLUDED_DIRECTORIES
        for part in relative_path.parts
    ):
        return False

    if path.name in EXCLUDED_FILENAMES:
        return False

    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False

    if path.name in INCLUDED_FILENAMES:
        return True

    return path.suffix.lower() in INCLUDED_SUFFIXES


def collect_files() -> list[Path]:
    "Collect eligible files in deterministic order"
    return sorted(
        (
            path
            for path in PROJECT_ROOT.rglob("*")
            if path.is_file() and should_include(path)
        ),
        key=lambda path: path.relative_to(PROJECT_ROOT).as_posix(),
    )


def read_text_safely(path: Path) -> str:
    "Read a text file with a clear fallback for decoding failures"
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(
            encoding="utf-8",
            errors="replace",
        )


def build_bundle(files: list[Path]) -> str:
    "Build the complete repository bundle"
    generated_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    sections = [
        "# Repository Bundle",
        "",
        f"Project: {PROJECT_ROOT.name}",
        f"Generated at: {generated_at}",
        f"Included files: {len(files)}",
        "",
        "=" * 88,
        "PROJECT TREE",
        "=" * 88,
        "",
    ]

    sections.extend(
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in files
    )

    for path in files:
        relative_path = path.relative_to(
            PROJECT_ROOT
        ).as_posix()
        content = read_text_safely(path)

        sections.extend(
            [
                "",
                "=" * 88,
                f"FILE: {relative_path}",
                "=" * 88,
                "",
                content.rstrip(),
                "",
            ]
        )

    return "\n".join(sections)


def main() -> None:
    "Generate the repository bundle"
    files = collect_files()
    bundle = build_bundle(files)

    OUTPUT_PATH.write_text(
        bundle,
        encoding="utf-8",
    )

    print(f"Bundle created: {OUTPUT_PATH}")
    print(f"Included files: {len(files)}")
    print(
        f"Bundle size: {OUTPUT_PATH.stat().st_size:,} bytes"
    )


if __name__ == "__main__":
    main()