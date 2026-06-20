from collections import defaultdict

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import ModalScreen, Screen
from textual.widgets import Header, Footer, Button, Label, ListView, ListItem, Static

from model_inference import InferenceEngine
from model_manager import (
    delete_model,
    download_model,
    get_model_size_mb,
    is_model_downloaded,
    return_model_path,
    return_model_tokenizer,
)
from models_data import AVAILABLE_MODELS, DATASET_CATEGORIES
from screens.loading_screen import ConfirmDeleteScreen, DownloadScreen, LoadingScreen, ConfirmDownloadScreen


class CategoryInfoModal(ModalScreen):
    """Modal screen to display the full category description."""

    CSS = """
    CategoryInfoModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.6);
    }
    #info-modal-dialog {
        width: 60;
        height: auto;
        padding: 2 4;
        background: $surface;
        border: thick $accent;
    }
    #info-modal-title {
        text-style: bold;
        margin-bottom: 1;
        color: $accent;
    }
    #info-modal-desc {
        margin-bottom: 2;
        color: $text;
    }
    #close-info-modal {
        width: 100%;
    }
    """

    def __init__(self, title: str, description: str):
        super().__init__()
        self.cat_title = title
        self.cat_desc = description

    def compose(self) -> ComposeResult:
        with Vertical(id="info-modal-dialog"):
            yield Label(f"ℹ  {self.cat_title}", id="info-modal-title")
            yield Static(self.cat_desc, id="info-modal-desc")
            yield Button("Close", variant="primary", id="close-info-modal")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-info-modal":
            self.app.pop_screen()


