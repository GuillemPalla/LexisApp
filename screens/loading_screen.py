from textual.app import ComposeResult
from textual.containers import Center, Vertical, Horizontal
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Label, LoadingIndicator, ProgressBar, Static

class LoadingScreen(Screen):
    """Reusable transparent modal displaying a loading animation overlay."""

    DEFAULT_CSS = """
    LoadingScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.5);
    }
    """

    def compose(self) -> ComposeResult:
        with Center():
            yield LoadingIndicator()


class ConfirmDownloadScreen(ModalScreen[bool]):
    """Warning modal shown before an un-cancellable download begins."""

    DEFAULT_CSS = """
    ConfirmDownloadScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.6);
    }

    #warning-card {
        width: 70;
        height: 15;
        padding: 2 3;
        background: $surface;
        border: round $accent;
    }

    .warning-text {
        text-align: center;
        margin-bottom: 1;
    }

    #button-layout {
        layout: horizontal;
        align: center middle;
        margin-top: 1;
    }
    
    Button {
        margin: 0 1;
    }
    """

    def __init__(self, size_mb: float) -> None:
        super().__init__()
        self.size_mb = size_mb

    def compose(self) -> ComposeResult:
        with Vertical(id="warning-card"):
            yield Label(f"[bold]Warning:[/bold] You are about to download [bold]{self.size_mb} MB[/bold].", classes="warning-text")
            yield Label("This download [red]cannot be cancelled[/red] once started.", classes="warning-text")
            yield Label("Do you want to proceed?", classes="warning-text")
            
            with Horizontal(id="button-layout"):
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

    DEFAULT_CSS = """
    DownloadScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.6);
    }

    #download-card {
        width: 60;
        height: auto;
        padding: 2 3;
        background: $surface;
        border: round $accent;
    }

    #dl-title {
        text-style: bold;
        margin-bottom: 1;
        color: $text;
    }

    #dl-filename {
        color: $text-muted;
        margin-bottom: 1;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    #dl-progress {
        width: 100%;
        margin-bottom: 1;
    }

    #dl-stats {
        color: $text-muted;
    }
    """

    def __init__(self, total_bytes: int = 0) -> None:
        super().__init__()
        self._total_bytes = total_bytes  # 0 = unknown up front

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="download-card"):
                yield Static("Downloading model…", id="dl-title")
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