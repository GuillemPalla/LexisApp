from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, RichLog, TextArea

class ChatScreen(Screen):
    """Second Screen: Separate dedicated space for conversing with loaded models."""
    CSS = """
    #main-chat {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    RichLog {
        background: $boost;
        border: tall $background;
        height: 75%;
    }
    TextArea {
        height: 15%;
    }
    #actions-row {
        height: auto;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-chat"):
            yield RichLog(id="chat-log", highlight=True, markup=True)
            yield TextArea(placeholder="Type your prompt here...", id="prompt-input")
            with Horizontal(id="actions-row"):
                yield Button("Send Prompt", id="send-btn", variant="success")
                yield Button("Switch Model", id="back-btn", variant="error")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#prompt-input").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            self.process_prompt()
        elif event.button.id == "back-btn":
            self.app.switch_screen("management")

    @work(exclusive=True, thread=True)
    def process_prompt(self) -> None:
        input_widget = self.query_one("#prompt-input", TextArea)
        chat_log = self.query_one("#chat-log", RichLog)
        
        prompt = input_widget.text.strip()
        if not prompt or not self.app.engine:
            return

        self.app.call_from_thread(chat_log.write, f"\n[bold cyan]User:[/bold cyan] {prompt}\n")
        self.app.call_from_thread(chat_log.write, "[bold green]LLM: [/bold green]")
        
        def clear_input(): input_widget.text = ""
        self.app.call_from_thread(clear_input)
        
        for token in self.app.engine.generate_stream(prompt):
            self.app.call_from_thread(chat_log.write, token, scroll_end=True)