from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line
from datetime import date, timedelta, datetime

from gui.gui_db_pro import *
import core.device_controller as dc
from core.runtime_state import get_runtime_state

class DeviceButton(ToggleButton):
    bg_color = ListProperty([0.3, 0.3, 0.3, 1])
    
class DashboardScreen(Screen):
    def on_enter(self):
        self.ids.room_list.clear_widgets()
        rooms = [{"name": "CP9421"}, {"name": "CP9422"}]
        
        for r in rooms:
            btn = Button(
                text=r["name"],
                size_hint_y=None,
                height=dp(70),
                background_normal='',
                background_color=(0.05, 0.1, 0.15, 1),
                font_size=dp(18),
                bold=True
            )

            def update_canvas(instance, value):
                instance.canvas.after.clear()
                with instance.canvas.after:
                    Color(0, 0.7, 1, 1)
                    Line(rounded_rectangle=(instance.x, instance.y, instance.width, instance.height, dp(12)), 
                         width=dp(1.5))
            
            btn.bind(pos=update_canvas, size=update_canvas)
            btn.bind(on_release=lambda x, name=r["name"]: self.change_screen(name))
            self.ids.room_list.add_widget(btn)

    def open_room(self, room_id, room_name):
        s = self.manager.get_screen("room")
        s.room_id = room_id
        s.room_name = room_name
        self.manager.current = "room"

    def go_control_room(self):
        room_name = self.ids.room_spinner.text
        pin = self.manager.get_screen("pin")
        pin.room_name = room_name
        self.manager.current = "pin"

class ControlButton(ButtonBehavior, BoxLayout):
    text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.height = dp(65)
        self.padding = dp(10)

        with self.canvas.before:
            Color(0.1, 0.7, 0.9, 1)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(15)]
            )

        self.bind(pos=self.update_rect, size=self.update_rect)

        self.label = Label(
            text=self.text,
            font_size=dp(18),
            bold=True,
            color=(1, 1, 1, 1),
            halign="center",
            valign="middle"
        )
        self.label.bind(size=lambda s, w: setattr(s, 'text_size', w))
        self.add_widget(self.label)
        self.bind(text=self.update_text)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update_text(self, instance, value):
        self.label.text = value

