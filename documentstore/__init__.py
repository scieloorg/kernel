import warnings


warnings.filterwarnings(
    "ignore",
    message=r"pkg_resources is deprecated as an API\.",
    category=UserWarning,
)

warnings.filterwarnings(
    "ignore",
    message=r"datetime\.datetime\.utcnow\(\) is deprecated.*",
    category=DeprecationWarning,
)
