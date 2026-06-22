import os
import sys

from textual.app import App

from screens.chat_screen import ChatScreen
from screens.model_management_screen import ModelManagementScreen

class LexisApp(App):
    """Main Orchestrating Application Class."""
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
    if sys.platform == "win32":
        os.system("chcp 65001 > nul")

    app = LexisApp()
    app.run()