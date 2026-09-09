import math
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.dropdown import DropDown
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.utils import get_color_from_hex


class RoundedBox(BoxLayout):
    def __init__(self, bg_hex="#FFFFFF", radius=14, border_hex=None, border_width=1.5, **kwargs):
        super().__init__(**kwargs)
        self.border_hex = border_hex
        self.border_width = border_width
        self.radius_value = radius
        with self.canvas.before:
            Color(*get_color_from_hex(bg_hex))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
            if border_hex:
                from kivy.graphics import Line
                Color(*get_color_from_hex(border_hex))
                self.border_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, radius), width=border_width)
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        if self.border_hex:
            self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius_value)


def field_label(text):
    return Label(
        text=text,
        font_size=13,
        size_hint=(1, None),
        height=20,
        halign="left",
        valign="middle",
        color=get_color_from_hex("#6B7280"),
        font_name="Roboto",
    )


class HoverButton(Button):

    def __init__(self, base_hex="#FFFFFF", hover_hex="#F3F4F6", **kwargs):
        kwargs.setdefault("background_normal", "")
        super().__init__(**kwargs)
        self.base_hex = base_hex
        self.hover_hex = hover_hex
        self.background_color = get_color_from_hex(base_hex)
        self._is_hovering = False
        Window.bind(mouse_pos=self._on_mouse_pos)

    def _on_mouse_pos(self, window, pos):
        if not self.get_root_window():
            return
        inside = self.collide_point(*self.to_widget(*pos))
        if inside and not self._is_hovering:
            self._is_hovering = True
            self.background_color = get_color_from_hex(self.hover_hex)
        elif not inside and self._is_hovering:
            self._is_hovering = False
            self.background_color = get_color_from_hex(self.base_hex)

    def set_base_color(self, hex_color):
        self.base_hex = hex_color
        if not self._is_hovering:
            self.background_color = get_color_from_hex(hex_color)

    def set_colors(self, base_hex, hover_hex):
        self.base_hex = base_hex
        self.hover_hex = hover_hex
        if not self._is_hovering:
            self.background_color = get_color_from_hex(base_hex)


class SearchIcon(Widget):

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, 1))
        kwargs.setdefault("width", 32)
        super().__init__(**kwargs)
        with self.canvas:
            Color(*get_color_from_hex("#6B7280"))
            self.circle = Line(circle=(0, 0, 6), width=1.6)
            self.handle = Line(points=[0, 0, 0, 0], width=1.6)
        self.bind(pos=self.update_icon, size=self.update_icon)
        self.update_icon()

    def update_icon(self, *args):
        cx = self.x + self.width / 2 - 3
        cy = self.y + self.height / 2 + 2
        r = 6
        self.circle.circle = (cx, cy, r)
        angle = math.radians(45)
        hx1 = cx + r * math.cos(angle)
        hy1 = cy - r * math.sin(angle)
        hx2 = hx1 + 6 * math.cos(angle)
        hy2 = hy1 - 6 * math.sin(angle)
        self.handle.points = [hx1, hy1, hx2, hy2]


class LanguagePicker(RoundedBox):

    def __init__(self, options, default_text="", on_change=None, **kwargs):
        kwargs.setdefault("border_hex", "#D1D5DB")
        super().__init__(bg_hex="#FFFFFF", **kwargs)
        self.options = options
        self.selected_text = default_text
        self.on_change = on_change

        self.add_widget(SearchIcon())

        self.text_input = TextInput(
            text=default_text,
            hint_text="Search language...",
            multiline=False,
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            foreground_color=get_color_from_hex("#111827"),
            hint_text_color=get_color_from_hex("#9CA3AF"),
            font_size=16,
            font_name="Roboto",
            padding=[4, 14, 14, 14],
            cursor_color=get_color_from_hex("#1E88E5"),
        )
        self.text_input.bind(text=self.on_text_change)
        self.text_input.bind(focus=self.on_focus_change)
        self.text_input.bind(on_text_validate=self.on_enter_pressed)
        self.add_widget(self.text_input)

        self.dropdown = DropDown(auto_width=False)
        self.dropdown.bind(on_select=self.on_select)

        self._current_matches = []

    def on_focus_change(self, instance, is_focused):
        if is_focused:
            self.text_input.text = ""
        else:
            if self.text_input.text.strip() == "":
                self.text_input.text = self.selected_text

    def on_text_change(self, instance, typed_text):
        self.dropdown.clear_widgets()

        query = typed_text.strip().lower()

        if query == "":
            matches = sorted(self.options)
        else:
            starts_with = sorted(name for name in self.options if name.lower().startswith(query))
            contains = sorted(name for name in self.options if query in name.lower() and not name.lower().startswith(query))
            matches = starts_with + contains

        matches = matches[:30]
        self._current_matches = matches

        for i, name in enumerate(matches):
            is_first = (i == 0)
            base_color = "#EAF2FF" if is_first else "#FFFFFF"
            hover_color = "#D6E9FF" if is_first else "#F3F4F6"

            btn = HoverButton(
                text=name,
                base_hex=base_color,
                hover_hex=hover_color,
                size_hint_y=None,
                height=42,
                color=get_color_from_hex("#111827"),
                font_name="Roboto",
                font_size=15,
                bold=is_first,
            )
            btn.bind(on_release=lambda b: self.dropdown.select(b.text))
            self.dropdown.add_widget(btn)

        if matches and self.text_input.focus and self.text_input.get_root_window():
            self.dropdown.width = self.text_input.width
            if not self.dropdown.attach_to:
                self.dropdown.open(self.text_input)

    def on_enter_pressed(self, instance):
        if self._current_matches:
            self.dropdown.select(self._current_matches[0])

    def on_select(self, instance, selected_name):
        self.selected_text = selected_name
        self.text_input.text = selected_name
        self.text_input.focus = False
        if self.on_change:
            self.on_change(selected_name)

    def set_selection(self, name):
        self.selected_text = name
        self.text_input.text = name


