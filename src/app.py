import sys
from pathlib import Path

# Explicitly add the 'app' directory to Python's module search path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from textual.app import App
from screens.chat_screen import ChatScreen
from screens.model_management_screen import ModelManagementScreen

class LexisApp(App):
    SCREENS = {
        "management": ModelManagementScreen,
        "chat": ChatScreen
    }
    def __init__(self):
        super().__init__()
        self.engine = None
        self.loaded_model_id: str | None = None

    def on_mount(self) -> None:
        self.theme = "gruvbox"
        self.push_screen("management")

if __name__ == "__main__":
    LexisApp().run()