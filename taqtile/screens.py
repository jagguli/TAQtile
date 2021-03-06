import logging
from subprocess import check_output

from libqtile.config import Screen
from libqtile.widget import (
    Sep,
    Pomodoro,
    CurrentLayout,
    Battery,
    NetGraph,
    MemoryGraph,
    CPUGraph,
    Systray,
    DF,
    CryptoTicker,
    Volume,
    WindowCount,
    CPU,
)

from taqtile import system
from taqtile.themes import current_theme, default_params
from taqtile.widgets import CalClock, Clock, TextBox
from taqtile.widgets.bar import Bar
from taqtile.widgets.windowname import WindowName
from taqtile.widgets.multiscreengroupbox import MultiScreenGroupBox


# from widgets.bankbalance import BankBalance
# from widgets.mail import NotmuchCount

# from taqtile.widgets.priority_notify import PriorityNotify


log = logging.getLogger("qtile")

PRIMARY_SCREEN = system.get_screen(0)
SECONDARY_SCREEN = system.get_screen(1)
TERTIARY_SCREEN = system.get_screen(2)
QUATERNARY_SCREEN = system.get_screen(3)

try:
    localtimezone = check_output(["tzupdate", "-p", "-s", "5"]).decode().strip()
except:
    log.exception("Failed to automatically set timezone")
    localtimezone = "Australia/Sydney"


