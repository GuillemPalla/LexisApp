# THIS FILE HAS BEEN AI GENERATED

from collections import defaultdict

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical, Horizontal
from textual.widgets import Button, Label, ListItem, ListView, Static

from models_data import AVAILABLE_MODELS, DATASET_CATEGORIES

PANE_TITLE = "[bold $accent]Ｌ　Ｅ　Ｘ　Ｉ　Ｓ[/]"


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

    /* ── Pane header ────────────────────────────────────────────────────── */
    #pane-logo {
        width: 100%;
        height: auto;
        min-height: 1;
        padding: 1 1;
        background: $surface-darken-1;
        color: $accent;
        text-style: bold;
        text-align: center;
        content-align: center middle;
        border-bottom: hkey $primary;
    }

    #model-scroll {
        height: 1fr;
        overflow-y: auto;
        hatch: right $primary 12%;
        padding-top: 1;
    }

    .model-list-content {
        width: 100%;
        height: auto;
        padding: 0;
    }

    /* ── Category section ───────────────────────────────────────────────── */
    .category-section {
        width: 100%;
        height: auto;
        margin-top: 1;
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
        padding: 0 1 0 4;
        color: $text-secondary;
        text-style: dim italic;
        height: 1;
    }

    /* ── Model list items ────────────────────────────────────────────────── */
    .category-list {
        height: auto;
        margin: 0 0 0 1;
        padding: 1 0 0 1;
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
        margin: 0;
    }

    .model-item {
        width: 100%;
        padding: 0 1;
        height: 2;
        color: $text-muted;
        content-align: left middle;
    }

    ListItem:hover .model-item {
        color: $text;
        background: $foreground 4%;
    }

    ListItem.is-selected .model-item {
        color: $text;
        text-style: bold;
        background: $surface-darken-1;
    }

    ListView:focus ListItem.is-selected .model-item {
        color: $accent;
        background: $panel;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._selected_model_id: str | None = None
        self._items_by_id: dict[str, ListItem] = {}
        self._grouped: dict[str, list[str]] = defaultdict(list)
        for model_id, info in AVAILABLE_MODELS.items():
            self._grouped[info.get("category", "__uncategorised__")].append(model_id)

    # ── Selection ────────────────────────────────────────────────────────────

    def _apply_selection(self, model_id: str | None) -> None:
        """Highlight exactly one model row across all category lists."""
        prev = self._selected_model_id
        if prev == model_id:
            return
        if prev and prev in self._items_by_id:
            self._items_by_id[prev].remove_class("is-selected")
        self._selected_model_id = model_id
        if model_id and model_id in self._items_by_id:
            self._items_by_id[model_id].add_class("is-selected")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Keep a single global selection — clear stale highlights in other lists."""
        for list_view in self.query(".category-list"):
            if list_view is not event.list_view and list_view.index is not None:
                list_view.index = None

        model_id = event.item.id if event.item else None
        self._apply_selection(model_id)

    # ── Composition ──────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Static(PANE_TITLE, id="pane-logo")

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
                                    Label(info["title"], classes="model-item"),
                                    id=model_id,
                                )

    def on_mount(self) -> None:
        self._items_by_id = {
            item.id: item for item in self.query("ListItem") if item.id
        }
        for list_view in self.query(".category-list"):
            list_view.index = None
