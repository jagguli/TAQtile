import re
import struct
from collections import OrderedDict

from libqtile.config import Group, Match, Rule as QRule, ScratchPad, DropDown

from taqtile.log import logger
from taqtile.screens import SECONDARY_SCREEN, PRIMARY_SCREEN
from taqtile.system import get_hostconfig, get_group_affinity


class Rule(QRule):
    def __init__(
        self,
        match,
        front=False,
        fullscreen=False,
        static=False,
        opacity=None,
        center=False,
        current_screen=False,
        geometry=None,
        sticky=False,
        **kwargs
    ):
        super().__init__(match, **kwargs)
        self.front = front
        self.fullscreen = fullscreen
        self.static = static
        self.opacity = opacity
        self.center = center
        self.current_screen = current_screen
        self.geometry = geometry
        self.sticky = False


def is_mailbox(client):
    try:
        surf_uri = client.window.get_property("_SURF_URI", str)
    except struct.error:
        return False

    if surf_uri and surf_uri.startswith("https://mail.google.com"):
        return True
    return False


def get_dgroups():
    return [
        Rule(
            Match(title="^Android Emulator.*|^Emulator.*"),
            float=True,
            intrusive=True,
            group=get_group_affinity("emulator"),
        ),
        Rule(
            Match(func=is_mailbox),
            group="mail",
            break_on_match=True,
        ),
        Rule(
            Match(
                title="shrapnel",
            ),
            float=True,
            break_on_match=False,
        ),
        Rule(
            Match(
                wm_class="antimicrox",
            ),
            float=True,
            break_on_match=False,
        ),
        Rule(
            Match(
                wm_class=re.compile("^crx_.*"),
                wm_instance_class=re.compile("^crx_.*"),
            ),
            group=get_group_affinity("hangouts"),
            break_on_match=False,
        ),
        Rule(
            Match(
                title=re.compile(r"whatsapp.*", re.I),
                wm_class=re.compile(".*whatsapp.*", re.I),
            ),
            group=get_group_affinity("whatsapp"),
            break_on_match=True,
        ),
        Rule(
            Match(title=re.compile(r"klipper", re.I)),
            group="3",
            break_on_match=False,
        ),
        Rule(
            Match(title=re.compile(r".*discord.*", re.I)),
            group="webcon",
            break_on_match=False,
        ),
        Rule(
            Match(
                wm_class=re.compile("insync.*", re.I),
                wm_instance_class=re.compile("insync.*", re.I),
            ),
            # float=True,
            static=True,
            break_on_match=True,
        ),
        Rule(
            Match(
                wm_class="onboard",
            ),
            # float=True,
            static=True,
            break_on_match=True,
        ),
    ]


