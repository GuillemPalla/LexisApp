# THIS FILE HAS BEEN AI GENERATED

from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView, Static

from model_inference import PRESET_ORDER, SAMPLING_PRESETS


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


# ─────────────────────────────────────────────────────────────────────────────
#  Chat screen — important information
# ─────────────────────────────────────────────────────────────────────────────

_CHAT_INFO_SECTIONS = (
    (
        "These are not chatbot assistants",
        (
            "If you are used to ChatGPT, Claude, or similar AI assistants, please adjust "
            "your expectations. These models have [bold]not[/bold] been fine-tuned to act "
            "as helpful assistants — they were trained only on large volumes of text.\n\n"
            "They behave as [bold]text completers[/bold]: they take whatever you write and "
            "continue generating more text in the same direction. They do not follow "
            "instructions, hold a conversation, or \"understand\" what you want unless "
            "your prompt naturally leads them that way."
        ),
    ),
    (
        "Extremely small, experimental models",
        (
            "The models here range from about [bold]1 million to 110 million parameters[/bold] "
            "— a tiny fraction of mainstream LLMs (which often have [bold]tens or hundreds of "
            "billions[/bold] of parameters, i.e. hundreds to thousands of times larger).\n\n"
            "Because of their size, output can be [bold]erratic, random, or nonsensical[/bold]. "
            "Facts may be completely wrong. Responses are generated statistically, not "
            "deliberately — they are [bold]not intended[/bold] to offend, accuse, or represent "
            "anyone or anything.\n\n"
            "Use this tool for experimentation only. Do not rely on these outputs for "
            "decisions, facts, or anything consequential."
        ),
    ),
)


class ChatInfoModal(ModalScreen):
    """Modal: warnings about how chat-screen models behave and their limitations."""

    BINDINGS = [("escape", "dismiss", "Close")]

    CSS = MODAL_CSS + """
    ChatInfoModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.65);
    }

    ChatInfoModal .modal-dialog {
        width: 95%;
        max-width: 140;
        height: 75%;
        max-height: 75%;
        padding: 2 3;
    }

    .chat-info-title {
        text-style: bold underline;
        height: auto;
        margin-bottom: 1;
        padding: 0 1;
        color: $text-warning;
        text-align: center;
        width: 100%;
    }

    .chat-info-columns {
        width: 100%;
        height: 1fr;
        overflow-y: auto;
        layout: horizontal;
    }

    .info-panel {
        width: 1fr;
        height: auto;
        padding: 1 2;
        margin: 0 1;
        background: $surface-darken-1;
        border: tall $primary 25%;
    }

    .info-panel-title {
        text-style: bold;
        margin: 0 0 1 0;
        padding: 0 1;
        color: $text;
        text-align: center;
        width: 100%;
    }

    .info-panel-body {
        padding: 0 1;
        color: $text-secondary;
        height: auto;
    }

    .chat-info-close {
        width: 100%;
        height: auto;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("⚠  Important Information", classes="chat-info-title")
            with Horizontal(classes="chat-info-columns"):
                for title, body in _CHAT_INFO_SECTIONS:
                    with Vertical(classes="info-panel"):
                        yield Label(title, classes="info-panel-title")
                        yield Static(body, classes="info-panel-body")
            yield Button("Close", variant="primary", id="close-chat-info", classes="chat-info-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-chat-info":
            self.dismiss()

    def action_dismiss(self) -> None:
        self.dismiss()


# ─────────────────────────────────────────────────────────────────────────────
#  Chat screen — sampling profile picker
# ─────────────────────────────────────────────────────────────────────────────

class SamplingProfileModal(ModalScreen[str | None]):
    """Modal: choose a sampling profile with description and parameter details."""

    BINDINGS = [("escape", "cancel", "Close")]

    CSS = MODAL_CSS + """
    SamplingProfileModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.65);
    }

    SamplingProfileModal .modal-dialog {
        width: 90%;
        max-width: 100;
        height: auto;
        max-height: 85%;
        padding: 2 3;
    }

    .sampling-modal-title {
        text-style: bold underline;
        height: auto;
        margin-bottom: 1;
        padding: 0 1;
        color: $text-warning;
        text-align: center;
        width: 100%;
    }

    .sampling-modal-hint {
        height: auto;
        margin-bottom: 2;
        padding: 0 2;
        color: $text-secondary;
        text-style: dim italic;
        text-align: center;
        width: 100%;
    }

    #preset-scroll {
        height: auto;
        max-height: 28;
        margin-bottom: 2;
        border: tall $primary 25%;
        background: $surface-darken-1;
    }

    #preset-list {
        height: auto;
        padding: 0 1;
    }

    #preset-list > ListItem {
        padding: 1 2;
        margin: 1 0;
        border: tall $primary 20%;
        background: $background;
    }

    #preset-list > ListItem:hover {
        background: $surface-darken-1;
    }

    #preset-list:focus > ListItem.-active {
        background: $primary 20%;
        border: tall $accent;
    }

    .preset-title {
        text-style: bold;
        height: auto;
        width: 100%;
    }

    .preset-desc {
        height: auto;
        width: 100%;
        margin: 1 0;
        color: $text-secondary;
        text-style: dim;
    }

    .preset-params {
        height: auto;
        width: 100%;
        color: $accent;
    }

    .sampling-modal-close {
        width: 100%;
        height: auto;
    }
    """

    def __init__(self, current_key: str) -> None:
        super().__init__()
        self.current_key = current_key

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("⚙  Sampling Profile", classes="sampling-modal-title")
            yield Static(
                "Choose how randomly the model picks each next token.",
                classes="sampling-modal-hint",
            )
            with ScrollableContainer(id="preset-scroll"):
                with ListView(id="preset-list"):
                    for key in PRESET_ORDER:
                        preset = SAMPLING_PRESETS[key]
                        marker = "● " if key == self.current_key else "  "
                        yield ListItem(
                            Label(f"{marker}{preset.label}", classes="preset-title"),
                            Static(preset.description, classes="preset-desc"),
                            Static(preset.params_summary(), classes="preset-params"),
                            id=key,
                        )
            yield Button("Cancel", variant="default", id="cancel-sampling", classes="sampling-modal-close")

    def on_mount(self) -> None:
        preset_list = self.query_one("#preset-list", ListView)
        try:
            preset_list.index = PRESET_ORDER.index(self.current_key)
        except ValueError:
            preset_list.index = 0

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "preset-list" and event.item.id:
            self.dismiss(event.item.id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-sampling":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
