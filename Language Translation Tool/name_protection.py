import re

PLACEHOLDER_TEMPLATE = "⟦{index}⟧"
PLACEHOLDER_PATTERN = re.compile(r"⟦(\d+)⟧")

DEVANAGARI_TARGET_CODES = {"ne", "hi"}

_transliterator = None


def _get_transliterator():
    global _transliterator
    if _transliterator is None:
        from hindi_xlit import HindiTransliterator
        _transliterator = HindiTransliterator()
    return _transliterator


def protect_proper_nouns(text):
    words = text.split()
    placeholders = {}
    protected_words = list(words)

    for i, word in enumerate(words):
        if i == 0:
            continue

        stripped = word.strip(".,!?;:\"'")
        if len(stripped) > 1 and stripped[0].isupper() and not stripped.isupper():
            token = PLACEHOLDER_TEMPLATE.format(index=len(placeholders))
            placeholders[token] = word
            protected_words[i] = token

    protected_text = " ".join(protected_words)
    return protected_text, placeholders


def restore_proper_nouns(text, placeholders, dest_code=None):
    def _replace(match):
        token = f"⟦{match.group(1)}⟧"
        original_word = placeholders.get(token)
        if original_word is None:
            return match.group(0)

        if dest_code in DEVANAGARI_TARGET_CODES:
            stripped = original_word.rstrip(".,!?;:")
            trailing_punct = original_word[len(stripped):]
            try:
                transliterator = _get_transliterator()
                candidates = transliterator.transliterate(stripped)
                if candidates:
                    return candidates[0] + trailing_punct
            except Exception:
                pass

        return original_word

    restored = PLACEHOLDER_PATTERN.sub(_replace, text)
    restored = re.sub(r" {2,}", " ", restored)
    return restored