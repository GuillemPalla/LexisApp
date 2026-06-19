import time
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Label, ListView, ListItem, Static

from model_manager import (
    download_model,
    is_model_downloaded,
    return_model_path,
)
from models_data import AVAILABLE_MODELS_INFO
from screens.loading_screen import DownloadScreen, LoadingScreen, ConfirmDownloadScreen


class InferenceEngine:
    def __init__(self, model_path):
        time.sleep(1)

    def generate_stream(self, prompt: str):
        yield f"Echo response to: {prompt}"


class ModelManagementScreen(Screen):
    """First Screen: Split layout handling model management, metadata visualization and downloading."""

    CSS = """
    ModelManagementScreen {
        background: $background;
    }

    #workspace {
        layout: horizontal;
        height: 100%;
        width: 100%;
    }

    #left-pane {
        width: 30%;
        height: 100%;
        border-right: vkey $accent;
        background: $surface-darken-1;
    }

    #list-header {
        padding: 1 2;
        background: $primary-darken-1;
        color: $text;
        text-style: bold;
    }

    #right-pane {
        width: 70%;
        height: 100%;
        padding: 2 4;
    }

    #details-card {
        height: 85%;
        overflow-y: auto;
    }

    .meta-label {
        margin-top: 1;
        color: $text-muted;
    }

    .meta-value {
        margin-bottom: 1;
        color: $text;
    }

    #action-bar {
        height: 15%;
        align: right bottom;
    }

    #action-btn {
        width: 25;
        height: 3;
    }
    """

    def __init__(self):
        super().__init__()
        self.selected_model_id = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="workspace"):
            with Vertical(id="left-pane"):
                yield Label(" Available Models", id="list-header")
                with ListView(id="model-list"):
                    for model_id in AVAILABLE_MODELS_INFO.keys():
                        yield ListItem(Label(f"• {model_id}"), id=model_id)

            with Vertical(id="right-pane"):
                with Vertical(id="details-card"):
                    yield Static("", id="model-title")
                    yield Static("", id="model-description")

                    yield Label("[bold]Parameters:[/bold]", classes="meta-label")
                    yield Static("", id="model-params", classes="meta-value")

                    yield Label("[bold]Architecture Substructure:[/bold]", classes="meta-label")
                    yield Static("", id="model-arch", classes="meta-value")

                    yield Label("[bold]Disk Size requirement:[/bold]", classes="meta-label")
                    yield Static("", id="model-size", classes="meta-value")

                with Horizontal(id="action-bar"):
                    yield Button("Select a model", id="action-btn", variant="primary", disabled=True)

        yield Footer()

    def on_mount(self) -> None:
        model_list = self.query_one("#model-list", ListView)
        if model_list.children:
            model_list.index = 0

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item and event.item.id:
            self.selected_model_id = event.item.id
            self.update_model_details(self.selected_model_id)

    def update_model_details(self, model_id: str) -> None:
        info = AVAILABLE_MODELS_INFO[model_id]

        self.query_one("#model-title", Static).update(f"[b][underline]{info['title']}[/underline][/b]\n")
        self.query_one("#model-description", Static).update(f"[i]{info['description']}[/i]\n")
        self.query_one("#model-params", Static).update(info['parameters'])
        self.query_one("#model-arch", Static).update(info['architecture'])
        self.query_one("#model-size", Static).update(f"{info['size_mb']} MB")

        action_btn = self.query_one("#action-btn", Button)
        action_btn.disabled = False

        if is_model_downloaded(model_id):
            action_btn.label = "Load Model"
            action_btn.variant = "success"
        else:
            action_btn.label = f"Download ({info['size_mb']} MB)"
            action_btn.variant = "primary"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "action-btn" and self.selected_model_id:
            self.manage_model_workflow(self.selected_model_id)

    @work(exclusive=True)
    async def manage_model_workflow(self, model_name: str) -> None:
        action_btn = self.query_one("#action-btn")
        model_list = self.query_one("#model-list")

        action_btn.disabled = True
        model_list.disabled = True

        try:
            if not is_model_downloaded(model_name):
                info = AVAILABLE_MODELS_INFO[model_name]
                
                # Push the warning modal and wait for the user's choice
                proceed = await self.app.push_screen_wait(ConfirmDownloadScreen(info['size_mb']))
                if not proceed:
                    return # Exit early, the finally block will re-enable UI

                download_screen = DownloadScreen()
                self.app.push_screen(download_screen)

                worker = self.run_download(model_name, download_screen)
                await worker.wait()

                self.app.pop_screen()
                _ = worker.result

            self.app.push_screen(LoadingScreen())
            worker = self.run_model_initialization(model_name)
            await worker.wait()
            engine = worker.result

            self.app.engine = engine
            self.app.pop_screen()
            self.app.switch_screen("chat")

        except Exception as e:
            self.query_one("#model-title", Static).update(f"[red]Error: {str(e)}[/red]")
            if isinstance(self.app.screen, (DownloadScreen, LoadingScreen)):
                self.app.pop_screen()

        finally:
            action_btn.disabled = False
            model_list.disabled = False
            if self.selected_model_id:
                self.update_model_details(self.selected_model_id)

    @work(thread=True)
    def run_download(self, model_name: str, download_screen: DownloadScreen) -> None:
        download_model(
            model_name,
            progress_callback=download_screen.update_progress,
        )

    @work(thread=True)
    def run_model_initialization(self, model_name: str) -> InferenceEngine:
        model_path = return_model_path(model_name)
        return InferenceEngine(model_path)