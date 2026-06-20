"""
screens/modals.py
─────────────────
Reusable modal dialogs for the model-management screen.
"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


# ── Shared modal CSS ──────────────────────────────────────────────────────────

MODAL_CSS = """
.modal-overlay {
    align: center middle;
    background: rgba(0, 0, 0, 0.65);
}

.modal-dialog {
    width: 64;
    height: auto;
    padding: 3 4;
    background: $background;
    border: tall $primary 30%;
    hatch: right $primary 12%;
}

.modal-title {
    text-style: bold underline;
    margin-bottom: 2;
    padding: 0 1;
    color: $text-warning;
}

.modal-body {
    margin-bottom: 3;
    padding: 0 2;
    color: $text-secondary;
    text-style: dim;
    height: auto;
}

.modal-close {
    width: 100%;
    margin-top: 1;
}
"""


# ─────────────────────────────────────────────────────────────────────────────
#  Category info modal
# ─────────────────────────────────────────────────────────────────────────────

class CategoryInfoModal(ModalScreen):
    """Modal: full category description."""

    CSS = MODAL_CSS + """
    CategoryInfoModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.65);
    }
    """

    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        self.cat_title = title
        self.cat_desc = description

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label(f"ℹ  {self.cat_title}", classes="modal-title")
            yield Static(self.cat_desc, classes="modal-body")
            yield Button("Close", variant="primary", id="close-modal", classes="modal-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-modal":
            self.app.pop_screen()


# ─────────────────────────────────────────────────────────────────────────────
#  Architecture feature detail modal
# ─────────────────────────────────────────────────────────────────────────────

class ArchFeatureModal(ModalScreen):
    """Modal: explanation of one architecture feature."""

    CSS = MODAL_CSS + """
    ArchFeatureModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.65);
    }
    """

    def __init__(self, feature: str, explanation: str) -> None:
        super().__init__()
        self.feature = feature
        self.explanation = explanation

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label(f"⚙  {self.feature}", classes="modal-title")
            yield Static(self.explanation, classes="modal-body")
            yield Button("Close", variant="primary", id="close-arch-modal", classes="modal-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-arch-modal":
            self.app.pop_screen()