class RoomScreen(Screen):
    room_name = StringProperty("")
    room_id = NumericProperty(0)

    def update_clock(self, dt):
        self.ids.clock.text = datetime.now().strftime("%H:%M:%S")

    def update_dashboard(self):
        now = datetime.now()
        booking = get_current_booking(self.room_id)

        if booking:
            start = booking["start_time"]
            end = booking["end_time"]
            today = date.today()
            tomorrow = today + timedelta(days=1)
            booking_date = start.date()

            if booking_date == today:
                day_text = "Today"
            elif booking_date == tomorrow:
                day_text = "Tomorrow"
            else:
                day_text = start.strftime("%d %b")

            self.ids.current_time.text = f"{day_text} {start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
            left = end - now
            mins = int(left.total_seconds() / 60)
            if mins < 0: mins = 0

            self.ids.time_left.text = f"Time Left: {mins} min"
            total = (end - start).total_seconds()
            passed = (now - start).total_seconds()
            percent = (passed / total) * 100 if total > 0 else 0
            percent = max(0, min(100, percent))
            self.ids.booking_progress.value = percent
        else:
            self.ids.current_time.text = "-"
            self.ids.time_left.text = ""
            self.ids.booking_progress.value = 0

        # Upcoming Bookings
        today = date.today()
        tomorrow = today + timedelta(days=1)
        bookings = get_future_bookings(self.room_id)
        self.ids.upcoming.clear_widgets()

        next_booking = None
        status_colors = {
            "approved": (0.2, 0.9, 0.5, 1),
            "pending": (1, 0.7, 0.2, 1),
            "rejected": (1, 0.3, 0.3, 1),
            "cancel": (0.6, 0.6, 0.6, 1),
            "cancel_by_admin": (0.5, 0.5, 0.5, 1)
        }

        for b in bookings:
            start = b["start_time"]
            end = b["end_time"]
            status = b["status"]
            booking_date = start.date()

            if booking_date == today: day_text = "Today"
            elif booking_date == tomorrow: day_text = "Tomorrow"
            else: day_text = start.strftime("%d %b")

            card = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(60),
                padding=dp(10),
                spacing=dp(15)
            )

            with card.canvas.before:
                Color(0.07, 0.15, 0.25, 0.8)
                rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])

            card.bind(pos=lambda i, v: setattr(rect, 'pos', i.pos), size=lambda i, v: setattr(rect, 'size', i.size))

            day_label = Label(text=day_text, size_hint_x=None, width=dp(100), font_size=dp(15), bold=True)
            time_label = Label(text=f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}", font_size=dp(16))
            status_color = status_colors.get(status, (0.8, 0.8, 0.8, 1))
            status_label = Label(text=status.upper(), size_hint_x=None, width=dp(120), bold=True, color=status_color, font_size=dp(14))

            card.add_widget(day_label)
            card.add_widget(time_label)
            card.add_widget(status_label)
            self.ids.upcoming.add_widget(card)

            if not next_booking and start > now:
                next_booking = b

        if next_booking:
            start = next_booking["start_time"]
            end = next_booking["end_time"]
            booking_date = start.date()
            if booking_date == today: day_text = "Today"
            elif booking_date == tomorrow: day_text = "Tomorrow"
            else: day_text = start.strftime("%d %b")
            self.ids.next_time.text = f"{day_text} {start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
        else:
            self.ids.next_time.text = "-"

        # Device Status Updates
        self.ids.device_status.clear_widgets()
        runtime = get_runtime_state()
        devices = get_devices_by_room(self.room_id)

        for d in devices:
            node_id = d["node_id"]
            name = d["node_name"]
            node_type = d["node_type"]

            if node_type == "led":
                channels = runtime.get("device_channels", {}).get(node_id)
                if channels:
                    for ch in channels:
                        channel_id = ch.get("channel_id", 0)
                        status = get_device_status(node_id, channel_id)
                        self.add_device_card(f"{name} {channel_id}", node_type, status)
                else:
                    status = get_device_status(node_id, 0)
                    self.add_device_card(name, node_type, status)
            else:
                status = get_device_status(node_id, 0)
                self.add_device_card(name, node_type, status)

    def add_device_card(self, name, node_type, status):
        icon_map = {
            "projector": "icons/projector.png",
            "air_conditioner": "icons/air.png",
            "led": "icons/led.png",
            "audio_equipment": "icons/audio.png",
            "computer": "icons/computer.png",
            "door": "icons/door.png"
        }

        status_text = "ON" if status == "on" else "OFF"
        status_color = (0, 1, 0, 1) if status == "on" else (1, 0, 0, 1)

        box = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(dp(110), dp(115)),
            spacing=dp(5),
            padding=dp(5)
        )

        icon = Image(
            source=icon_map.get(node_type, "icons/device.png"),
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            pos_hint={"center_x": 0.5}
        )

        name_label = Label(
            text=name,
            font_size=dp(12),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(30),
            text_size=(dp(100), None),
            color=(0.8, 0.9, 1, 1)
        )

        status_label = Label(
            text=status_text,
            font_size=dp(14),
            bold=True,
            size_hint_y=None,
            height=dp(20),
            color=status_color
        )

        box.add_widget(icon)
        box.add_widget(name_label)
        box.add_widget(status_label)
        self.ids.device_status.add_widget(box)

    def open_control(self):
        pin = self.manager.get_screen("pin")
        pin.room_id = self.room_id
        pin.room_name = self.room_name
        self.manager.current = "pin"

    def on_enter(self):
        if "room_selector" not in self.ids: return
        spinner = self.ids.room_selector
        rooms = get_rooms()
        spinner.values = [r["name"] for r in rooms]

        if rooms:
            spinner.text = rooms[0]["name"]
            self.room_id = rooms[0]["id"]
            self.room_name = rooms[0]["name"]

        self.ids.date_label.text = datetime.now().strftime("%d %b %Y")
        self.update_dashboard()
        Clock.schedule_interval(self.update_clock, 1)
        Clock.schedule_interval(lambda dt: self.update_dashboard(), 5)

    def change_room(self, room_name):
        rooms = get_rooms()
        for r in rooms:
            if r["name"] == room_name:
                self.room_id = r["id"]
                self.room_name = r["name"]
                break
        self.update_dashboard()