class QuickLanguageBar(BoxLayout):

    def __init__(self, quick_options, full_options, default_text, on_change=None, **kwargs):
        kwargs.setdefault("size_hint", (1, None))
        kwargs.setdefault("height", 44)
        super().__init__(orientation="horizontal", spacing=8, **kwargs)
        self.quick_options = quick_options
        self.full_options = full_options
        self.on_change = on_change
        self.selected_text = default_text
        self.pill_buttons = {}

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=False, bar_width=0)
        self.inner = BoxLayout(orientation="horizontal", size_hint=(None, 1), spacing=8)
        self.inner.bind(minimum_width=self.inner.setter("width"))

        for name in quick_options:
            btn = self._make_pill(name)
            btn.bind(on_release=lambda b, n=name: self.select(n))
            self.inner.add_widget(btn)
            self.pill_buttons[name] = btn

        self.more_btn = self._make_pill("Search")
        self.more_btn.bind(on_release=self.open_search)
        self.inner.add_widget(self.more_btn)

        scroll.add_widget(self.inner)
        self.add_widget(scroll)

        self._build_search_dropdown()
        self._refresh_highlight()

    def _make_pill(self, name):
        width = max(100, len(name) * 9 + 30)
        return HoverButton(
            text=name,
            base_hex="#FFFFFF",
            hover_hex="#F3F4F6",
            size_hint=(None, 1),
            width=width,
            color=get_color_from_hex("#111827"),
            font_name="Roboto",
            font_size=14,
        )

    def _build_search_dropdown(self):
        self.search_dropdown = DropDown(auto_width=False)

        container = BoxLayout(orientation="vertical", size_hint_y=None, spacing=4, padding=8)
        container.bind(minimum_height=container.setter("height"))

        self.search_input = TextInput(
            hint_text="Search language...",
            multiline=False,
            size_hint_y=None,
            height=40,
            font_name="Roboto",
            font_size=15,
        )
        container.add_widget(self.search_input)

        self.results_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        self.results_box.bind(minimum_height=self.results_box.setter("height"))
        container.add_widget(self.results_box)

        self.search_dropdown.add_widget(container)
        self.search_input.bind(text=self._update_search_results)
        self._update_search_results(None, "")

    def _update_search_results(self, instance, typed_text):
        self.results_box.clear_widgets()
        query = typed_text.strip().lower()
        matches = self.full_options if query == "" else [n for n in self.full_options if query in n.lower()]
        matches = matches[:30]

        for name in matches:
            btn = HoverButton(
                text=name,
                base_hex="#FFFFFF",
                hover_hex="#F3F4F6",
                size_hint_y=None,
                height=40,
                color=get_color_from_hex("#111827"),
                font_name="Roboto",
                font_size=14,
            )
            btn.bind(on_release=lambda b, n=name: self._pick_from_search(n))
            self.results_box.add_widget(btn)

    def _pick_from_search(self, name):
        self.select(name)
        self.search_dropdown.dismiss()

    def open_search(self, instance):
        self.search_dropdown.width = 280
        if not self.search_dropdown.attach_to:
            self.search_dropdown.open(self.more_btn)

    def select(self, name, fire_callback=True):
        self.selected_text = name
        self._refresh_highlight()
        if fire_callback and self.on_change:
            self.on_change(name)

    def _refresh_highlight(self):
        for name, btn in self.pill_buttons.items():
            if name == self.selected_text:
                btn.set_colors("#1E88E5", "#1976D2")
                btn.color = get_color_from_hex("#FFFFFF")
                btn.bold = True
            else:
                btn.set_colors("#FFFFFF", "#F3F4F6")
                btn.color = get_color_from_hex("#111827")
                btn.bold = False

        if self.selected_text in self.pill_buttons:
            self.more_btn.text = "Search"
            self.more_btn.set_colors("#FFFFFF", "#F3F4F6")
            self.more_btn.color = get_color_from_hex("#111827")
        else:
            self.more_btn.text = self.selected_text
            self.more_btn.set_colors("#1E88E5", "#1976D2")
            self.more_btn.color = get_color_from_hex("#FFFFFF")