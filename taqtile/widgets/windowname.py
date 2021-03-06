from libqtile.widget import WindowName as QWindowName
from taqtile.themes import current_theme, default_params

from taqtile.log import logger
from libqtile import bar, hook, pangocffi


class WindowName(QWindowName):
    default_background = None
    defaults = [
        ("focused_background", "#FF0000", "Focused background colour."),
        ("focused_foreground", "#000000", "Focused foreground colour."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(WindowName.defaults)
        self.default_background = self.background
        self.default_foreground = self.foreground

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        hook.subscribe.current_screen_change(self.hook_response)

    def draw(self):
        if self.bar.screen == self.qtile.current_screen:
            self.background = self.focused_background
            self.foreground = self.focused_foreground
        else:
            self.background = self.default_background
            self.foreground = self.default_foreground
        return super().draw()
