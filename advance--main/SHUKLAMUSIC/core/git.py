# -----------------------------------------------
# 🔸 StrangerMusic Project
# 🔹 Developed & Maintained by: Shashank Shukla (https://github.com/itzshukla)
# 📅 Copyright © 2022 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by ItzShukla
# -----------------------------------------------
#
# NOTE: The self-update-from-git feature needs the `git` command-line tool
# to be present on the host. Some deploy environments (e.g. Heroku when the
# app ends up on a buildpack stack instead of the container/Docker stack,
# or plain VPS setups without git installed) do not have it. Previously,
# `from git import Repo` at import time crashed the ENTIRE bot on startup
# with "Bad git executable" whenever that binary was missing. Now this is
# handled gracefully: if GitPython/git can't be used, we just log a warning
# and skip the self-update step instead of crashing the whole app.
# -----------------------------------------------
import asyncio
import shlex
from typing import Tuple

import config
from ..logging import LOGGER

try:
    from git import Repo
    from git.exc import GitCommandError, InvalidGitRepositoryError
    _GIT_AVAILABLE = True
except Exception as _git_import_error:  # covers ImportError from GitPython itself
    Repo = None
    GitCommandError = Exception
    InvalidGitRepositoryError = Exception
    _GIT_AVAILABLE = False
    _GIT_IMPORT_ERROR = _git_import_error


def install_req(cmd: str) -> Tuple[str, str, int, int]:
    async def install_requirements():
        args = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return (
            stdout.decode("utf-8", "replace").strip(),
            stderr.decode("utf-8", "replace").strip(),
            process.returncode,
            process.pid,
        )

    return asyncio.get_event_loop().run_until_complete(install_requirements())


def git():
    if not _GIT_AVAILABLE:
        LOGGER(__name__).warning(
            "Git executable not found or GitPython failed to load (%s). "
            "Skipping self-update check; the bot will continue starting normally.",
            _GIT_IMPORT_ERROR,
        )
        return

    REPO_LINK = config.UPSTREAM_REPO
    if config.GIT_TOKEN:
        GIT_USERNAME = REPO_LINK.split("com/")[1].split("/")[0]
        TEMP_REPO = REPO_LINK.split("https://")[1]
        UPSTREAM_REPO = f"https://{GIT_USERNAME}:{config.GIT_TOKEN}@{TEMP_REPO}"
    else:
        UPSTREAM_REPO = config.UPSTREAM_REPO
    try:
        repo = Repo()
        LOGGER(__name__).info(f"Git Client Found [VPS DEPLOYER]")
    except GitCommandError:
        LOGGER(__name__).info(f"Invalid Git Command")
    except InvalidGitRepositoryError:
        try:
            repo = Repo.init()
            if "origin" in repo.remotes:
                origin = repo.remote("origin")
            else:
                origin = repo.create_remote("origin", UPSTREAM_REPO)
            origin.fetch()
            repo.create_head(
                config.UPSTREAM_BRANCH,
                origin.refs[config.UPSTREAM_BRANCH],
            )
            repo.heads[config.UPSTREAM_BRANCH].set_tracking_branch(
                origin.refs[config.UPSTREAM_BRANCH]
            )
            repo.heads[config.UPSTREAM_BRANCH].checkout(True)
            try:
                repo.create_remote("origin", config.UPSTREAM_REPO)
            except BaseException:
                pass
            nrs = repo.remote("origin")
            nrs.fetch(config.UPSTREAM_BRANCH)
            try:
                nrs.pull(config.UPSTREAM_BRANCH)
            except GitCommandError:
                repo.git.reset("--hard", "FETCH_HEAD")
            install_req("pip3 install --no-cache-dir -r requirements.txt")
            LOGGER(__name__).info(f"Fetching updates from upstream repository...")
        except Exception as e:
            LOGGER(__name__).warning(
                "Self-update step failed (%s). Continuing startup without it.", e
            )
    except Exception as e:
        # Any other unexpected git-related failure should never take the
        # whole bot down — just log it and move on.
        LOGGER(__name__).warning(
            "Unexpected error during self-update check (%s). Continuing startup.", e
        )
