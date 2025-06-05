import pathlib

builtin_banner_path: pathlib.Path | None = pathlib.Path(__file__).parent.joinpath(
    "banner.txt"
)
if builtin_banner_path.exists():
    builtin_banner_path = builtin_banner_path.resolve().relative_to(
        pathlib.Path.cwd().resolve()
    )
else:
    builtin_banner_path = None


def get_banner_text() -> str | None:
    """
    Reads the contents of a banner.txt file if it exists.

    The banner is looked up in the same directory as this file. If the file
    exists, the contents are read and returned as a string. Otherwise, None
    is returned.

    Returns:
        str | None: The banner text if the file exists, otherwise None.
    """
    from .config import settings

    banner_path = settings.banner_file
    if banner_path is None:
        return None
    if banner_path.exists():
        return banner_path.read_text(encoding="utf-8")
    return None
