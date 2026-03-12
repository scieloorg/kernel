from importlib.metadata import PackageNotFoundError, version


def get_version() -> str:
    try:
        return version("scielo-kernel")
    except PackageNotFoundError:
        return "0+unknown"
