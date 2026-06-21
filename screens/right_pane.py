"""
screens/right_pane.py
─────────────────────
Right-pane widget: tabbed model detail view (Overview / Specs / Architecture)
plus the action bar (Download / Load / Delete).
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static, TabbedContent, TabPane

from model_manager import get_model_size_mb, is_model_downloaded
from models_data import AVAILABLE_MODELS, ARCHITECTURES
from screens.modals import ArchFeatureModal


# ─────────────────────────────────────────────────────────────────────────────
#  Right pane
# ─────────────────────────────────────────────────────────────────────────────

class ModelDetailPane(Vertical):
    """
    Right panel: empty state → tabbed detail view → action bar.

    The parent screen calls `show_model(model_id)` whenever a selection changes.
    Button.Pressed events for action-btn / delete-btn bubble to the screen.
    """

    DEFAULT_CSS = """
    ModelDetailPane {
        width: 68%;
        height: 100%;
        layout: vertical;
        background: $background;
    }

    /* ── Empty state ────────────────────────────────────────────────────── */
    #empty-state {
        height: 1fr;
        align: center middle;
        color: $text-secondary;
        text-style: dim italic;
        hatch: right $primary 12%;
    }

    /* ── Tabs ───────────────────────────────────────────────────────────── */
    #details-tabs {
        height: 1fr;
    }

    #details-tabs > Tabs {
        background: $surface-darken-1;
        height: 4;
        border-bottom: hkey $primary;
    }

    #details-tabs Tab {
        padding: 1 4;
        height: 4;
        color: $text-muted;
        background: $surface-darken-1;
        border-right: vkey $primary-darken-1;
    }

    #details-tabs Tab.-active {
        color: $text-warning;
        text-style: bold underline;
        background: $background;
        border-bottom: none;
    }

    #details-tabs > ContentSwitcher {
        height: 1fr;
    }

    #details-tabs TabPane {
        height: 1fr;
        padding: 3 4;
        overflow-y: auto;
        scrollbar-gutter: stable;
        background: $background;
        hatch: right $primary 12%;
    }

    /* ── Overview tab ───────────────────────────────────────────────────── */
    .family-badge {
        width: auto;
        height: auto;
        padding: 1 2;
        margin-bottom: 2;
        background: $primary-muted 50%;
        color: $text-primary;
        text-style: bold;
    }

    #model-title-label {
        text-style: bold;
        color: $text;
        margin-bottom: 2;
        padding: 0 2;
    }

    #model-description {
        color: $text-secondary;
        text-style: dim italic;
        margin-bottom: 3;
        padding: 0 2;
    }

    /* Stat strip */
    .stat-strip {
        height: 7;
        margin-top: 2;
        margin-bottom: 2;
    }

    .stat-box {
        width: 1fr;
        height: 100%;
        margin-right: 1;
        border: tall $primary 30%;
        background: $surface-darken-1;
        align: center middle;
        padding: 1 2;
    }

    .stat-box:hover {
        background: $panel;
        border: tall $primary;
    }

    .stat-box:last-of-type {
        margin-right: 0;
    }

    .stat-num {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $text-success;
        padding: 0;
    }

    .stat-lbl {
        width: 100%;
        text-align: center;
        color: $text-muted;
        text-style: dim;
        padding: 0;
    }

    .stat-spacer {
        height: 1;
    }

    /* ── Specs tab ──────────────────────────────────────────────────────── */
    .spec-section-title {
        text-style: bold underline;
        color: $text-warning;
        margin-top: 2;
        margin-bottom: 2;
        padding: 1 2 1 3;
    }

    .specs-sep {
        height: 1;
        color: $primary-darken-2;
        margin: 2 0;
    }

    .spec-row {
        layout: horizontal;
        height: auto;
        min-height: 1;
        align: left middle;
        padding: 1 2 1 3;
        margin-left: 2;
        border-left: vkey $primary-darken-2;
    }

    .spec-row:hover {
        background: $foreground 4%;
        border-left: vkey $accent;
    }

    .spec-key {
        width: 24;
        color: $text-muted;
        height: auto;
    }

    .spec-value {
        width: 1fr;
        color: $text;
        text-style: bold;
        height: auto;
    }

    .spec-value-accent {
        width: 1fr;
        color: $text-success;
        text-style: bold;
        height: auto;
    }

    /* ── Architecture tab ───────────────────────────────────────────────── */
    .arch-family-title {
        text-style: bold underline;
        color: $text-warning;
        margin-bottom: 3;
        padding: 0 2 0 3;
    }

    #arch-features-container {
        width: 100%;
        height: auto;
        padding: 0 0 0 2;
        margin-left: 1;
        border-left: vkey $primary-darken-2;
    }

    .arch-feature-row {
        layout: horizontal;
        width: 100%;
        height: auto;
        min-height: 1;
        margin-bottom: 0;
        align: left middle;
        padding: 1 2;
        border: tall transparent;
    }

    .arch-feature-row:hover {
        background: $foreground 4%;
    }

    .arch-chip-label {
        width: 1fr;
        height: auto;
        color: $text;
        align: left middle;
    }

    .arch-chip-info-btn {
        width: 3;
        min-width: 3;
        max-width: 3;
        height: auto;
        padding: 0;
        margin: 0 0 0 1;
        border: none !important;
        background: transparent;
        color: $text-muted;
        text-style: none;
        content-align: center middle;
    }

    .arch-chip-info-btn:hover,
    .arch-chip-info-btn:focus {
        background: $accent;
        color: $background;
    }

    .arch-chip-info-btn:disabled {
        color: $text-muted 40%;
        background: transparent;
        text-style: dim;
    }

    .arch-swa-note {
        color: $text-warning;
        text-style: dim italic;
        margin-top: 3;
        padding: 1 3;
        border: round $warning 50%;
        height: auto;
    }

    /* ── Action bar ─────────────────────────────────────────────────────── */
    #action-bar {
        height: auto;
        padding: 1 2;
        align: right middle;
        background: $surface-darken-1;
        border-top: hkey $primary;
    }

    #action-btn {
        width: auto;
        min-width: 30;
        height: auto;
    }

    #delete-btn {
        width: auto;
        min-width: 14;
        height: auto;
        margin-left: 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._arch_btn_map: dict[str, tuple[str, str]] = {}  # btn_id → (model_id, feature)
        self._selected_model_id: str | None = None

    # ── Composition ──────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Static("←  Select a model to view its details", id="empty-state")

        with TabbedContent(id="details-tabs", initial="tab-overview"):
            # ── Overview ─────────────────────────────────────────────────
            with TabPane("Overview", id="tab-overview"):
                yield Static("", id="section-title-overview", classes="family-badge")
                yield Static("", id="model-title-label")
                yield Static("", id="model-description")
                with Horizontal(classes="stat-strip"):
                    with Vertical(classes="stat-box"):
                        yield Static("", classes="stat-spacer")
                        yield Static("", id="stat-parameters", classes="stat-num")
                        yield Static("Parameters", classes="stat-lbl")
                        yield Static("", classes="stat-spacer")
                    with Vertical(classes="stat-box"):
                        yield Static("", classes="stat-spacer")
                        yield Static("", id="stat-tokens", classes="stat-num")
                        yield Static("Tokens trained", classes="stat-lbl")
                        yield Static("", classes="stat-spacer")
                    with Vertical(classes="stat-box"):
                        yield Static("", classes="stat-spacer")
                        yield Static("", id="stat-disk", classes="stat-num")
                        yield Static("Disk size", classes="stat-lbl")
                        yield Static("", classes="stat-spacer")

            # ── Specs ────────────────────────────────────────────────────
            with TabPane("Specs", id="tab-specs"):
                yield Static("Model dimensions", classes="spec-section-title")
                yield Horizontal(
                    Static("Context window", classes="spec-key"),
                    Static("", id="spec-context", classes="spec-value"),
                    classes="spec-row",
                )
                yield Horizontal(
                    Static("Layers", classes="spec-key"),
                    Static("", id="spec-layers", classes="spec-value"),
                    classes="spec-row",
                )
                yield Horizontal(
                    Static("Attention heads", classes="spec-key"),
                    Static("", id="spec-heads", classes="spec-value"),
                    classes="spec-row",
                )
                yield Horizontal(
                    Static("KV heads (GQA)", classes="spec-key"),
                    Static("", id="spec-kv-heads", classes="spec-value"),
                    id="kv-heads-row",
                    classes="spec-row",
                )
                yield Horizontal(
                    Static("Embedding dim", classes="spec-key"),
                    Static("", id="spec-emb-dim", classes="spec-value"),
                    classes="spec-row",
                )
                yield Horizontal(
                    Static("SWA window size", classes="spec-key"),
                    Static("", id="spec-swa-window", classes="spec-value"),
                    id="swa-window-row",
                    classes="spec-row",
                )

                yield Static("─" * 40, classes="specs-sep")

                yield Static("Scale", classes="spec-section-title")
                yield Horizontal(
                    Static("Parameters", classes="spec-key"),
                    Static("", id="spec-parameters", classes="spec-value-accent"),
                    classes="spec-row",
                )
                yield Horizontal(
                    Static("Tokens trained", classes="spec-key"),
                    Static("", id="spec-tokens", classes="spec-value"),
                    classes="spec-row",
                )
                yield Horizontal(
                    Static("Disk size required", classes="spec-key"),
                    Static("", id="spec-disk", classes="spec-value"),
                    classes="spec-row",
                )

            # ── Architecture ─────────────────────────────────────────────
            with TabPane("Architecture", id="tab-arch"):
                yield Static("", id="arch-family-label", classes="arch-family-title")
                yield Vertical(id="arch-features-container")
                yield Static("", id="swa-pattern-note", classes="arch-swa-note")

        with Horizontal(id="action-bar"):
            yield Button("Select a model", id="action-btn", variant="primary", disabled=True)
            yield Button("🗑 Delete", id="delete-btn", variant="error", disabled=True)

    def on_mount(self) -> None:
        self.query_one("#details-tabs").display = False

    # ── Public API ────────────────────────────────────────────────────────────

    def show_model(self, model_id: str) -> None:
        """Populate all tabs with data for *model_id*."""
        self._selected_model_id = model_id
        info = AVAILABLE_MODELS[model_id]
        size_mb = get_model_size_mb(model_id)
        arch_family = info.get("arch_family", "")
        arch = ARCHITECTURES.get(arch_family, {"features": [], "details": {}})

        self.query_one("#empty-state").display = False
        self.query_one("#details-tabs").display = True

        self._populate_overview(info, size_mb, arch_family)
        self._populate_specs(info, size_mb)
        self._populate_architecture(model_id, info, arch_family, arch)
        self._update_action_buttons(model_id, size_mb)

    # ── Tab population helpers ────────────────────────────────────────────────

    def _populate_overview(self, info: dict, size_mb: int | None, arch_family: str) -> None:
        disk = info.get("disk_size_mb")
        disk_display = f"{size_mb} MB" if size_mb else (f"{disk} MB" if disk else "—")

        self.query_one("#section-title-overview", Static).update(arch_family)
        self.query_one("#model-title-label", Static).update(info["title"])
        self.query_one("#model-description", Static).update(info["description"])
        self.query_one("#stat-parameters", Static).update(info.get("parameters", "—"))
        self.query_one("#stat-tokens", Static).update(info.get("tokens_trained", "—"))
        self.query_one("#stat-disk", Static).update(disk_display)

    def _populate_specs(self, info: dict, size_mb: int | None) -> None:
        disk = info.get("disk_size_mb")
        disk_display = f"{size_mb} MB" if size_mb else (f"{disk} MB" if disk else "—")

        self.query_one("#spec-parameters", Static).update(info.get("parameters", "—"))
        self.query_one("#spec-tokens", Static).update(info.get("tokens_trained", "—"))
        self.query_one("#spec-disk", Static).update(disk_display)
        self.query_one("#spec-context", Static).update(
            f"{info.get('context_size', '—')} tokens"
        )
        self.query_one("#spec-layers", Static).update(str(info.get("layers", "—")))
        self.query_one("#spec-heads", Static).update(str(info.get("attention_heads", "—")))
        self.query_one("#spec-emb-dim", Static).update(str(info.get("embedding_dim", "—")))

        # Conditional rows
        kv_heads = info.get("kv_heads")
        kv_row = self.query_one("#kv-heads-row")
        if kv_heads:
            self.query_one("#spec-kv-heads", Static).update(str(kv_heads))
            kv_row.display = True
        else:
            kv_row.display = False

        swa_window = info.get("swa_window_size")
        swa_row = self.query_one("#swa-window-row")
        if swa_window:
            self.query_one("#spec-swa-window", Static).update(f"{swa_window} tokens")
            swa_row.display = True
        else:
            swa_row.display = False

    def _populate_architecture(
        self,
        model_id: str,
        info: dict,
        arch_family: str,
        arch: dict,
    ) -> None:
        self.query_one("#arch-family-label", Static).update(
            f"{arch_family} Architecture"
        )

        # Rebuild feature chips
        container = self.query_one("#arch-features-container", Vertical)
        container.remove_children()
        self._arch_btn_map.clear()

        features = arch.get("features", [])
        details = arch.get("details", {})

        new_rows: list[Horizontal] = []
        for i, feature in enumerate(features):
            btn_id = f"arch_info_{model_id}_{i}"
            self._arch_btn_map[btn_id] = (arch_family, feature)
            has_detail = feature in details
            new_rows.append(
                Horizontal(
                    Static(f"  ▸  {feature}", classes="arch-chip-label"),
                    Button(
                        "ℹ",
                        id=btn_id,
                        classes="arch-chip-info-btn",
                        flat=True,
                        compact=True,
                        disabled=not has_detail,
                    ),
                    classes="arch-feature-row",
                )
            )
        container.mount(*new_rows)

        # SWA pattern note
        swa_pattern = info.get("swa_pattern", "")
        swa_note = self.query_one("#swa-pattern-note", Static)
        if swa_pattern:
            swa_note.update(f"↔  Attention pattern: {swa_pattern}")
            swa_note.display = True
        else:
            swa_note.display = False

    def _update_action_buttons(self, model_id: str, size_mb: int | None) -> None:
        action_btn = self.query_one("#action-btn", Button)
        delete_btn = self.query_one("#delete-btn", Button)
        action_btn.disabled = False

        if is_model_downloaded(model_id):
            action_btn.label = "▶  Load Model"
            action_btn.variant = "success"
            delete_btn.disabled = False
        else:
            label = f"⬇  Download  ({size_mb} MB)" if size_mb else "⬇  Download"
            action_btn.label = label
            action_btn.variant = "primary"
            delete_btn.disabled = True

    # ── Architecture info button handler ──────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle arch feature info buttons; let others bubble."""
        btn_id = event.button.id
        if btn_id and btn_id.startswith("arch_info_") and btn_id in self._arch_btn_map:
            arch_family, feature = self._arch_btn_map[btn_id]
            arch = ARCHITECTURES.get(arch_family, {})
            detail = arch.get("details", {}).get(feature, "")
            if detail:
                self.app.push_screen(ArchFeatureModal(feature, detail))
            event.stop()  # consumed — don't propagate to the screen