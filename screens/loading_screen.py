from textual.app import ComposeResult
from textual.containers import Center, VerticalGroup, HorizontalGroup
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Label, ProgressBar, Static


# ── Shared overlay / card CSS ─────────────────────────────────────────────────

OVERLAY_CSS = """
.overlay-screen {
    align: center middle;
    background: rgba(0, 0, 0, 0.65);
}

.overlay-card {
    width: 70;
    height: auto;
    padding: 3 4;
    background: $background;
    border: tall $primary 30%;
    hatch: right $primary 12%;
}

.overlay-title {
    text-style: bold underline;
    color: $text-warning;
    text-align: center;
    margin-bottom: 2;
    padding: 0 1;
}

.overlay-text {
    text-align: center;
    margin-bottom: 2;
    padding: 0 2;
    color: $text-secondary;
    height: auto;
}

.overlay-prompt {
    margin-bottom: 1;
}

.overlay-text-strong {
    color: $text;
    text-style: bold;
}

#button-layout {
    width: 100%;
    height: auto;
    align-horizontal: center;
    margin-top: 1;
    padding: 1 0 2 0;
    border-top: hkey $primary;
}

#button-layout Button {
    margin: 0 2;
    min-width: 16;
}
"""


class Spinner(Static):
    """Single-line animated spinner (LoadingIndicator collapses to height 0 in card layouts)."""

    FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

    DEFAULT_CSS = """
    Spinner {
        width: 100%;
        height: 1;
        text-align: center;
        color: $warning;
        text-style: bold;
    }
    """

    def on_mount(self) -> None:
        self._frame = 0
        self.update(self.FRAMES[0])
        self.set_interval(0.08, self._advance)

    def _advance(self) -> None:
        self._frame = (self._frame + 1) % len(self.FRAMES)
        self.update(self.FRAMES[self._frame])


class LoadingScreen(Screen):
    """Reusable transparent modal displaying a loading animation overlay."""

    DEFAULT_CSS = OVERLAY_CSS + """
    LoadingScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.65);
    }

    #loading-card {
        width: 50;
    }

    #loading-spinner {
        margin-bottom: 1;
    }

    #loading-progress {
        width: 100%;
        padding: 0 2;
    }

    #loading-progress Bar {
        width: 100%;
    }
    """

    def __init__(self, title: str = "Initializing model…") -> None:
        super().__init__()
        self.title = title

    def compose(self) -> ComposeResult:
        with Center():
            with VerticalGroup(id="loading-card", classes="overlay-card"):
                yield Static(self.title, id="loading-title", classes="overlay-title")
                yield Spinner(id="loading-spinner")
                yield ProgressBar(
                    total=None,
                    show_eta=False,
                    show_percentage=False,
                    id="loading-progress",
                )


class ConfirmDownloadScreen(ModalScreen[bool]):
    """Warning modal shown before an un-cancellable download begins."""

    DEFAULT_CSS = OVERLAY_CSS + """
    ConfirmDownloadScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.65);
    }
    """

    def __init__(self, size_mb: float) -> None:
        super().__init__()
        self.size_mb = size_mb

    def compose(self) -> ComposeResult:
        with Center():
            with VerticalGroup(id="warning-card", classes="overlay-card"):
                yield Label("Download confirmation", classes="overlay-title")
                yield Label(
                    f"You are about to download [bold]{self.size_mb} MB[/bold].",
                    classes="overlay-text",
                )
                yield Label(
                    "This download [red]cannot be cancelled[/red] once started.",
                    classes="overlay-text",
                )
                yield Label("Do you want to proceed?", classes="overlay-text overlay-prompt")

                with HorizontalGroup(id="button-layout"):
                    yield Button("Proceed", id="proceed-btn", variant="error")
                    yield Button("Cancel", id="cancel-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "proceed-btn":
            self.dismiss(True)
        else:
            self.dismiss(False)


class ConfirmDeleteScreen(ModalScreen[bool]):
    DEFAULT_CSS = OVERLAY_CSS + """
    ConfirmDeleteScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.65);
    }
    """

    def __init__(self, size_mb: float) -> None:
        super().__init__()
        self.size_mb = size_mb

    def compose(self) -> ComposeResult:
        with Center():
            with VerticalGroup(id="warning-card", classes="overlay-card"):
                yield Label("Delete confirmation", classes="overlay-title")
                yield Label(
                    f"You are about to delete [bold]{self.size_mb}[/bold].",
                    classes="overlay-text",
                )
                yield Label(
                    "This action [red]cannot be undone[/red].",
                    classes="overlay-text",
                )
                yield Label("Do you want to proceed?", classes="overlay-text overlay-prompt")

                with HorizontalGroup(id="button-layout"):
                    yield Button("Proceed", id="proceed-btn", variant="error")
                    yield Button("Cancel", id="cancel-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "proceed-btn":
            self.dismiss(True)
        else:
            self.dismiss(False)


class DownloadScreen(Screen):
    """
    Modal overlay shown while a model is being downloaded.
    Exposes update_progress(downloaded, total, filename).
    """

    DEFAULT_CSS = OVERLAY_CSS + """
    DownloadScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.65);
    }

    #download-card {
        width: 60;
    }

    #dl-filename {
        color: $text-muted;
        text-style: dim italic;
        margin-bottom: 2;
        padding: 0 2;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    #dl-progress {
        width: 100%;
        margin-bottom: 2;
        padding: 0 2;
    }

    #dl-stats {
        color: $text-success;
        text-style: bold;
        text-align: center;
        padding: 0 2;
    }
    """

    def __init__(self, total_bytes: int = 0) -> None:
        super().__init__()
        self._total_bytes = total_bytes  # 0 = unknown up front

    def compose(self) -> ComposeResult:
        with Center():
            with VerticalGroup(id="download-card", classes="overlay-card"):
                yield Static("Downloading model…", id="dl-title", classes="overlay-title")
                yield Static("", id="dl-filename")
                yield ProgressBar(total=100, show_eta=False, id="dl-progress")
                yield Static("", id="dl-stats")

    def update_progress(self, downloaded: int, total: int, filename: str) -> None:
        """Safe to call from any thread."""
        self.app.call_from_thread(self._apply_progress, downloaded, total, filename)

    def _apply_progress(self, downloaded: int, total: int, filename: str) -> None:
        """Runs on the Textual event loop thread."""
        short_name = filename.split("/")[-1]
        self.query_one("#dl-filename", Static).update(short_name)

        if total > 0:
            pct = int(downloaded / total * 100)
            self.query_one("#dl-progress", ProgressBar).update(progress=pct)
            dl_mb = downloaded / 1_048_576
            tot_mb = total / 1_048_576
            self.query_one("#dl-stats", Static).update(
                f"{dl_mb:.1f} MB / {tot_mb:.1f} MB"
            )
        else:
            dl_mb = downloaded / 1_048_576
            self.query_one("#dl-stats", Static).update(f"{dl_mb:.1f} MB")
