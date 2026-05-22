from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

PACKAGE_NAME = "europassxml-to-reactiveresumejson"

try:
    __version__ = version(PACKAGE_NAME)
except PackageNotFoundError:
    __version__ = "0.1.0+local"
