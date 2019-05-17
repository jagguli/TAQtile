import os
import re
import shlex
from os.path import isdir, join, pathsep, dirname

from plumbum.cmd import dmenu, bluetoothctl, clipmenu, xdotool

from log import logger
from recent_runner import RecentRunner
from screens import PRIMARY_SCREEN, SECONDARY_SCREEN
from dbus_bluetooth import get_devices
from themes import dmenu_defaults
from system import get_hostconfig, window_exists


def dmenu_show(title, items):
    dmenu_args = shlex.split(dmenu_defaults())
    logger.info("DMENU: %s", dmenu_args)
    try:
        return (dmenu[
            "-i", "-p", "%s " % title
            ] << "\n".join(items))(*dmenu_args).strip()
    except Exception as e:
        logger.exception("error running dmenu")


def list_windows(qtile, current_group=False):

    def title_format(x):
        return "%s" % (
            #x.group.name if x.group else '',
            x.name)

    if current_group:
        window_titles = [
            w.name for w in qtile.groupMap[qtile.current_group.name].windows
            if w.name != "<no name>"
        ]
    else:
        window_titles = [
            title_format(w) for w in qtile.windows_map.values() if w.name != "<no name>"
        ]
    logger.info(window_titles)

    def process_selected(selected):
        if not current_group:
            group, selected = selected.split(']', 1)
        selected = selected.strip()
        logger.info("Switch to: %s", selected)
        for window in qtile.windows_map.values():
            try:
                if window.group and str(window.name.decode('utf8')) == str(selected):
                    logger.debug("raise %s:", window)
                    if window.group.screen:
                        qtile.cmd_to_screen(window.group.screen.index)
                    else:
                        window.group.cmd_toscreen()
                    qtile.current_group.focus(window, False)
                    return True
            except Exception as e:
                logger.exception("error in group")
        return True

    process_selected(dmenu_show(
        qtile.current_group.name if current_group else "*",
        window_titles,
    ))


def list_windows_group(qtile):
    return list_windows(qtile, current_group=True)


def list_executables():
    paths = os.environ["PATH"].split(pathsep)
    executables = []
    for path in filter(isdir, paths):
        for file_ in os.listdir(path):
            if os.access(join(path, file_), os.X_OK):
                executables.append(file_)
    return set(executables)


def dmenu_run(qtile):
    recent = RecentRunner('qtile_run')
    selected = dmenu_show("Run", recent.list(list_executables()))
    print(selected)
    if not selected:
        return
    logger.debug((dir(qtile)))
    qtile.cmd_spawn(selected)
    recent.insert(selected)


def dmenu_org(qtile):
    org_categories = [
        "todo",
        "event",
        "note",
    ]
    title = dmenu_show("Run", org_categories)
    cmd_str = (
        "emacsclient -f xdev -c org-protocol://capture://"
        "url/%s/etext" % (
            title,
        )
    )
    qtile.cmd_spawn(cmd_str)


def list_bluetooth(qtile):
    recent = RecentRunner('qtile_bluetooth')
    devices = get_devices()['/org/bluez/hci0']['devices']
    all_devices = dict([
        (device['Alias'], device['Address'])
        for device in devices.values()
    ])
    selected = dmenu_show("Bluetooth:", recent.list(all_devices.keys()))
    if not selected:
        return
    action = dmenu_show("Action", ["connect", "disconnect"])
    (bluetoothctl << "%s %s\nexit\n" % (action, all_devices[selected]))()
    recent.insert(selected)


def get_window_titles(qtile):
    return [
        w['name'] for w in qtile.cmd_windows()
        if w['name'] != "<no name>"
    ]

def list_calendars(qtile):
    group = 'cal'
    try:
        recent = RecentRunner('qtile_calendar')
        inboxes = {
            'melit.stevenjoseph@gmail.com': "^Google Calendar.*$",
            'steven@stevenjoseph.in': "^stevenjoseph - Calendar.*$",
            'steven@streethawk.co': "Streethawk - Calendar.*$",
        }
        selected = dmenu_show("Calendars:", recent.list(inboxes.keys()))
        if not selected:
            return
        recent.insert(selected)
        match = re.compile(inboxes[selected], re.I)
        if qtile.current_screen.index != SECONDARY_SCREEN:
            logger.debug("cmd_to_screen")
            qtile.cmd_to_screen(SECONDARY_SCREEN)
        if qtile.current_group.name != group:
            logger.debug("cmd_toggle_group")
            qtile.current_screen.cmd_toggle_group(group)
        for window in qtile.cmd_windows():
            if match.match(window['name']):
                logger.debug("Matched" + str(window))
                window = qtile.windows_map.get(window['id'])
                qtile.current_group.layout.current = window
                logger.debug("layout.focus")
                qtile.current_group.layout.focus(window)
                break
        else:
            cmd = (
                'chromium --app="https://calendar.google.com/calendar/b/%s/"' %
                selected
            )

            logger.debug(cmd)
            qtile.cmd_spawn(cmd)

    except:
        logger.exception("error list_calendars")

def list_inboxes(qtile):
    group = 'mail'
    try:
        recent = RecentRunner('qtile_inbox')
        inboxes = get_hostconfig('google_accounts', [])
        selected = dmenu_show("Inboxes:", recent.list(inboxes))
        if not selected:
            return
        recent.insert(selected)
        if qtile.current_screen.index != SECONDARY_SCREEN:
            logger.debug("cmd_to_screen")
            qtile.cmd_to_screen(SECONDARY_SCREEN)
        if qtile.current_group.name != group:
            logger.debug("cmd_toggle_group")
            qtile.current_screen.cmd_toggle_group(group)
        if window_exists(qtile, re.compile(r"mail.google.com__mail_u_%s" % selected, re.I)):
            logger.debug("Matched" + str(window))
            window = qtile.windows_map.get(window['id'])
            qtile.current_group.layout.current = window
            logger.debug("layout.focus")
            qtile.current_group.layout.focus(window)
        else:
            cmd = (
                'chromium --app="https://mail.google.com/mail/u/%s/#inbox"' %
                selected
            )

            logger.debug(cmd)
            qtile.cmd_spawn(cmd)

    except:
        logger.exception("error list_inboxes")


def dmenu_clip(qtile):
    title = "Clipboard: "
    dmenu_args = shlex.split(dmenu_defaults())
    logger.info("DMENU: %s", dmenu_args)
    try:
        xdotool(
            "type",
            "--clearmodifiers",
            "--",
            clipmenu[
                "-i", "-p", "%s" % title
            ](*dmenu_args).strip()
        )
    except Exception as e:
        logger.exception("error in clip access")
