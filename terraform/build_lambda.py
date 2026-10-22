from pathlib import Path
import shutil
import subprocess
import sys


PACKAGE_DIRECTORY = Path(__file__).parent / "lambda-package"
SOURCE_DIRECTORY = Path(__file__).parent.parent / "src" / "flashcardApp"
REQUIREMENTS_FILE = Path(__file__).parent / "lambda-requirements.txt"


def main() -> None:
    if PACKAGE_DIRECTORY.exists():
        shutil.rmtree(PACKAGE_DIRECTORY)
    PACKAGE_DIRECTORY.mkdir()

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--target",
            str(PACKAGE_DIRECTORY),
            "-r",
            str(REQUIREMENTS_FILE),
        ],
        check=True,
    )

    for source_file in SOURCE_DIRECTORY.glob("*.py"):
        shutil.copy2(source_file, PACKAGE_DIRECTORY / source_file.name)


if __name__ == "__main__":
    main()
