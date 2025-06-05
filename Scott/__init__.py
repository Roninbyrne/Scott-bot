from Scott.core.dir import dirr
from Scott.core.git import git
from Scott.core.bot import app
from Scott.core.bot import start_bot

from .logging import LOGGER

dirr()
git()

__all__ = ["app", "start_bot"]