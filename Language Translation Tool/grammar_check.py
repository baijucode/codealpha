import requests

LANGUAGETOOL_API_URL = "https://api.languagetool.org/v2/check"

GRAMMAR_CHECK_LANGS = {
    "english": "en-US",
    "french": "fr",
    "spanish": "es",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "russian": "ru",
}


def check_and_fix_grammar(text, source_name):

    lt_code = GRAMMAR_CHECK_LANGS.get(source_name)
    if not lt_code:
        return text, 0

    try:
        response = requests.post(
            LANGUAGETOOL_API_URL,
            data={"text": text, "language": lt_code},
            timeout=8,
        )
        response.raise_for_status()
        result = response.json()
    except Exception:
        return text, 0

    matches = result.get("matches", [])
    if not matches:
        return text, 0

    corrected = text
    fixes_applied = 0
    for match in sorted(matches, key=lambda m: m["offset"], reverse=True):
        replacements = match.get("replacements", [])
        if not replacements:
            continue
        best_suggestion = replacements[0]["value"]
        start = match["offset"]
        end = start + match["length"]
        corrected = corrected[:start] + best_suggestion + corrected[end:]
        fixes_applied += 1

    return corrected, fixes_applied