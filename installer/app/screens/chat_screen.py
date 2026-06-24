import os
import sys
import threading

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, RichLog, TextArea, Label, Static

from model_inference import DEFAULT_PRESET_KEY, PRESET_ORDER, SAMPLING_PRESETS
from models_data import AVAILABLE_MODELS
from screens.modals import ChatInfoModal, SamplingProfileModal

_SAMPLING_BTN_MIN_WIDTH = max(len(f"⚙ {SAMPLING_PRESETS[key].label}") for key in PRESET_ORDER) + 2


class ChatScreen(Screen):
    """Text completion screen — the model continues from whatever the user writes."""

    CSS = """
    ChatScreen {
        background: $background;
    }

    #main-chat {
        width: 100%;
        height: 1fr;
        layout: vertical;
        padding: 1 2;
        background: $background;
        hatch: right $primary 12%;
    }

    #completions-log {
        background: $surface-darken-1;
        border: tall $primary 30%;
        height: 1fr;
        margin-bottom: 2;
        padding: 1 2;
        scrollbar-gutter: stable;
    }

    #completions-log:focus {
        border: tall $primary;
    }

    #prompt-label {
        height: auto;
        padding: 0 2 1 2;
        color: $text-secondary;
        text-style: dim italic;
    }

    TextArea {
        height: 20%;
        min-height: 4;
        margin-bottom: 0;
        padding: 1 2;
        border: tall $primary 30%;
        background: $surface-darken-1;
    }

    TextArea:focus {
        border: tall $accent;
        background: $background;
    }

    #chat-top-bar {
        height: auto;
        padding: 0 2 1 2;
        align: left middle;
    }

    #back-btn {
        min-width: 8;
    }

    #loaded-model-title {
        width: 1fr;
        text-align: center;
        text-style: bold;
        color: $text;
        content-align: center middle;
    }

    #actions-row {
        height: auto;
        padding: 1 2;
        margin-top: 1;
        align: left middle;
        background: $surface-darken-1;
        border-top: hkey $primary;
    }

    #actions-row Button {
        margin-right: 2;
        min-width: 16;
    }

    #sampling-btn {
        min-width: 28;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Each entry: {"prompt": str, "completion": str, "done": bool}
        self._history: list[dict] = []
        self._streaming: bool = False
        self._cancel_event: threading.Event = threading.Event()
        self._info_shown_this_visit: bool = False
        self._sampling_key: str = DEFAULT_PRESET_KEY

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-chat"):
            with Horizontal(id="chat-top-bar"):
                yield Button("Back", id="back-btn", variant="error")
                yield Static("", id="loaded-model-title")
                yield Button("⚠ Important Information", id="info-btn", variant="warning")
            yield RichLog(id="completions-log", highlight=False, markup=True, wrap=True)
            yield Label("Write your text and the model will continue it:", id="prompt-label")
            yield TextArea(id="prompt-input")
            with Horizontal(id="actions-row"):
                yield Button("Continue", id="send-btn", variant="success")
                yield Button("⚙ Sampling", id="sampling-btn", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self._reset_sampling_to_default()
        self._update_model_title()
        self.query_one("#prompt-input").focus()

    def on_screen_resume(self) -> None:
        self._update_model_title()
        if not self._info_shown_this_visit:
            self._reset_sampling_to_default()
            self._info_shown_this_visit = True
            self.call_after_refresh(self._show_info_modal)

    def _update_model_title(self) -> None:
        title = ""
        model_id = self.app.loaded_model_id
        if model_id and model_id in AVAILABLE_MODELS:
            title = AVAILABLE_MODELS[model_id]["title"]
        self.query_one("#loaded-model-title", Static).update(title)

    def _show_info_modal(self) -> None:
        self.app.push_screen(ChatInfoModal())

    def _update_sampling_button(self) -> None:
        preset = SAMPLING_PRESETS[self._sampling_key]
        label = f"⚙ {preset.label}"
        btn = self.query_one("#sampling-btn", Button)
        btn.label = label
        btn.styles.min_width = max(len(label) + 2, _SAMPLING_BTN_MIN_WIDTH)
    
    def _reset_sampling_to_default(self) -> None:
        self._sampling_key = DEFAULT_PRESET_KEY
        if self.app.engine:
            self.app.engine.set_sampling_preset(DEFAULT_PRESET_KEY)
        self._update_sampling_button()

    def _apply_sampling_preset(self, key: str) -> None:
        self._sampling_key = key
        if self.app.engine:
            self.app.engine.set_sampling_preset(key)
        self._update_sampling_button()

    def _open_sampling_modal(self) -> None:
        def on_result(key: str | None) -> None:
            if key and key in SAMPLING_PRESETS:
                self._apply_sampling_preset(key)

        self.app.push_screen(SamplingProfileModal(self._sampling_key), on_result)

    def _reset(self) -> None:
        """Cancel any active generation and clear all state and UI."""
        if self._streaming:
            self._cancel_event.set()

        self._history = []
        self._streaming = False
        self._cancel_event.clear()

        log = self.query_one("#completions-log", RichLog)
        log.clear()

        input_widget = self.query_one("#prompt-input", TextArea)
        input_widget.load_text("")

        send_btn = self.query_one("#send-btn", Button)
        send_btn.label = "Continue"
        send_btn.variant = "success"
        send_btn.disabled = False

        self._set_sampling_controls_disabled(False)

    def _set_sampling_controls_disabled(self, disabled: bool) -> None:
        self.query_one("#sampling-btn", Button).disabled = disabled

    # Rendering

    def _render_log(self) -> None:
        """Redraw the completions log from _history."""
        log = self.query_one("#completions-log", RichLog)
        log.clear()

        for i, entry in enumerate(self._history):
            if i > 0:
                # Visual separator between completions
                log.write("[dim]─" * 60 + "[/dim]")

            # Prompt and completion in one write so they flow on the same line
            log.write(
                f"[bold cyan]{entry['prompt']}[/bold cyan]"
                f"[yellow]{entry['completion']}[/yellow]",
                shrink=True,
            )

    # Event handling

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            if self._streaming:
                self._cancel_generation()
            else:
                self._submit_prompt()
        elif event.button.id == "back-btn":
            self._info_shown_this_visit = False
            self._reset()
            self.app.switch_screen("management")
        elif event.button.id == "info-btn":
            self._show_info_modal()
        elif event.button.id == "sampling-btn":
            self._open_sampling_modal()

    def _cancel_generation(self) -> None:
        """Signal the streaming worker to stop."""
        self._cancel_event.set()

    def _submit_prompt(self) -> None:
        if self._streaming:
            return

        input_widget = self.query_one("#prompt-input", TextArea)
        prompt = input_widget.text.strip()
        if not prompt or not self.app.engine:
            return

        # Snapshot the prompt and open a new history entry
        self._history.append({"prompt": prompt, "completion": "", "done": False})
        input_widget.text = ""
        self._render_log()

        # Swap button to Cancel while streaming
        send_btn = self.query_one("#send-btn", Button)
        send_btn.label = "Cancel"
        send_btn.variant = "warning"
        send_btn.disabled = False

        self._set_sampling_controls_disabled(True)
        self._cancel_event.clear()
        self._streaming = True

        self._stream_completion(prompt)

    # Streaming worker

    @work(exclusive=True, thread=True)
    def _stream_completion(self, prompt: str) -> None:
        """Run in a background thread; updates the last history entry token by token."""
        entry = self._history[-1]

        with open(os.devnull, "w") as devnull:
            old_stderr = sys.stderr
            sys.stderr = devnull
            try:
                for token_text in self.app.engine.generate(prompt):
                    if self._cancel_event.is_set():
                        break
                    entry["completion"] += token_text
                    # Re-render the whole log each token so the text appears inline
                    self.app.call_from_thread(self._render_log)
            finally:
                sys.stderr = old_stderr

        entry["done"] = True

        def _finish():
            self._streaming = False
            self._cancel_event.clear()
            send_btn = self.query_one("#send-btn", Button)
            send_btn.label = "Continue"
            send_btn.variant = "success"
            send_btn.disabled = False
            self._set_sampling_controls_disabled(False)
            self.query_one("#prompt-input").focus()

        self.app.call_from_thread(_finish)
