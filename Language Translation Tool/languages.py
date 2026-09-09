"""
Language code setup, shared by the translation, speech recognition, and
text-to-speech pieces of the app. Kept separate because every one of those
three services uses its OWN language code format, and translating between
them lives here.
"""

from deep_translator import GoogleTranslator   # Google's real NMT model - switched back from MyMemory after MyMemory's translation-memory lookup proved unreliable for Nepali specifically (returning unrelated stored matches for novel sentences). Worth knowing: this uses an unofficial, unsanctioned method of reaching Google's translate service rather than a licensed API - fine for personal/testing use, but a real consideration if this app is ever monetized/published commercially.
from gtts.lang import tts_langs as get_gtts_langs   # gTTS's own list of language codes it supports


# a small safety net so the app can still open if there's no internet at
# launch, or MyMemory happens to be down - without this, the app would
# crash before the window even appears
FALLBACK_LANGS = {
    "english": "en-GB", "nepali": "ne-NP", "hindi": "hi-IN",
    "french": "fr-FR", "spanish": "es-ES", "arabic": "ar-SA",
}

try:
    SUPPORTED_LANGS = GoogleTranslator().get_supported_languages(as_dict=True)   # {'english': 'en', 'french': 'fr', 'nepali': 'ne', ...}
except Exception:
    print("Couldn't fetch the language list from MyMemory (no internet at startup?) - using a small fallback list instead")
    SUPPORTED_LANGS = FALLBACK_LANGS


lang_list = sorted(SUPPORTED_LANGS.keys())
code_for = SUPPORTED_LANGS   # already {'english': 'en', 'french': 'fr', ...} - no inversion needed

# ---------------------------------------------------------------------------
# SPEECH RECOGNITION LOCALE MAP
# ---------------------------------------------------------------------------
# googletrans gives us short codes like "en", "fr", "ne" - but Google's speech
# recognition service wants full locale codes like "en-US", "fr-FR", "ne-NP".
# There's no automatic way to derive one from the other, so we hand-map the
# languages we actually expect people to use here. Anything not listed falls
# back to "en-US" (see MIC_LOCALE_MAP.get(...) below) - recognition will
# likely be poor for those languages until an entry is added for them here.
MIC_LOCALE_MAP = {
    "english": "en-US",
    "nepali": "ne-NP",
    "hindi": "hi-IN",
    "french": "fr-FR",
    "spanish": "es-ES",
    "arabic": "ar-SA",
    "german": "de-DE",
    "italian": "it-IT",
    "portuguese": "pt-PT",
    "russian": "ru-RU",
    "japanese": "ja-JP",
    "korean": "ko-KR",
    "chinese (simplified)": "zh-CN",
    "chinese (traditional)": "zh-TW",
}


def resolve_gtts_lang_code(mymemory_code):
    """
    MyMemory's language codes look like 'ne-NP', 'fr-FR', 'en-GB' (locale-style
    tags), but gTTS uses its own, mostly-plain code list ('ne', 'fr', 'en' -
    with a few exceptions like 'zh-CN', 'zh-TW', 'pt-PT' that DO keep the
    region). This checks the full tag first, then falls back to just the base
    language code, and returns None if gTTS has no voice for it at all.
    """
    try:
        supported = get_gtts_langs()
    except Exception:
        return None   # couldn't reach Google to fetch the list (needs internet)

    if mymemory_code in supported:
        return mymemory_code

    base_code = mymemory_code.split("-")[0]
    if base_code in supported:
        return base_code

    return None