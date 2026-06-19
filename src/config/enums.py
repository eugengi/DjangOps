"""Enums for the config project.

Module to host all enumerations at the project-level.

Note:
    This module is not intended to host all Enums. Django apps should
    host and manage their own `enums.py` module for easier app deploys.
"""

from enum import StrEnum, auto, unique
from typing import NoReturn


class BaseStrEnum(StrEnum):
    """Base class for the project's enum string constants."""

    @classmethod
    def _missing_(cls, value: object) -> NoReturn:
        choices = ", ".join(map(str, cls))
        errmsg = f"""
            {value} is not a valid {cls.__name__}.
            Valid choices: {choices}
            """
        raise ValueError(errmsg)


@unique
class Environment(BaseStrEnum):
    """Target environment settings for the Django project."""

    DEVELOP = auto()
    TESTING = auto()
    STAGING = auto()
    PRODUCTION = auto()
