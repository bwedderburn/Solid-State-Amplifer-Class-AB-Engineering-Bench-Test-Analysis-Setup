"""
Compatibility shim for pip-tools when running under pip >= 25.3.

GitHub's dependency submission workflow invokes ``pip-compile`` in a clean
environment.  pip-tools < 7.6 still expects ``InstallRequirement.use_pep517``
to exist, but pip 25.3 removed that attribute, causing the check to crash
before it can validate our requirements file.  Injecting a default keeps the
validation step working until the upstream toolchain settles.

This module is imported automatically by Python whenever it's present on
``sys.path`` (see :mod:`site`).  The shim is intentionally tiny and safe for
normal development flows.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from typing import TYPE_CHECKING, Any, cast

InstallRequirement: Any


def _ensure_pip_compatibility() -> None:
    if os.environ.get("AMPBENCHKIT_SKIP_PIP_FIX") == "1":
        return

    try:
        import pip  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - pip not available
        return

    version_parts = pip.__version__.split(".")
    try:
        major, minor = int(version_parts[0]), int(version_parts[1])
    except (ValueError, IndexError):
        return

    if (major, minor) < (25, 3):
        return

    env = dict(os.environ)
    env["AMPBENCHKIT_SKIP_PIP_FIX"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "pip<25.3"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )

    if result.returncode != 0:
        return

    # Drop cached pip modules so follow-up imports see the downgraded build.
    for name in [mod for mod in sys.modules if mod.startswith("pip")]:
        sys.modules.pop(name, None)
    importlib.invalidate_caches()

    pip = importlib.import_module("pip")  # type: ignore[import-not-found]
    version_parts = pip.__version__.split(".")
    try:
        major, minor = int(version_parts[0]), int(version_parts[1])
    except (ValueError, IndexError):
        return

    if (major, minor) >= (25, 3):
        # Downgrade did not take effect; bail out so we avoid recursion.
        os.environ.setdefault("AMPBENCHKIT_SKIP_PIP_FIX", "1")


_ensure_pip_compatibility()

try:
    from pip._internal.req.req_install import InstallRequirement
except ModuleNotFoundError:  # pragma: no cover - pip not available
    InstallRequirement = None


def _inject_use_pep517(req: Any) -> None:
    req.use_pep517 = False


if (
    InstallRequirement is not None
    and not TYPE_CHECKING
    and not hasattr(InstallRequirement, "use_pep517")
):
    # Pip < 25 exposed ``use_pep517``; pip >= 25.3 removed it.
    # pip-tools still checks for the attribute, so provide a benign default.
    _inject_use_pep517(cast(Any, InstallRequirement))

RequirementCommand: Any

try:
    from pip._internal.cli.req_command import RequirementCommand
except ModuleNotFoundError:  # pragma: no cover - pip not available
    RequirementCommand = None


def _shim_make_resolver(command: Any) -> Any:
    original = command.make_resolver  # classmethod descriptor

    def wrapper(cls: Any, *args: Any, **kwargs: Any) -> Any:
        kwargs.pop("use_pep517", None)
        return original.__func__(cls, *args, **kwargs)

    return classmethod(wrapper)


if RequirementCommand is not None and not TYPE_CHECKING:
    RequirementCommand.make_resolver = _shim_make_resolver(  # type: ignore[assignment]
        RequirementCommand
    )


def _patch_piptools_utils() -> None:
    try:
        from piptools import utils as piptools_utils  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - pip-tools absent
        return

    original = piptools_utils.copy_install_requirement

    def wrapper(template: Any, **extra_kwargs: Any) -> Any:
        if not hasattr(template, "use_pep517"):
            template.use_pep517 = False
        if "use_pep517" not in extra_kwargs:
            extra_kwargs["use_pep517"] = False
        return original(template, **extra_kwargs)

    piptools_utils.copy_install_requirement = wrapper  # type: ignore[assignment]


if not TYPE_CHECKING:
    _patch_piptools_utils()