def get_screens(num_monitors, groups):
    multi_monitor = num_monitors > 1

    tasklist_params = default_params(
        selected=("[", "]"),
        rounded=False,
        border=current_theme["border_focus"],
        icon_size=0,
        padding=0,
        padding_y=0,
        margin=0,
        foreground=current_theme["foreground"],
    )

    # prompt_params = default_params()
    current_layout_params = default_params(name="default")
    windowname_params = default_params()
    systray_params = default_params(icon_size=15)
    clock_params = default_params(
        padding=2, format="%Y-%m-%d %a %H:%M", fontsize=12
    )
    pacman_params = default_params()
    notify_params = default_params()
    bitcointicker_params = default_params()
    batteryicon_params = default_params(
        charge_char="^",
        discharge_char="v",
        battery_name=system.get_hostconfig("battery"),
        format="{char}{percent:1.0%}",
    )
    windowtabs_params = default_params(selected=("[", "]"), separator="|")

    graph_defaults = {
        k[0]: k[1]
        for k in [
            ("graph_color", "18BAEB.6", "Graph color"),
            ("fill_color", "1667EB.3", "Fill color for linefill graph"),
            ("border_color", "215578", "Widget border color"),
            ("border_width", 1, "Widget border width"),
            ("margin_x", 1, "Margin X"),
            ("margin_y", 1, "Margin Y"),
            ("samples", 100, "Count of graph samples."),
            ("frequency", 1, "Update frequency in seconds"),
            ("type", "linefill", "'box', 'line', 'linefill'"),
            ("line_width", 1, "Line width"),
            (
                "start_pos",
                "bottom",
                "Drawer starting position ('bottom'/'top')",
            ),
            ("width", 50, "Width"),
        ]
    }
    cpugraph_params = dict(graph_defaults)
    cpugraph_params["graph_color"] = "FF3333.6"
    cpugraph_params["fill_color"] = "FF3333.3"
    memgraph_params = dict(graph_defaults)
    memgraph_params["graph_color"] = "80FF00.6"
    memgraph_params["fill_color"] = "80FF00.3"
    memgraph_params["type"] = "linefill"
    netgraph_params = dict(graph_defaults)
    sep_params = default_params(
        size_percent=100, padding=0, fontsize=9, foreground="000000"
    )
    graph_label_defaults = dict(
        margin=0,
        padding_x=0,
        padding_y=2,
    )

    primary_bar = [
        TextBox("first"),
        Sep(**sep_params),
        MultiScreenGroupBox(screen=PRIMARY_SCREEN),
        # Sep(**sep_params),
        # Prompt(**prompt_params),
        Sep(**sep_params),
        # TaskList2(**tasklist_params),
        WindowName(**windowname_params),
        # widget.TextBox(**layout_textbox_params),
        Sep(**sep_params),
        CurrentLayout(**current_layout_params),
        Sep(**sep_params),
        TextBox("w", **default_params()),
        WindowCount(**default_params()),
        Sep(**sep_params),
        # ThreadedPacman(**pacman_params),
        # Sep(**sep_params),
        DF(visible_on_warn=False, **default_params()),
        # Sep(**sep_params),
        # BankBalance(account='credit', **default_params()),
        # Sep(**sep_params),
        # BankBalance(account='debit', **default_params()),
        # Sep(**sep_params),
        # PriorityNotify(**default_params()),
        # Image(filename="/usr/share/icons/oxygen/16x16/devices/cpu.png"),
        # Sep(**sep_params),
        # NotmuchCount(**default_params()),
        Sep(**sep_params),
        TextBox("v", **default_params()),
        Volume(update_interval=1, **default_params()),
        Sep(**sep_params),
        CPU(**default_params()),
        Sep(**sep_params),
        TextBox(
            "c",
            **default_params(
                foreground=cpugraph_params["graph_color"],
                **graph_label_defaults
            )
        ),
        CPUGraph(**cpugraph_params),
        # Image(filename="/usr/share/icons/oxygen/16x16/devices/media-flash-memory-stick.png"),
        TextBox(
            "m",
            **default_params(
                foreground=memgraph_params["graph_color"],
                **graph_label_defaults
            )
        ),
        MemoryGraph(**memgraph_params),
        # Image(filename="/usr/share/icons/oxygen/16x16/devices/network-wired.png"),
        TextBox(
            "n",
            **default_params(
                foreground=netgraph_params["graph_color"],
                **graph_label_defaults
            )
        ),
        NetGraph(**netgraph_params),
        Sep(**sep_params),
        # Notify(width=30, **notify_params),
        Sep(**sep_params),
    ]
    if system.get_hostconfig("battery"):
        primary_bar.append(Battery(**batteryicon_params))
        primary_bar.append(Sep(**sep_params))

    secondary_bar = [
        TextBox("second"),
        Sep(**sep_params),
        MultiScreenGroupBox(screen=SECONDARY_SCREEN),
        Sep(**sep_params),
        # TaskList2(**tasklist_params),
        WindowName(**windowname_params),
        Sep(**sep_params),
        TextBox("w", **default_params()),
        WindowCount(**default_params()),
        Sep(**sep_params),
        CryptoTicker(currency="AUD"),
        Sep(**sep_params),
        CurrentLayout(**current_layout_params),
        Sep(**sep_params),
        Systray(**systray_params),
        Sep(**sep_params),
        CalClock(timezone=localtimezone, **clock_params),
    ]
    tertiary_bar = [
        TextBox("third"),
        Sep(**sep_params),
        MultiScreenGroupBox(screen=TERTIARY_SCREEN),
        # Sep(**sep_params),
        ##TaskList2(**tasklist_params),
        WindowName(**windowname_params),
        Sep(**sep_params),
        TextBox("w", **default_params()),
        WindowCount(**default_params()),
        Sep(**sep_params),
        CurrentLayout(**current_layout_params),
        CalClock(timezone=localtimezone, **clock_params),
    ]
    quaternary_bar = [
        TextBox("fourth"),
        Sep(**sep_params),
        MultiScreenGroupBox(screen=TERTIARY_SCREEN),
        # Sep(**sep_params),
        ##TaskList2(**tasklist_params),
        WindowName(**windowname_params),
        Sep(**sep_params),
        TextBox("w", **default_params()),
        WindowCount(**default_params()),
        Sep(**sep_params),
        CurrentLayout(**current_layout_params),
        CalClock(timezone=localtimezone, **clock_params),
    ]

    clock_text = default_params(fontsize=12)
    wclock_params = default_params(padding=2, format="%a %H:%M", fontsize=12)

    def make_clock_bar():
        timezones = [
            "UTC",
            "US/Central",
            "US/Eastern",
            "Australia/Sydney",
            "Asia/Ho_Chi_Minh",
            "Asia/Kolkata",
            "Africa/Lagos",
            "Asia/Riyadh",
        ]
        widgets = []
        for timezone in timezones:
            if timezone == localtimezone:
                continue
            widgets.append(TextBox("%s:" % timezone, **clock_text))
            widgets.append(Clock(timezone=timezone, **wclock_params))
            widgets.append(
                Sep(**sep_params),
            )
        widgets.extend(
            [
                Sep(**sep_params),
                Pomodoro(**default_params()),
                Sep(**sep_params),
            ]
        )
        return Bar(widgets, **default_params())

    # clock_bar.size = 0
    screens = dict()
    if num_monitors == 1:
        primary_bar.append(CalClock(timezone=localtimezone, **clock_params))
        screens[PRIMARY_SCREEN] = Screen(
            Bar(primary_bar, **default_params()),
            bottom=make_clock_bar(),
        )
    else:
        screens[PRIMARY_SCREEN] = Screen(
            Bar(primary_bar, **default_params()),
            bottom=make_clock_bar(),
        )
        screens[SECONDARY_SCREEN] = Screen(
            Bar(secondary_bar, **default_params()),
            bottom=make_clock_bar(),
        )
        screens[TERTIARY_SCREEN] = Screen(
            Bar(tertiary_bar, **default_params()),
            bottom=make_clock_bar(),
        )
        screens[QUATERNARY_SCREEN] = Screen(
            Bar(quaternary_bar, **default_params()),
            bottom=make_clock_bar(),
        )
    screens = [screens[y] for y in sorted(screens.keys())]
    log.error("Screens: %s ", screens)
    return screens
