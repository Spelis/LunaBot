import pathlib

builtin_directory = (
    pathlib.Path(__file__).parent.resolve().relative_to(pathlib.Path.cwd().resolve())
)


def path_as_import_prefix(path: pathlib.Path):
    return path.as_posix().replace("/", ".")