class PinScreen(Screen):
    room_name = StringProperty("")
    entered = StringProperty("")
    current_date = StringProperty("")
    current_time = StringProperty("")
    room_id = NumericProperty(0)

    def on_enter(self):
        Clock.schedule_interval(self.update_time, 1)

    def update_time(self, *args):
        now = datetime.now()
        self.current_date = now.strftime("%d %b %Y")
        self.current_time = now.strftime("%H:%M:%S")

    def add(self, num):
        if len(self.entered) < 4:
            self.entered += num

    def clear(self):
        self.entered = ""

    def check(self):
        room_name = self.room_name.strip()
        expected_pin = "".join(char for char in room_name if char.isdigit())
        if self.entered == expected_pin:
            control = self.manager.get_screen("control")
            control.room_name = self.room_name
            control.room_id = self.room_id

            self.entered = ""
            self.manager.current = "control"
        else:
            print("Wrong PIN")
            self.entered = ""
            
class RoundedButton(Button):
    def __init__(self, bg_color=(0.3, 0.3, 0.3, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.bold = True
        self.base_color = bg_color

        with self.canvas.before:
            self.bg_color = Color(*bg_color)
            self.rect = RoundedRectangle(radius=[dp(12)])

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_press(self):
        self.bg_color.rgba = (self.base_color[0]*0.85, self.base_color[1]*0.85, self.base_color[2]*0.85, 1)

    def on_release(self):
        self.bg_color.rgba = self.base_color

class ControlScreen(Screen):
    room_name = StringProperty("")
    room_id = NumericProperty(0)
    icon_map = {
        "projector": "icons/projector.png",
        "air_conditioner": "icons/air.png",
        "led": "icons/led.png",
        "audio_equipment": "icons/audio.png",
        "computer": "icons/computer.png",
        "door": "icons/door.png"
    }

    def on_enter(self):
        now = datetime.now()
        self.ids.date_label.text = now.strftime("%d %b %Y")
        Clock.schedule_interval(self.update_clock, 1)
        self.load_tabs()
        self.ids.carousel.bind(index=self.on_carousel_index)
        self.switch_tab("lights")
        self.event = Clock.schedule_interval(self.refresh_status, 2)

    def update_clock(self, dt):
        self.ids.clock.text = datetime.now().strftime("%H:%M:%S")

    def on_leave(self):
        if hasattr(self, "event"):
            self.event.cancel()

    def load_tabs(self):
        self.ids.carousel.clear_widgets()
        devices = get_devices_by_room(self.room_id)
        runtime = get_runtime_state()

        order = ["led", "air_conditioner", "computer", "projector", "audio_equipment", "door"]
        groups = {k: [] for k in order}

        for d in devices:
            t = d["node_type"]
            if t in groups:
                groups[t].append(d)

        self.toggles = {}
        for t in order:
            page = self.create_page(groups[t], runtime)
            self.ids.carousel.add_widget(page)

    def create_page(self, devices, runtime):
        root = BoxLayout(orientation="vertical")
        scroll = ScrollView()
        grid = GridLayout(
            cols=1,
            spacing=dp(15),
            padding=dp(20),
            size_hint_y=None
        )
        grid.bind(minimum_height=grid.setter("height"))

        for d in devices:
            node_id = d["node_id"]
            name = d["node_name"]
            node_type = d["node_type"]

            if node_type == "led":
                channels = runtime.get("device_channels", {}).get(node_id, [])
                if channels:
                    for ch in channels:
                        grid.add_widget(self.device_card(f"{name} CH{ch['channel_id']}", node_id, node_type, ch["gpio"], ch["channel_id"]))
                else:
                    grid.add_widget(self.device_card(name, node_id, node_type, None, 0))
            else:
                grid.add_widget(self.device_card(name, node_id, node_type, None, 0))

        scroll.add_widget(grid)
        root.add_widget(scroll)
        return root

    def device_card(self, name, node_id, node_type, gpio, channel):
        status = get_device_status(node_id, channel)
        status_text = "ON" if status == "on" else "OFF"
        status_color = (0.3, 1, 0.6, 1) if status == "on" else (1, 0.4, 0.4, 1)

        card = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(90),
            padding=dp(15),
            spacing=dp(15)
        )

        with card.canvas.before:
            Color(0.06, 0.15, 0.22, 0.95)
            rect = RoundedRectangle(radius=[dp(15)])

        card.bind(pos=lambda i, v: setattr(rect, 'pos', i.pos), size=lambda i, v: setattr(rect, 'size', i.size))

        icon = Image(source=self.icon_map.get(node_type, "icons/device.png"), size_hint=(None, None), size=(dp(50), dp(50)))
        label = Label(text=name, font_size=dp(16), color=(0.85, 0.95, 1, 1), size_hint_x=0.4, halign="left", valign="middle")
        label.bind(size=lambda s, w: setattr(s, 'text_size', w))
        
        status_label = Label(text=status_text, color=status_color, size_hint_x=None, width=dp(70), font_size=dp(16), bold=True)

        if not hasattr(self, "status_labels"): self.status_labels = {}
        self.status_labels[(node_id, channel)] = status_label

        card.add_widget(icon)
        card.add_widget(label)
        card.add_widget(status_label)

        if node_type == "computer":
            on_text, off_text = ("Wake", "Shutdown") if "student" not in name.lower() else (None, "Shutdown")
        elif node_type == "door": on_text, off_text = ("Open", "Close")
        elif node_type in ["air_conditioner", "projector"]: on_text, off_text = ("Start", "Stop")
        else: on_text, off_text = ("ON", "OFF")

        if on_text:
            btn_on = RoundedButton(text=on_text, size=(dp(80), dp(35)), size_hint=(None, None), bg_color=(0.0, 0.7, 0.4, 1), font_size=dp(14))
            btn_on.bind(on_release=lambda x: self.send_action(node_id, node_type, gpio, channel, "on"))
            btn_on_wrap = AnchorLayout(anchor_y="center", size_hint_x=None, width=dp(90))
            btn_on_wrap.add_widget(btn_on)
            card.add_widget(btn_on_wrap)

        btn_off = RoundedButton(text=off_text, size=(dp(80), dp(35)), size_hint=(None, None), bg_color=(0.8, 0.25, 0.25, 1), font_size=dp(14))
        btn_off.bind(on_release=lambda x: self.send_action(node_id, node_type, gpio, channel, "off"))
        btn_off_wrap = AnchorLayout(anchor_y="center", size_hint_x=None, width=dp(90))
        btn_off_wrap.add_widget(btn_off)
        card.add_widget(btn_off_wrap)

        return card

    def send_action(self, node_id, node_type, gpio, channel, action):
        runtime = get_runtime_state()
        success = False
        try:
            if node_type == "led" and gpio:
                dc.led_bulk_auto(node_id, [gpio], action, runtime)
                success = True
            elif node_type == "led":
                dc.led_auto(node_id, action, runtime)
                success = True
            else:
                dc.control_device(node_id, action, runtime)
                success = True
        except Exception as e:
            print("send fail:", e)

        if success:
            for i in range(5):
                Clock.schedule_once(lambda dt, i=i: self.refresh_status(0), i * 0.3)

    def refresh_status(self, dt):
        if not hasattr(self, "status_labels"): return
        for key, label in self.status_labels.items():
            node_id, channel = key
            status = get_device_status(node_id, channel)
            if status == "on":
                label.text = "ON"
                label.color = (0, 1, 0, 1)
            else:
                label.text = "OFF"
                label.color = (1, 0, 0, 1)

    def switch_tab(self, tab):
        mapping = {"lights": 0, "air": 1, "computer": 2, "projector": 3, "audio": 4, "door": 5}
        index = mapping.get(tab, 0)
        if index < len(self.ids.carousel.slides):
            self.ids.carousel.index = index
        self.update_tab_color(tab)

    def on_carousel_index(self, instance, value):
        mapping = {0: "lights", 1: "air", 2: "computer", 3: "projector", 4: "audio", 5: "door"}
        self.update_tab_color(mapping.get(value, "lights"))

    def update_tab_color(self, active):
        normal = (0.12, 0.2, 0.28, 1)
        active_color = (0.08, 0.7, 0.9, 1)
        tabs = {
            "lights": self.ids.btn_lights, "air": self.ids.btn_air,
            "computer": self.ids.btn_computer, "projector": self.ids.btn_projector,
            "audio": self.ids.btn_audio, "door": self.ids.btn_door
        }
        for name, btn in tabs.items():
            btn.bg_color = active_color if name == active else normal
