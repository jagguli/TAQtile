import os
import re
from datetime import datetime
from functools import lru_cache
from getpass import getuser
from os.path import dirname, join, splitext, expanduser, isdir, pathsep
from subprocess import Popen
from urllib.parse import quote_plus

from libqtile import hook
from libqtile.extension.dmenu import Dmenu, DmenuRun

from libqtile.extension.window_list import WindowList as QWindowList
from libqtile.scratchpad import ScratchPad

from libqtile.backend import base

# from libqtile.extension.window_list import WindowList
from plumbum import local

from taqtile.log import logger
from taqtile.recent_runner import RecentRunner
from taqtile.system import (
    get_current_window,
    get_hostconfig,
    window_exists,
    get_current_screen,
    get_current_group,
    get_redis,
)
from taqtile.groups import Rule, Match

from .surf import Surf  # flake8: noqa
from .kubectl import KubeCtl


@hook.subscribe.client_new
def set_timestamp(window):
    window.window.set_property(
        "QTILE_CREATED", int(datetime.now().timestamp()), type="ATOM", format=32
    )


class WindowList(QWindowList):
    def run(self):
        self.list_windows()
        window_list = []
        for key, item in self.item_to_win.items():
            created = item.window.get_property(
                "QTILE_CREATED", type="ATOM", unpack=int
            )
            if created:
                created = created[0]
            window_list.append((created, key))

            logger.debug(f"window_list: {item} {created}")
        out = Dmenu.run(
            self,
            items=[
                x[-1]
                for x in sorted(window_list, key=lambda x: x[0], reverse=True)
            ],
        )

        try:
            sout = out.rstrip("\n")
        except AttributeError:
            # out is not a string (for example it's a Popen object returned
            # by super(WindowList, self).run() when there are no menu items to
            # list
            return

        try:
            win = self.item_to_win[sout]
        except KeyError:
            # The selected window got closed while the menu was open?
            logger.warning("no window found %s" % sout)
            return
        logger.debug(
            f"window found {win} {win.group}: {self.qtile.current_group}"
        )

        if self.qtile.current_group.name != win.group.name:
            screen = self.qtile.current_screen
            screen.set_group(win.group)
        win.group.focus(win, force=True)
        # win.cmd_focus()


@lru_cache()
def list_executables(ttl_hash=None):
    del ttl_hash
    logger.error("getting execs")
    paths = os.environ["PATH"].split(pathsep)
    executables = []
    for path in filter(isdir, paths):
        for file_ in os.listdir(path):
            if os.access(join(path, file_), os.X_OK):
                executables.append(file_)
    return set(executables)


class KillWindows(Dmenu):
    defaults = [
        (
            "item_format",
            "{group}.{id}: {window}",
            "the format for the menu items",
        ),
        (
            "all_groups",
            True,
            "If True, list windows from all groups; otherwise only from the current group",
        ),
        ("dmenu_lines", "80", "Give lines vertically. Set to None get inline"),
    ]

    def __init__(self, **config):
        Dmenu.__init__(self, **config)
        self.add_defaults(KillWindows.defaults)

    def list_windows(self):
        id = 0
        self.item_to_win = {}

        if self.all_groups:
            windows = [
                w
                for w in self.qtile.windows_map.values()
                if isinstance(w, base.Window)
            ]
        else:
            windows = self.qtile.current_group.windows

        for win in windows:
            if win.group and not isinstance(win.group, ScratchPad):
                item = self.item_format.format(
                    group=win.group.label or win.group.name,
                    id=id,
                    window=win.name,
                )
                self.item_to_win[item] = win
                id += 1

    def run(self):
        self.list_windows()
        self.dmenu_prompt = "Kill selected windows <Ctrk-Ret> to select:"
        self._configure(self.qtile)
        windows = super().run(items=self.item_to_win.keys()).split("\n")

        logger.debug("selected killing window: %s", windows)
        for win in windows:
            win = win.strip()
            if not win:
                continue
            self.dmenu_prompt = "Kill %s" % win
            self._configure(self.qtile)
            if (
                Dmenu.run(self, items=["confirm", "cancel"]).strip()
                == "confirm"
            ):
                try:
                    win = self.item_to_win[win]
                except KeyError:
                    logger.warning("window not found %s", win)
                    # The selected window got closed while the menu was open?
                else:
                    logger.debug("killing window: %s", win)
                    win.cmd_kill()


