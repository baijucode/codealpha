import os
import sys
import subprocess
import threading
import tempfile
import uuid
import traceback
import pyaudio
import speech_recognition as sr
from gtts import gTTS
from deep_translator import GoogleTranslator
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.audio import SoundLoader
from kivy.core.clipboard import Clipboard
from kivy.graphics import Color, RoundedRectangle
from kivy.utils import get_color_from_hex
from kivy.clock import Clock

from widgets import RoundedBox, HoverButton, LanguagePicker, QuickLanguageBar
from languages import lang_list, code_for, MIC_LOCALE_MAP, resolve_gtts_lang_code
from audio_utils import format_speech_text
from grammar_check import check_and_fix_grammar
from name_protection import protect_proper_nouns, restore_proper_nouns
from fonts import APP_FONT


class TranslatorLayout(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 24
        self.spacing = 14

        title = Label(
            text="Language Translator",
            font_size=26,
            size_hint=(1, 0.09),
            bold=True,
            color=get_color_from_hex("#111827"),
            font_name="Roboto",  # kivy default font renders latin text more reliably than GoNotoKurrent at small sizes
        )
        self.add_widget(title)

        lang_row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=44, spacing=8)

        self.source_bar = QuickLanguageBar(
            quick_options=["english", "nepali", "hindi", "french", "spanish"],
            full_options=lang_list,
            default_text="english",
            size_hint=(0.45, 1),
        )
        lang_row.add_widget(self.source_bar)

        self.swap_btn = HoverButton(
            text="Swap\nlanguages",
            base_hex="#E5E7EB",
            hover_hex="#D1D5DB",
            size_hint=(0.1, 1),
            color=get_color_from_hex("#374151"),
            font_name="Roboto",  # kivy default font renders latin text more reliably than GoNotoKurrent at small sizes
            font_size=11,
            halign="center",
            bold=True,
        )
        self.swap_btn.bind(on_release=self.swap_languages)
        lang_row.add_widget(self.swap_btn)

        default_target = "french" if "french" in lang_list else lang_list[0]
        self.target_bar = QuickLanguageBar(
            quick_options=["english", "nepali", "french", "spanish", "arabic"],
            full_options=lang_list,
            default_text=default_target,
            size_hint=(0.45, 1),
        )
        lang_row.add_widget(self.target_bar)

        self.add_widget(lang_row)

        search_row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=48, spacing=8)

        self.source_search = LanguagePicker(
            options=lang_list,
            default_text="english",
            on_change=self._on_source_search_change,
            size_hint=(0.45, 1),
        )
        self.source_search.text_input.hint_text = "Search source language..."
        search_row.add_widget(self.source_search)

        search_row.add_widget(BoxLayout(size_hint=(0.1, 1)))   # spacer matching the swap button's width above

        self.target_search = LanguagePicker(
            options=lang_list,
            default_text=default_target,
            on_change=self._on_target_search_change,
            size_hint=(0.45, 1),
        )
        self.target_search.text_input.hint_text = "Search target language..."
        search_row.add_widget(self.target_search)

        self.add_widget(search_row)

        self.source_bar.on_change = self._on_source_bar_change
        self.target_bar.on_change = self._on_target_bar_change

        panels_row = BoxLayout(orientation="horizontal", size_hint=(1, 1), spacing=0)

        # left panel: white background with a visible border, where the user types
        input_card = RoundedBox(bg_hex="#FFFFFF", border_hex="#D1D5DB", size_hint=(0.5, 1), padding=14, radius=10)
        self.input_box = TextInput(
            hint_text="Enter text",
            multiline=True,
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),   # transparent - the RoundedBox behind it shows through
            foreground_color=get_color_from_hex("#111827"),
            hint_text_color=get_color_from_hex("#9CA3AF"),
            font_size=18,
            font_name=APP_FONT,
            padding=[4, 4, 4, 4],
            cursor_color=get_color_from_hex("#1E88E5"),
        )
        
        self.input_box.bind(text=self.on_input_text_change)
        input_card.add_widget(self.input_box)
        panels_row.add_widget(input_card)

        # thin vertical divider between the two panels, like Google's layout
        divider = BoxLayout(size_hint=(None, 1), width=1)
        with divider.canvas:
            Color(*get_color_from_hex("#D1D5DB"))
            self.divider_rect = RoundedRectangle(pos=divider.pos, size=divider.size)
        divider.bind(pos=lambda inst, val: setattr(self.divider_rect, "pos", val))
        divider.bind(size=lambda inst, val: setattr(self.divider_rect, "size", val))
        panels_row.add_widget(divider)


        result_card = RoundedBox(bg_hex="#E8EAED", border_hex="#D1D5DB", size_hint=(0.5, 1), padding=14, radius=10)

        self.result_label = Label(
            text="Translation",
            font_size=18,
            font_name=APP_FONT,
            size_hint_y=None,             # sizes itself to fit its own text content...
            text_size=(None, None),        # width gets bound below once the card's actual size is known
            halign="left",
            valign="top",
            color=get_color_from_hex("#9CA3AF"),   # starts gray like a placeholder, darkens once translated
        )
        # ...and this keeps the label's height in sync with however tall the text actually is
        self.result_label.bind(texture_size=lambda inst, val: setattr(self.result_label, "height", val[1]))

        result_scroll = ScrollView(do_scroll_x=False)
        result_scroll.add_widget(self.result_label)
        result_card.add_widget(result_scroll)
        result_scroll.bind(size=self.update_result_text_size)

        panels_row.add_widget(result_card)

        self.add_widget(panels_row)

        self.translate_btn = HoverButton(
            text="Translate",
            base_hex="#1E88E5",
            hover_hex="#1976D2",
            size_hint=(1, None),
            height=46,
            font_size=17,
            bold=True,
            font_name="Roboto",  # kivy default font renders latin text more reliably than GoNotoKurrent at small sizes
            color=get_color_from_hex("#FFFFFF"),
        )
        self.translate_btn.bind(on_release=lambda instance: self.translate_text(0))

        #  Mic button - listens via the microphone and fills the input box 
        self.mic_btn = HoverButton(
            text="Speak",
            base_hex="#43A047",
            hover_hex="#388E3C",
            size_hint=(None, None),
            width=110,
            height=46,
            font_size=17,
            bold=True,
            font_name="Roboto",
            color=get_color_from_hex("#FFFFFF"),
        )
        self.mic_btn.bind(on_press=self.start_listening, on_release=self.stop_listening)
        self._is_listening = False   # true while the button is held down and we're actively recording
        self._audio_frames = []      # raw audio chunks collected while held

        self.listen_btn = HoverButton(
            text="Listen",
            base_hex="#8E24AA",
            hover_hex="#7B1FA2",
            size_hint=(None, None),
            width=110,
            height=46,
            font_size=17,
            bold=True,
            font_name="Roboto",
            color=get_color_from_hex("#FFFFFF"),
        )
        self.listen_btn.bind(on_release=self.play_translation)
        self._is_speaking = False   # true while audio is being generated, guards against double-taps
        self._current_audio_path = None   # tracks the last generated mp3 so it can be deleted once replaced

        self.clear_btn = HoverButton(
            text="Clear",
            base_hex="#757575",
            hover_hex="#616161",
            size_hint=(None, None),
            width=90,
            height=46,
            font_size=16,
            bold=True,
            font_name="Roboto",
            color=get_color_from_hex("#FFFFFF"),
        )
        self.clear_btn.bind(on_release=self.clear_input)

        # copy button - copies the TRANSLATED result to the clipboard
        self.copy_btn = HoverButton(
            text="Copy",
            base_hex="#00897B",
            hover_hex="#00796B",
            size_hint=(None, None),
            width=90,
            height=46,
            font_size=16,
            bold=True,
            font_name="Roboto",
            color=get_color_from_hex("#FFFFFF"),
        )
        self.copy_btn.bind(on_release=self.copy_translation)

        action_row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=46, spacing=8)
        action_row.add_widget(self.clear_btn)
        action_row.add_widget(self.translate_btn)
        action_row.add_widget(self.mic_btn)
        action_row.add_widget(self.listen_btn)
        action_row.add_widget(self.copy_btn)
        self.add_widget(action_row)
        self.status_label = Label(
            text="",
            font_size=13,
            font_name="Roboto",  # kivy default font renders latin text more reliably than GoNotoKurrent at small sizes
            size_hint=(1, None),
            height=20,
            color=get_color_from_hex("#6B7280"),
        )
        self.add_widget(self.status_label)
        self._translate_event = None

    def _on_source_search_change(self, name):
        self.source_bar.select(name, fire_callback=False)
        if self.input_box.text.strip():
            self.schedule_translate()

    def _on_target_search_change(self, name):
        self.target_bar.select(name, fire_callback=False)
        if self.input_box.text.strip():
            self.schedule_translate()

    def _on_source_bar_change(self, name):

        self.source_search.set_selection(name)
        if self.input_box.text.strip():
            self.schedule_translate()

    def _on_target_bar_change(self, name):
        self.target_search.set_selection(name)
        if self.input_box.text.strip():
            self.schedule_translate()

    def update_result_text_size(self, instance, size):

        self.result_label.text_size = (size[0], None)

    def swap_languages(self, instance):
        # can't meaningfully swap FROM "auto-detect" since there's nothing concrete to swap to
        if self.source_bar.selected_text == "Detect language automatically":
            return
        src = self.source_bar.selected_text
        tgt = self.target_bar.selected_text
        self.source_bar.select(tgt)
        self.target_bar.select(src)
        self.source_search.set_selection(tgt)
        self.target_search.set_selection(src)
        # re-trigger translation with the swapped languages if there's already text typed
        if self.input_box.text.strip():
            self.schedule_translate()

    def on_input_text_change(self, instance, value):
        self.schedule_translate()

    def schedule_translate(self):
        if self._translate_event:
            self._translate_event.cancel()

        if self.input_box.text.strip() == "":
            self.result_label.text = "Translation"
            self.result_label.color = get_color_from_hex("#9CA3AF")
            self.status_label.text = ""
            return

        self.status_label.text = "Translating..."
        self._translate_event = Clock.schedule_once(self.translate_text, 0.6)

    def start_listening(self, instance):

        if self._is_listening:
            return
        self._is_listening = True
        self._audio_frames = []
        self.mic_btn.text = "Listening..."
        self.mic_btn.set_colors("#EF5350", "#E53935")   # turns red while held, like a recording indicator
        self.status_label.text = "Listening... release to stop"

        threading.Thread(target=self._record_while_held, daemon=True).start()

    def stop_listening(self, instance):
        if not self._is_listening:
            return
        self._is_listening = False   # the recording loop below checks this flag every chunk and exits
        self.mic_btn.text = "Speak"
        self.mic_btn.set_colors("#43A047", "#388E3C")
        self.status_label.text = "Processing..."

    def _record_while_held(self):
        RATE = 16000          # samples per second - good balance of quality vs. file size for speech
        CHUNK = 1024           # frames read per pass, small enough to check the stop flag frequently

        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                             input=True, frames_per_buffer=CHUNK)
        except Exception as e:
            p.terminate()
            error_msg = f"Mic error: {e}"
            Clock.schedule_once(lambda dt: self._on_listen_error(error_msg))
            self._is_listening = False
            return

        while self._is_listening:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                self._audio_frames.append(data)
            except Exception:
                break

        stream.stop_stream()
        stream.close()
        p.terminate()

        if not self._audio_frames:
            Clock.schedule_once(lambda dt: self._on_listen_error("Didn't catch any audio - hold the button while you speak"))
            return

        audio_data = sr.AudioData(b"".join(self._audio_frames), RATE, 2)

        source_name = self.source_bar.selected_text
        locale = MIC_LOCALE_MAP.get(source_name, "en-US")
        recognizer = sr.Recognizer()

        try:
            text = recognizer.recognize_google(audio_data, language=locale)
        except sr.UnknownValueError:
            Clock.schedule_once(lambda dt: self._on_listen_error("Couldn't make out what you said"))
            return
        except sr.RequestError as e:
            error_msg = f"Speech service error: {e}"
            Clock.schedule_once(lambda dt: self._on_listen_error(error_msg))
            return

        Clock.schedule_once(lambda dt: self._on_listen_success(text))

    def _on_listen_success(self, text):
        self.status_label.text = ""
        text = format_speech_text(text)
        self.input_box.text = text

    def _on_listen_error(self, message):
        self._is_listening = False
        self.mic_btn.text = "Speak"
        self.mic_btn.set_colors("#43A047", "#388E3C")
        self.status_label.text = message

    def clear_input(self, instance):
        self.input_box.text = ""
        self.result_label.text = "Translation"
        self.result_label.color = get_color_from_hex("#9CA3AF")   # back to the placeholder's grey
        self.status_label.text = ""

    def copy_translation(self, instance):
        result_text = self.result_label.text.strip()
        if not result_text or result_text == "Translation":
            self.status_label.text = "Translate something first"
            return

        Clipboard.copy(result_text)
        self.status_label.text = "Copied!"
        Clock.schedule_once(lambda dt: self._clear_status_if_unchanged("Copied!"), 2)

    def _clear_status_if_unchanged(self, expected_text):

        if self.status_label.text == expected_text:
            self.status_label.text = ""

    def play_translation(self, instance):
        # ignore taps while audio is still being generated from a previous tap
        if self._is_speaking:
            return

        result_text = self.result_label.text.strip()

        if not result_text or result_text == "Translation":
            self.status_label.text = "Translate something first"
            return

        self._is_speaking = True
        self.listen_btn.text = "Loading..."
        self.status_label.text = "Generating audio..."

        threading.Thread(target=self._generate_and_play_audio, args=(result_text,), daemon=True).start()

    def _generate_and_play_audio(self, text):
        target_name = self.target_bar.selected_text
        dest_code = code_for.get(target_name, "en-GB")

        gtts_code = resolve_gtts_lang_code(dest_code)
        if gtts_code is None:
            error_msg = f"No voice available for {target_name}"
            Clock.schedule_once(lambda dt: self._on_audio_error(error_msg))
            return

        try:
            tts = gTTS(text=text, lang=gtts_code)
            tmp_path = os.path.join(tempfile.gettempdir(), f"translation_{uuid.uuid4().hex}.mp3")
            tts.save(tmp_path)
        except Exception as e:
            traceback.print_exc()   # full details go to the terminal
            error_msg = f"Couldn't generate audio: {e}"
            Clock.schedule_once(lambda dt: self._on_audio_error(error_msg))
            return

        Clock.schedule_once(lambda dt: self._on_audio_ready(tmp_path))

    def _on_audio_ready(self, path):
        self._is_speaking = False
        self.listen_btn.text = "Listen"
        self.status_label.text = ""

        if self._current_audio_path and self._current_audio_path != path:
            try:
                os.remove(self._current_audio_path)
            except Exception:
                pass   # might still be playing/locked - not worth failing over
        self._current_audio_path = path

        sound = SoundLoader.load(path)
        if sound:
            sound.play()
        else:

            print(f"Kivy's SoundLoader couldn't load {path} - falling back to the OS's default player")
            self._play_with_os_fallback(path)

    def _play_with_os_fallback(self, path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["afplay", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            traceback.print_exc()
            self.status_label.text = f"Couldn't play audio: {e}"

    def _on_audio_error(self, message):
        self._is_speaking = False
        self.listen_btn.text = "Listen"
        self.status_label.text = message

    def translate_text(self, dt):
        user_text = self.input_box.text

        if user_text.strip() == "":
            return

        source_name = self.source_bar.selected_text
        target_name = self.target_bar.selected_text

        if source_name == "Detect language automatically":
            src_code = "auto"
        else:
            src_code = code_for[source_name]

        dest_code = code_for[target_name]

        self.status_label.text = "Translating..."

        threading.Thread(
            target=self._run_translation,
            args=(user_text, src_code, dest_code, source_name),
            daemon=True,
        ).start()

    def _run_translation(self, user_text, src_code, dest_code, source_name):

        protected_text, placeholders = protect_proper_nouns(user_text)

        corrected_text, fixes_applied = check_and_fix_grammar(protected_text, source_name)

        print(f"[translate] original text:  {user_text!r}")
        print(f"[translate] after name protection: {protected_text!r} (placeholders: {placeholders})")
        print(f"[translate] after grammar check ({fixes_applied} fix(es)): {corrected_text!r}")
        print(f"[translate] src={src_code} dest={dest_code}")

        try:
            raw_translated = GoogleTranslator(source=src_code, target=dest_code).translate(corrected_text)
        except Exception as e:
            traceback.print_exc()   # full details go to the terminal - status_label only has room for a short message
            error_msg = "Error: " + str(e)
            Clock.schedule_once(lambda dt: self._on_translate_error(error_msg))
            return

        translated_text = restore_proper_nouns(raw_translated, placeholders, dest_code=dest_code)

        print(f"[translate] Google Translate returned (before name restore): {raw_translated!r}")
        print(f"[translate] final result (after name restore): {translated_text!r}")

        Clock.schedule_once(lambda dt: self._on_translate_success(translated_text, fixes_applied))

    def _on_translate_success(self, translated_text, fixes_applied=0):
        self.result_label.text = translated_text
        self.result_label.color = get_color_from_hex("#111827")   # dark text now that it's a real result

        if fixes_applied > 0:
            note = "Fixed wording before translating" if fixes_applied == 1 else f"Fixed {fixes_applied} wording issues before translating"
            self.status_label.text = note
            Clock.schedule_once(lambda dt: self._clear_status_if_unchanged(note), 3)
        else:
            self.status_label.text = ""

    def _on_translate_error(self, message):
        self.status_label.text = message