def generate_groups(num_groups, layouts):
    is_laptop = get_hostconfig("laptop")

    # dgroup rules that not belongs to any group

    def terminal_match(regex):
        return Match(
            title=re.compile(regex)
            # wm_class= "xterm-256color"
        )

    logger.debug("num_groups:%s", num_groups)
    groups = []
    # map og group and prefered screen
    group_args = OrderedDict(
        {
            "monitor": dict(
                screen_affinity=PRIMARY_SCREEN,
                matches=[
                    terminal_match(r"^monitor$"),
                    # Match(title=re.compile(r"System Monitor", re.I)),
                ],
            ),
            "mail": dict(
                screen_affinity=PRIMARY_SCREEN,
                exclusive=False,
                init=True,
                matches=[
                    Match(wm_instance_class=re.compile("mail.google.com.*")),
                ],
            ),
            "calendar": dict(
                screen_affinity=PRIMARY_SCREEN,
                exclusive=False,
                init=True,
                matches=[
                    Match(wm_instance_class=re.compile("calendar.google.com.*"))
                ],
            ),
            "work": dict(
                screen_affinity=SECONDARY_SCREEN,
                init=True,
                persist=True,
                matches=[
                    Match(
                        title=re.compile(r".*\[work\].*", re.I),
                        wm_instance_class=re.compile(
                            r"chromium \(~\/\.config\/chromium\.work\)|chromium \(\/home\/steven\/\.config\/chromium\.work\)",
                            re.I,
                        ),
                    ),
                ],
            ),
            "home": dict(
                screen_affinity=SECONDARY_SCREEN,
                init=True,
                persist=True,
                matches=[
                    Match(
                        wm_instance_class=re.compile(
                            r"chromium \(~\/\.config\/chromium\.home\)|chromium \(\/home\/steven\/\.config\/chromium\.home\)",
                            re.I,
                        )
                    ),
                ],
            ),
            "social": dict(
                screen_affinity=PRIMARY_SCREEN,
                init=True,
                persist=True,
                matches=[
                    Match(title=re.compile(r".*twitter\.com.*", re.I)),
                    Match(title=re.compile(r".*diamondapp\.com.*", re.I)),
                ],
            ),
            "slack": dict(
                screen_affinity=PRIMARY_SCREEN,
                init=True,
                persist=True,
                matches=[
                    Match(wm_class="zoom"),
                    Match(wm_class="slack"),
                ],
            ),
            "webcon": dict(
                screen_affinity=PRIMARY_SCREEN,
                init=True,
                persist=True,
                matches=[
                    Match(wm_class="discord"),
                    Match(title=re.compile(r".*discord.*", re.I)),
                    Match(title=re.compile(r".*whatsapp.*", re.I)),
                    Match(wm_class="telegram-desktop"),
                ],
            ),
            "krusader": dict(
                screen_affinity=PRIMARY_SCREEN,
                persist=False,
                matches=Match(
                    title=re.compile(r".*krusader.*"), wm_class="Krusader"
                ),
            ),
            # "emacs": dict(
            #    screen_affinity=PRIMARY_SCREEN,
            #    persist=True,
            #    matches=[
            #        Match(wm_class=["emacs"]),
            #        Match(wm_class=["jetbrains-studio"]),
            #    ],
            # ),
            "audio": dict(
                screen_affinity=PRIMARY_SCREEN,
                persist=True,
                matches=[
                    Match(wm_class="pavucontrol-qt"),
                    Match(wm_class="qpwgraph"),
                    Match(wm_class="spotify"),
                    Match(title=re.compile(r".*open\.spotify\.com.*", re.I)),
                ],
            ),
            "crypto": dict(
                screen_affinity=SECONDARY_SCREEN,
                persist=True,
                matches=[
                    Match(wm_class="electrum"),
                    Match(wm_class="monero-wallet-gui"),
                    Match(wm_class="bitcoin-qt"),
                ],
            ),
        }
    )
    if not is_laptop:
        group_args["htop"] = dict(
            screen_affinity=SECONDARY_SCREEN,
            persist=False,
            matches=terminal_match(r"^htop$"),
        )
        group_args["log"] = dict(
            screen_affinity=SECONDARY_SCREEN,
            persist=False,
            matches=terminal_match(r"^log$"),
        )
        group_args["ulog"] = dict(
            screen_affinity=SECONDARY_SCREEN,
            persist=False,
            matches=terminal_match(r"^ulog$"),
        )

    for i in range(1, num_groups + 1):
        groups.append(
            Group(
                str(i),
                label=str(i)[-1] if i > 9 else str(i),
                **group_args.get(str(i), {"layout": "max", "layouts": layouts})
            )
        )
    for i, groupargs in group_args.items():
        groups.append(Group(str(i), **groupargs))
    groups.append(
        ScratchPad(
            "scratch",
            dropdowns=[
                DropDown(
                    name="xterm",
                    cmd="xterm",
                ),
                DropDown(
                    name="htop",
                    cmd="st -t htop -e htop",
                ),
                DropDown(
                    name="ncpamixer",
                    cmd="st -t pamixer -e ncpamixer",
                    height=1,
                ),
            ],
        )
    )
    return groups
