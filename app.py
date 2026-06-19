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
    
    def on_mount(self) -> None:
        self.push_screen("management")


if __name__ == "__main__":
    app = LexisApp()
    app.run()