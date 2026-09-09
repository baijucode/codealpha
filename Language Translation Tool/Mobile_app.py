#App entry point. All the actual UI, translation, speech, and audio logic lives in the other modules alongside this file - this is just the bootstrap
from kivy.app import App
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

from translator_layout import TranslatorLayout
from audio_utils import cleanup_old_audio_files

Window.clearcolor = get_color_from_hex("#F0F2F5")
Window.size = (950, 650)   


class TranslatorApp(App):
    def build(self):
        self.title = "Language Translator"
        cleanup_old_audio_files()
        return TranslatorLayout()


if __name__ == "__main__":
    TranslatorApp().run()