class BringWindowToGroup(WindowList):
    def run(self):
        self.list_windows()
        logger.debug("running summon window")
        items = list(self.item_to_win.keys())
        logger.debug("running summon window %s", items)
        out = super().run()
        logger.debug("running summon window %s", out)

        try:
            sout = out.rstrip("\n")
        except AttributeError:
            # out is not a string (for example it's a Popen object returned
            # by super(WindowList, self).run() when there are no menu items to
            # list
            return

        try:
            win = self.item_to_win[sout]
        except KeyError:
            # The selected window got closed while the menu was open?
            return

        screen = self.qtile.current_screen
        win.cmd_togroup(screen.group)
        # screen.set_group(win.group)
        win.group.focus(win)


class History(Dmenu):
    pass


class SessionActions(Dmenu):
    actions = {
        "lock": "gnome-screensaver-command --lock ;;",
        "logout": "loginctl terminate-user %s" % getuser(),
        "shutdown": 'gksu "shutdown -h now" & ;;',
        "reboot": 'gksu "shutdown -r now" & ;;',
        "suspend": "gksu pm-suspend && gnome-screensaver-command --lock ;;",
        "hibernate": "gksu pm-hibernate && gnome-screensaver-command --lock ;;",
    }

    def run(self):
        out = super().run(items=self.actions.keys()).strip()
        logger.debug("selected: %s:%s", out, self.actions[out])
        self.qtile.cmd_spawn(out)


class BroTab(Dmenu):
    """
    Give vertical list of all open windows in dmenu. Switch to selected.
    """

    defaults = [
        ("item_format", "* {window}", "the format for the menu items"),
        (
            "all_groups",
            True,
            "If True, list windows from all groups; otherwise only from the current group",
        ),
        ("dmenu_lines", "80", "Give lines vertically. Set to None get inline"),
    ]
    _tabs = None

    def __init__(self, **config):
        Dmenu.__init__(self, **config)
        self.add_defaults(WindowList.defaults)

    def _configure(self, qtile):
        Dmenu._configure(self, qtile)
        self.dbname = "qtile_brotab"

    @property
    def tabs(self):
        if not self._tabs:
            logger.info("initiailizeing tab list")
            self._tabs = [x for x in brotab("list").split("\n") if x]
        return self._tabs

    def run(self):
        # logger.info(self.item_to_win)
        recent = RecentRunner(self.dbname)
        out = super().run(items=self.tabs)
        screen = self.qtile.current_screen

        try:
            sout = out.rstrip("\n")
            bid, title, url = sout.split("\t")
            prefix, windowid, tabid = bid.split(".")
        except AttributeError:
            # out is not a string (for example it's a Popen object returned
            # by super(WindowList, self).run() when there are no menu items to
            # list
            return

        recent.insert(sout)
        brotab(["activate", str(bid)])
        # self.qtile.group["browser"].toscreen()
        self.qtile.cmd_toggle_group("browser")


class DmenuRunRecent(DmenuRun):
    defaults = [
        ("dbname", "dbname", "the sqlite db to store history."),
        ("dmenu_command", "dmenu", "the dmenu command to be launched"),
    ]
    qtile = None
    dbname = "qtile_run"
    dmenu_command = "dmenu"

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(super().defaults)

    def _configure(self, qtile):
        self.qtile = qtile
        super()._configure(qtile)

    def run(self):
        logger.error("running %s" % self.__class__.__name__)
        recent = RecentRunner(self.dbname)
        selected = (
            super()
            .run(
                items=list(
                    recent.list(
                        list_executables(datetime.utcnow().strftime("%H:%M"))
                    )
                )
            )
            .strip()
        )
        logger.info("Selected: %s", selected)
        if not selected:
            return
        recent.insert(selected)
        return Popen(
            ["nohup", selected], stdout=None, stdin=None, preexec_fn=os.setpgrp
        )


