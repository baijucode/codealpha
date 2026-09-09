import os
from kivy.core.text import LabelBase

# "GoNotoKurrent" is a community font that MERGES Google's Noto fonts for all
# the world's current, widely-used scripts into a single .ttf file (~15MB).
# This covers Latin, Cyrillic, Greek, Devanagari (Hindi/Nepali/Marathi),
# Arabic, Thai, Chinese, Japanese, Korean, and dozens more - all in one file.
# So instead of juggling multiple fonts and switching between them, we just
# use this one font everywhere.
# Source: https://github.com/satbyy/go-noto-universal

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
UNIVERSAL_FONT_PATH = os.path.join(FONTS_DIR, "GoNotoKurrent-Regular.ttf")

# also check the project root, in case the font file wasn't put in a "fonts" subfolder
FALLBACK_FONT_PATH = os.path.join(os.path.dirname(__file__), "GoNotoKurrent-Regular.ttf")

if os.path.exists(UNIVERSAL_FONT_PATH):
    LabelBase.register(name="UniversalFont", fn_regular=UNIVERSAL_FONT_PATH)
    APP_FONT = "UniversalFont"
elif os.path.exists(FALLBACK_FONT_PATH):
    # found it sitting in the project root instead of inside "fonts/" - use it anyway
    LabelBase.register(name="UniversalFont", fn_regular=FALLBACK_FONT_PATH)
    APP_FONT = "UniversalFont"
    print(f"NOTE: found font at {FALLBACK_FONT_PATH} instead of the expected fonts/ folder - using it anyway.")
else:
    # fallback to kivy's built-in default font if the file is missing.
    # NOTE: font_name can't be None in kivy (it crashes), so we must give it
    # a real font name string here - "Roboto" is kivy's built-in default.
    APP_FONT = "Roboto"
    print(f"WARNING: Font file not found at {UNIVERSAL_FONT_PATH} or {FALLBACK_FONT_PATH}")
    print("Non-Latin scripts (Nepali, Arabic, Chinese, etc) won't display correctly.")
