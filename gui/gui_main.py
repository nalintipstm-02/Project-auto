from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from core.runtime_state import load_runtime_state
from kivy.config import Config

Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '480')
Config.set('graphics', 'resizable', True)

Builder.load_file("gui_dashboard.kv")

from gui.gui_screens_pro import RoomScreen, ControlScreen, PinScreen

class SmartRoomApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(RoomScreen(name="room"))
        sm.add_widget(ControlScreen(name="control"))
        sm.add_widget(PinScreen(name="pin"))
        return sm

if __name__ == "__main__":
    load_runtime_state()
    SmartRoomApp().run()