class PassMenu(DmenuRun):
    defaults = [
        ("dbname", "dbname", "the sqlite db to store history."),
        ("dmenu_command", "dmenu", "the dmenu command to be launched"),
    ]
    dmenu_prompt = "pass"
    dbname = "pass_menu"
    dmenu_command = "dmenu"

    def run(self):
        logger.error("running")
        recent = RecentRunner("pass_menu")
        with local.cwd(expanduser("~/.password-store/")):
            passfiles = [
                splitext(join(base, f))[0][2:]
                for base, _, files in os.walk(".")
                for f in files
                if f.endswith(".gpg")
            ]
        selection = super().run(items=recent.list(passfiles)).strip()
        logger.info("Selected: %s", selection)
        if not selection:
            return
        recent.insert(selection)
        return Popen(
            [
                join(dirname(__file__), "..", "..", "bin", "passinsert"),
                selection,
                str(get_current_window(self.qtile).window.wid),
            ],
            stdout=None,
            stdin=None,
            preexec_fn=os.setpgrp,
        )


class Inboxes(DmenuRun):
    defaults = [
        ("dbname", "list_inboxes", "the sqlite db to store history."),
        ("dmenu_command", "dmenu", "the dmenu command to be launched"),
        ("group", "mail", "the group to use."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(Inboxes.defaults)
        self.launched = {}

    def run(self):
        recent = RecentRunner(self.dbname)
        inboxes = get_hostconfig("google_accounts", [])
        qtile = self.qtile
        group = self.group
        if get_current_group(qtile).name != group:
            logger.debug("cmd_toggle_group")
            get_current_screen(qtile).cmd_toggle_group(group)
        selected = super().run(items=recent.list(inboxes)).strip()
        logger.info("Selected: %s", selected)
        if not selected or selected not in inboxes:
            recent.remove(selected)
            return
        recent.insert(selected)
        mail_regex = inboxes[selected].get("mail_regex", ".*%s.*" % selected)
        # mail_regex = ".*%s.*" % selected
        window = window_exists(qtile, re.compile(mail_regex, re.I))
        logger.debug("mail window exists %s regex %s ", window, mail_regex)
        is_launched = retreive(mail_regex)
        if window:
            # window = get_windows_map(qtile).get(window.window.wid)
            logger.debug("Matched %s", str(window))
            window.cmd_togroup(group)
            logger.debug("layout.focus")
            get_current_group(qtile).focus(window)
        else:
            cmd = (
                # "google-chrome-stable",
                "/usr/sbin//systemd-run",
                "--user",
                "--slice=browser.slice",
                "surf",
                # "-u",
                # "Firefox/99.0",
                "https://mail.google.com/mail/u/%s/#inbox" % selected,
                # "--app=https://mail.google.com/mail/u/%s/#inbox" % selected,
                # "--profile-directory=%s" % inboxes[selected]["profile"],
            )

            logger.info(cmd)
            qtile.cmd_spawn(cmd)
            # rc.set(mail_regex, datetime.now().timestamp())
            # return Popen(cmd, stdout=None, stdin=None, preexec_fn=os.setpgrp)


def persist(key, value):
    try:
        rc = get_redis()
        return rc.set(key, value)
    except:
        logger.exception("redis boost failed")


def retreive(key):
    try:
        rc = get_redis()
        return rc.get(key)
    except:
        logger.exception("redis boost failed")


def delete(key):
    try:
        rc = get_redis()
        return rc.delete(key)
    except:
        logger.exception("redis boost failed")


# @hook.subscribe.client_name_updated
def on_inbox_open(client):
    inboxes = get_hostconfig("google_accounts", [])
    for inbox, config in inboxes.items():
        mail_regex = config.get("mail_regex", None)
        if mail_regex and re.match(mail_regex, client.name):
            persist(mail_regex, datetime.now())
            client.to_group("mail")


# @hook.subscribe.client_killed
def on_inbox_close(client):
    inboxes = get_hostconfig("google_accounts", [])
    for inbox, config in inboxes.items():
        mail_regex = config.get("mail_regex", None)
        logger.error("window close %s:%s.", client.name, mail_regex)
        if mail_regex and re.match(mail_regex, client.name):
            delete(mail_regex)
