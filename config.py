# TODO handle MultiScreenGroupBox clicks and events
import logging
import os
from os.path import expanduser
from log import init_log

logger = init_log(
    log_level=logging.DEBUG,
)

from libqtile import layout
from libqtile.command import lazy
from libqtile.config import Click, Drag

from groups import generate_groups, get_dgroups
from keys import get_keys
from screens import (
    get_screens,
    PRIMARY_SCREEN,
    SECONDARY_SCREEN,
    TERTIARY_SCREEN,
)
from system import get_num_monitors
from themes import current_theme
from extra import Terminal
import hooks  # pylint: disable=unused-import

mod = "mod4"
num_monitors = get_num_monitors()

layouts = [
    layout.Max(**current_theme),
    layout.Stack(**current_theme),
    layout.xmonad.MonadTall(ratio=0.50, **current_theme),
    layout.Tile(**current_theme),
    layout.Zoomy(**current_theme),
    # layout.TreeTab(),
    # a layout just for gimp
    # layout.Slice('term1', 192, name='gimp', role='gimp-toolbox',
    #             fallback=layout.Slice('right', 256, role='gimp-dock',
    #                                   fallback=layout.Stack(
    #                                       num_stacks=1, **border_args))),
]


# This allows you to drag windows around with the mouse if you want.
mouse = [
    Drag(
        [mod],
        "Button1",
        lazy.window.set_position_floating(),
        start=lazy.window.get_position(),
    ),
    Drag(
        [mod],
        "Button3",
        lazy.window.set_size_floating(),
        start=lazy.window.get_size(),
    ),
    # Click([mod], "Button2", lazy.window.bring_to_front())
]

float_windows = [
    "buddy_list",
]
follow_mouse_focus = True
bring_front_click = True
cursor_warp = False
auto_fullscreen = True
widget_defaults = current_theme
dgroups_app_rules = get_dgroups()
num_groups = (num_monitors - 1) * 10

groups = generate_groups(num_groups, layouts)
keys = get_keys(mod, num_groups, num_monitors)


Terminal(
    "term0",
    "F11",
    groups=groups,
    keys=keys,
    dgroups=dgroups_app_rules,
    screen=PRIMARY_SCREEN,
)

Terminal(
    "term1",
    "F12",
    groups=groups,
    keys=keys,
    dgroups=dgroups_app_rules,
    screen=SECONDARY_SCREEN,
)

Terminal(
    "term2",
    "XF86Launch5",
    groups=groups,
    keys=keys,
    dgroups=dgroups_app_rules,
    screen=TERTIARY_SCREEN,
)

Terminal(
    "salt-bison",
    [[mod], "F12"],
    groups=groups,
    keys=keys,
    dgroups=dgroups_app_rules,
    spawn="salt-bison",
    screen=SECONDARY_SCREEN,
)

Terminal(
    "comm",
    "F9",
    groups=groups,
    keys=keys,
    dgroups=dgroups_app_rules,
    screen=PRIMARY_SCREEN,
)

Terminal(
    "jupyter-bison",
    [[mod], "XF86Launch5"],
    groups=groups,
    keys=keys,
    dgroups=dgroups_app_rules,
    screen=SECONDARY_SCREEN,
    spawn="~/streethawk/infrastructure/srv/k8s/bin/jupyter-shell.sh",
)

Terminal(
    "jupyter-zebra",
    [[mod], "F11"],
    groups=groups,
    keys=keys,
    dgroups=dgroups_app_rules,
    screen=TERTIARY_SCREEN,
    spawn="jupyter-zebra",
)

screens = get_screens(num_monitors, groups)


class NoTimerFilter(logging.Filter):
    def filter(self, record):
        return "timer" not in record.getMessage()
