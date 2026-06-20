"""
screens/left_pane.py
────────────────────
Left-pane widget: categorised model list with category info buttons.
"""

from collections import defaultdict

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical, Horizontal
from textual.widgets import Button, Label, ListItem, ListView, Static

from models_data import AVAILABLE_MODELS, DATASET_CATEGORIES


# ─────────────────────────────────────────────────────────────────────────────
#  Left pane
# ─────────────────────────────────────────────────────────────────────────────

class ModelListPane(Vertical):
    """
    Left panel: header + scrollable list of models grouped by category.

    Raises:
        Button.Pressed  — for the ℹ category buttons (id = "info_{cat_key}")
        ListView.Selected — for model-item selection
    Both bubble naturally to the parent screen.
    """

    DEFAULT_CSS = """
    ModelListPane {
        width: 32%;
        height: 100%;
        layout: vertical;
        border-right: vkey $primary-darken-1;
        background: $background;
    }

    /* ── Main List Header ───────────────────────────────────────────────── */
    #list-header {
        dock: top;
        padding: 0 2;
        background: $surface-darken-1;
        color: $accent;
        text-style: bold;
        height: 1;
        content-align: left middle;
        border-bottom: hkey $primary;
    }

    #model-scroll {
        height: 1fr;
        overflow-y: auto;
        scrollbar-gutter: stable;
        hatch: right $primary 12%;
    }

    .model-list-content {
        width: 100%;
        height: auto;
        padding: 1 0 2 0;
    }

    /* ── Category section ───────────────────────────────────────────────── */
    .category-section {
        width: 100%;
        height: auto;
        margin-top: 2;
    }

    .category-section:first-child {
        margin-top: 0;
    }

    .category-header-row {
        layout: horizontal;
        width: 100%;
        height: auto;
        padding: 0 2;
        align: left middle;
    }

    .info-btn {
        width: 3;
        min-width: 3;
        max-width: 3;
        height: auto;
        padding: 0;
        margin: 0 1 0 0;
        border: none !important;
        background: transparent;
        color: $text-muted;
        text-style: none;
        content-align: center middle;
    }

    .info-btn:hover,
    .info-btn:focus {
        background: $accent;
        color: $background;
    }

    .category-header-label {
        width: 1fr;
        color: $text-warning;
        text-style: bold underline;
        height: auto;
    }

    .category-short-description {
        padding: 0 2 0 6;
        color: $text-secondary;
        text-style: dim italic;
        height: auto;
    }

    /* ── Model list items ────────────────────────────────────────────────── */
    .category-list {
        height: auto;
        margin: 0 0 0 2;
        padding-left: 1;
        border-left: vkey $primary-darken-2;
        background: transparent;
    }

    .category-list:focus {
        border-left: vkey $accent;
    }

    ListItem {
        background: transparent;
        padding: 0;
        height: auto;
    }

    .model-item {
        padding: 0 2;
        height: 1;
        color: $text-muted;
    }

    ListItem:hover .model-item {
        color: $text;
        background: $foreground 4%;
    }

    ListItem.-active {
        background: $surface-darken-1;
    }

    ListItem.-active .model-item {
        color: $text;
    }

    ListView:focus > ListItem.-active {
        background: $panel;
    }

    ListView:focus > ListItem.-active .model-item {
        color: $accent;
        text-style: bold;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._grouped: dict[str, list[str]] = defaultdict(list)
        for model_id, info in AVAILABLE_MODELS.items():
            self._grouped[info.get("category", "__uncategorised__")].append(model_id)

    # ── Composition ──────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Label(" LEXIS MODELS", id="list-header")

        with ScrollableContainer(id="model-scroll"):
            with Vertical(classes="model-list-content"):
                for category_key, model_ids in self._grouped.items():
                    cat = DATASET_CATEGORIES.get(category_key, {
                        "label": category_key.replace("_", " ").title(),
                        "short_description": "",
                        "description": "",
                    })

                    with Vertical(classes="category-section"):
                        yield Horizontal(
                            Button(
                                "ℹ",
                                id=f"info_{category_key}",
                                classes="info-btn",
                                flat=True,
                                compact=True,
                            ),
                            Label(cat["label"], classes="category-header-label"),
                            classes="category-header-row",
                        )
                        yield Static(
                            cat.get("short_description", ""),
                            classes="category-short-description",
                        )

                        with ListView(id=f"list_{category_key}", classes="category-list"):
                            for model_id in model_ids:
                                info = AVAILABLE_MODELS[model_id]
                                yield ListItem(
                                    Label(f" {info['title']}", classes="model-item"),
                                    id=model_id,
                                )

    def on_mount(self) -> None:
        first_list = self.query(".category-list").first(ListView)
        if first_list:
            first_list.index = 0
