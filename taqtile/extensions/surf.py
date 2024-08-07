import os
import subprocess
import re
from datetime import datetime
from functools import lru_cache
from getpass import getuser
from os.path import dirname, join, splitext, expanduser, isdir, pathsep
from urllib.parse import quote_plus

from libqtile import hook
from libqtile.extension.dmenu import Dmenu, DmenuRun
from libqtile.extension.window_list import WindowList
from plumbum import local

import logging
from taqtile.recent_runner import RecentRunner
from taqtile.system import (
    get_current_window,
    get_hostconfig,
    window_exists,
    get_current_screen,
    get_current_group,
    get_redis,
)
from taqtile.extensions.base import WindowGroupList

logger = logging.getLogger("taqtile")

SURF_HISTORY_DB = "qtile_surf"
surf_recent_runner = RecentRunner(SURF_HISTORY_DB)
BROWSER_MAP = {
    "twitter.com": "qutebrowser",
}
BROWSERS = {
    "brave": {"args": "--profile-directory=%(profile)s"},
    "firefox": {"args": "-P %(profile)s"},
    "surf": {},
    "qutebrowser": {},
}


@hook.subscribe.client_name_updated
def save_history(client):
    uri = None
    try:
        uri = getattr(
            client.window.get_property("_SURF_URI", "UTF8_STRING"),
            "value",
            None,
        )
        if uri:
            uri = uri.to_utf8()
            logger.info(uri)
            # surf_recent_runner.insert(uri)

    except AttributeError:
        logger.exception("failed to get uri updated ")


class Surf(WindowGroupList):
    """
    Give vertical list of all open windows in dmenu. Switch to selected.
    """

    show_icons = True
    dmenu_prompt = "Surf"
    recent_runner = surf_recent_runner
    dbname = SURF_HISTORY_DB
    GROUP = "surf"
    item_to_win = {}

    defaults = [
        ("item_format", "* {window}", "the format for the menu items"),
        (
            "all_groups",
            True,
            "If True, list windows from all groups; otherwise only from the current group",
        ),
        ("dmenu_lines", "80", "Give lines vertically. Set to None get inline"),
    ]

    def _configure(self, qtile):
        Dmenu._configure(self, qtile)
        self.configured_command.insert(1, "-multi-select")
        if self.show_icons:
            self.configured_command.insert(1, "-show-icons")
            self.configured_command.insert(2, "-icon-theme")
            self.configured_command.insert(3, "breeze-dark")
        logger.debug(f"configured_command: {self.configured_command}")

    def list_windows(self):
        items = super().list_windows()
        clip = []
        try:
            clip.append(
                f"clipboard: "
                + subprocess.check_output(["xclip", "-o"]).decode()
            )
        except Exception as e:
            logger.exception(f"exception getting clip: {e}")
        clip.extend(items)
        return clip

    def match_item(self, win):
        # logger.info(dir(win.window))
        if win.window.get_wm_class()[0] != "surf":
            return
        return self.item_format.format(
            group=win.group.label or win.group.name,
            id=id,
            window=win.name.split("|", 1)[-1],
        )

    def spawn(self, sout):
        sout = sout.strip()
        if sout.startswith("bookmarks:"):
            sout = self.run("cat ~/.bookmarks|dmenu ")
        if sout.startswith("clipboard:"):
            sout = sout.split("clipboard:")[-1].strip()

        url = ""
        for tld in [".com", ".org"]:
            if sout.endswith(tld) and not sout.startswith("http:"):
                url = "https://" + sout
                break
        if sout.endswith(".com"):
            url = sout
        elif sout.startswith("http"):
            url = sout.strip()
        elif sout:
            gg = "gg "
            if sout.startswith(gg):
                sout = sout.split(gg)[-1]
                url = "https://www.google.com/search?q='%s'&ie=utf-8&oe=utf-8"
            else:
                url = (
                    "https://duckduckgo.com/?t=ffab&q=%s&ia=web&kae=d&ks=l&kw=s"
                )
            url = url % quote_plus(sout)
        # self.qtile.spawn(f"systemd-run --user surf {url}")
        self.qtile.spawn(f"surf {url}")