class ModelManagementScreen(Screen):
    """First Screen: Split layout handling model management, metadata visualization and downloading."""

    CSS = """
    ModelManagementScreen {
        background: $background;
    }

    /* ── Layout ─────────────────────────────────────────────── */
    #workspace {
        layout: horizontal;
        height: 100%;
        width: 100%;
    }

    #left-pane {
        width: 32%;
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

    /* Scrollable container that holds alternating headers + ListViews */
    #model-scroll {
        height: 1fr;
        overflow-y: auto;
    }

    /* ── Category section headers (plain widgets, NOT inside ListView) ── */
    .category-header-row {
        height: auto;
        background: $primary-darken-2;
        padding: 1 2 0 2;
    }

    .info-btn {
        width: 3;
        height: 1;
        min-width: 3;
        border: none;
        background: transparent;
        color: $accent;
    }

    .info-btn:hover {
        background: $primary;
        color: $text;
    }

    .info-btn:focus {
        background: $primary;
        color: $text;
    }

    .category-header-label {
        color: $accent;
        text-style: bold;
        padding: 0 0 0 1;
        height: 1;
    }

    .category-short-description {
        background: $primary-darken-2;
        padding: 0 2 1 2;
        color: $text-muted;
        text-style: italic;
    }

    .category-divider {
        background: $primary-darken-2;
        color: $accent;
        padding: 0 2;
        height: 1;
    }

    /* Each per-category ListView shrinks to its content */
    .category-list {
        height: auto;
        background: $surface-darken-1;
    }

    /* ── Model rows ─────────────────────────────────────────── */
    .model-item {
        padding: 0 1;
    }

    /* ── Right-pane ─────────────────────────────────────────── */
    #right-pane {
        width: 68%;
        height: 100%;
        padding: 2 4;
    }

    #details-card {
        height: 85%;
        overflow-y: auto;
    }

    #action-bar {
        height: 15%;
        align: right bottom;
    }

    .meta-label {
        margin-top: 1;
        color: $text-muted;
    }

    .meta-value {
        margin-bottom: 1;
        color: $text;
    }

    /* ── Buttons ─────────────────────────────────────────────── */
    #action-btn {
        width: 25;
        height: 3;
    }

    #delete-btn {
        width: 25;
        height: 3;
        margin-left: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.selected_model_id = None
        # Pre-group models by category, preserving insertion order
        self._grouped: dict[str, list[str]] = defaultdict(list)
        for model_id, info in AVAILABLE_MODELS.items():
            self._grouped[info.get("category", "__uncategorised__")].append(model_id)
        # Track which ListView each model lives in (model_id -> ListView id)
        self._model_list_id: dict[str, str] = {}

    # ── Composition ──────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="workspace"):
            with Vertical(id="left-pane"):
                yield Label(" Lexis Models", id="list-header")

                with ScrollableContainer(id="model-scroll"):
                    for category_key, model_ids in self._grouped.items():
                        cat = DATASET_CATEGORIES.get(category_key, {
                            "label": category_key.replace("_", " ").title(),
                            "short_description": "",
                            "description": "",
                        })
                        list_id = f"list_{category_key}"

                        # ── Category header: plain widgets, never inside a ListView ──
                        yield Horizontal(
                            Button("ℹ", id=f"info_{category_key}", classes="info-btn"),
                            Label(cat["label"], classes="category-header-label"),
                            classes="category-header-row",
                        )
                        yield Static(
                            cat.get("short_description", ""),
                            classes="category-short-description",
                        )
                        yield Static("─" * 28, classes="category-divider")

                        # ── One ListView per category, containing only real model rows ──
                        with ListView(id=list_id, classes="category-list"):
                            for model_id in model_ids:
                                self._model_list_id[model_id] = list_id
                                info = AVAILABLE_MODELS[model_id]
                                yield ListItem(
                                    Label(f"  • {info['title']}", classes="model-item"),
                                    id=model_id,
                                )

            with Vertical(id="right-pane"):
                with Vertical(id="details-card"):
                    yield Static("", id="model-title")
                    yield Static("", id="model-description")

                    yield Label("[bold]Parameters:[/bold]", classes="meta-label")
                    yield Static("", id="model-params", classes="meta-value")

                    yield Label("[bold]Architecture:[/bold]", classes="meta-label")
                    yield Static("", id="model-arch", classes="meta-value")

                    yield Label("[bold]Disk size required:[/bold]", classes="meta-label")
                    yield Static("", id="model-size", classes="meta-value")

                with Horizontal(id="action-bar"):
                    yield Button("Select a model", id="action-btn", variant="primary", disabled=True)
                    yield Button("Delete Model", id="delete-btn", variant="error", disabled=True)

        yield Footer()

    def on_mount(self) -> None:
        # Focus and highlight the first model in the first category list
        first_list = self.query(".category-list").first(ListView)
        if first_list:
            first_list.index = 0

    # ── Event handlers ────────────────────────────────────────────────────────

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Fires from any of the per-category ListViews."""
        item_id = event.item.id if event.item else None
        if not item_id or item_id not in AVAILABLE_MODELS:
            return
        self.selected_model_id = item_id
        self.update_model_details(item_id)

    # ── Detail panel ──────────────────────────────────────────────────────────

    def update_model_details(self, model_id: str) -> None:
        info = AVAILABLE_MODELS[model_id]
        size_mb = get_model_size_mb(model_id)

        self.query_one("#model-title", Static).update(
            f"[b][underline]{info['title']}[/underline][/b]\n"
        )
        self.query_one("#model-description", Static).update(
            f"[i]{info['description']}[/i]\n"
        )
        self.query_one("#model-params", Static).update(info["parameters"])
        self.query_one("#model-arch", Static).update(info["architecture"])
        self.query_one("#model-size", Static).update(f"{size_mb} MB")

        action_btn = self.query_one("#action-btn", Button)
        delete_btn = self.query_one("#delete-btn", Button)
        action_btn.disabled = False

        if is_model_downloaded(model_id):
            action_btn.label = "Load Model"
            action_btn.variant = "success"
            delete_btn.disabled = False
        else:
            action_btn.label = f"Download  ({size_mb} MB)"
            action_btn.variant = "primary"
            delete_btn.disabled = True

    # ── Button routing ────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id and btn_id.startswith("info_"):
            cat_key = btn_id[len("info_"):]
            cat_info = DATASET_CATEGORIES.get(cat_key)
            if cat_info:
                self.app.push_screen(
                    CategoryInfoModal(cat_info["label"], cat_info["description"])
                )

        elif btn_id == "action-btn" and self.selected_model_id:
            self.manage_model_workflow(self.selected_model_id)

        elif btn_id == "delete-btn" and self.selected_model_id:
            self.delete_model_workflow(self.selected_model_id)

    # ── Async workflows ───────────────────────────────────────────────────────

    @work(exclusive=True)
    async def delete_model_workflow(self, model_name: str) -> None:
        action_btn = self.query_one("#action-btn")
        delete_btn = self.query_one("#delete-btn")

        action_btn.disabled = True
        delete_btn.disabled = True
        for lv in self.query(".category-list"):
            lv.disabled = True

        try:
            confirmed = await self.app.push_screen_wait(ConfirmDeleteScreen(model_name))
            if not confirmed:
                return

            worker = self.run_delete(model_name)
            await worker.wait()

        except Exception as e:
            self.query_one("#model-title", Static).update(
                f"[red]Error deleting model: {str(e)}[/red]"
            )
        finally:
            action_btn.disabled = False
            for lv in self.query(".category-list"):
                lv.disabled = False
            if self.selected_model_id:
                self.update_model_details(self.selected_model_id)

    @work(thread=True)
    def run_delete(self, model_name: str) -> None:
        delete_model(model_name)

    @work(exclusive=True)
    async def manage_model_workflow(self, model_name: str) -> None:
        action_btn = self.query_one("#action-btn")
        delete_btn = self.query_one("#delete-btn")

        action_btn.disabled = True
        delete_btn.disabled = True
        for lv in self.query(".category-list"):
            lv.disabled = True

        try:
            if not is_model_downloaded(model_name):
                size_mb = get_model_size_mb(model_name)
                proceed = await self.app.push_screen_wait(ConfirmDownloadScreen(size_mb))
                if not proceed:
                    return

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
            for lv in self.query(".category-list"):
                lv.disabled = False
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
        tokenizer_name = return_model_tokenizer(model_name)
        return InferenceEngine(model_path, tokenizer_name)