"""
screens/model_management_screen.py
───────────────────────────────────
Main model-management screen.

Layout: Header | [ModelListPane | ModelDetailPane] | Footer

This module is intentionally thin — all visual logic lives in the pane
widgets, and data/arch definitions live in models_data.py.
"""

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, ListView, Button

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
from screens.modals import CategoryInfoModal
from screens.left_pane import ModelListPane
from screens.right_pane import ModelDetailPane


class ModelManagementScreen(Screen):
    """Split layout: left = model list, right = rich model details."""

    CSS = """
    ModelManagementScreen {
        background: $background;
    }

    #workspace {
        layout: horizontal;
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.selected_model_id: str | None = None

    # ── Composition ──────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="workspace"):
            yield ModelListPane()
            yield ModelDetailPane()
        yield Footer()

    # ── Event handlers ────────────────────────────────────────────────────────

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id if event.item else None
        if not item_id or item_id not in AVAILABLE_MODELS:
            return
        self.selected_model_id = item_id
        self.query_one(ModelDetailPane).show_model(item_id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        # Category info modal (ℹ buttons in the left pane)
        if btn_id and btn_id.startswith("info_"):
            cat_key = btn_id[len("info_"):]
            cat_info = DATASET_CATEGORIES.get(cat_key)
            if cat_info:
                self.app.push_screen(
                    CategoryInfoModal(cat_info["label"], cat_info["description"])
                )

        # Download / Load button
        elif btn_id == "action-btn" and self.selected_model_id:
            self.manage_model_workflow(self.selected_model_id)

        # Delete button
        elif btn_id == "delete-btn" and self.selected_model_id:
            self.delete_model_workflow(self.selected_model_id)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_ui_locked(self, locked: bool) -> None:
        """Disable/enable interactive controls during async workflows."""
        detail = self.query_one(ModelDetailPane)
        detail.query_one("#action-btn", Button).disabled = locked
        detail.query_one("#delete-btn", Button).disabled = locked
        for lv in self.query(".category-list"):
            lv.disabled = locked

    def _refresh_detail(self) -> None:
        if self.selected_model_id:
            self.query_one(ModelDetailPane).show_model(self.selected_model_id)

    # ── Async workflows ───────────────────────────────────────────────────────

    @work(exclusive=True)
    async def delete_model_workflow(self, model_name: str) -> None:
        self._set_ui_locked(True)
        try:
            confirmed = await self.app.push_screen_wait(ConfirmDeleteScreen(model_name))
            if not confirmed:
                return
            await self.run_delete(model_name).wait()
        except Exception as e:
            self.query_one(ModelDetailPane).query_one("#model-title-label").update(
                f"[red]Error deleting model: {e}[/red]"
            )
        finally:
            self._set_ui_locked(False)
            self._refresh_detail()

    @work(thread=True)
    def run_delete(self, model_name: str) -> None:
        delete_model(model_name)

    @work(exclusive=True)
    async def manage_model_workflow(self, model_name: str) -> None:
        self._set_ui_locked(True)
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
            self.query_one(ModelDetailPane).query_one("#model-title-label").update(
                f"[red]Error: {e}[/red]"
            )
            if isinstance(self.app.screen, (DownloadScreen, LoadingScreen)):
                self.app.pop_screen()

        finally:
            self._set_ui_locked(False)
            self._refresh_detail()

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