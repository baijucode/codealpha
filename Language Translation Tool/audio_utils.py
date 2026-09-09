import os
import glob
import tempfile


def cleanup_old_audio_files():
    #clean leftovers caused by crash or force closed
 
    pattern = os.path.join(tempfile.gettempdir(), "translation_*.mp3")
    for path in glob.glob(pattern):
        try:
            os.remove(path)
        except Exception:
            pass   # file might be in use by another running instance - not worth failing over


def format_speech_text(text):#capital first letter adds periods . ! or ? at end of sentece

    text = text.strip()
    if not text:
        return text

    text = text[0].upper() + text[1:]

    if text[-1] not in ".!?":
        text += "."

    return text
