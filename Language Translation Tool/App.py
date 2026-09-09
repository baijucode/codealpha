import streamlit as st                     # streamlit = the library that builds the web UI
from googletrans import Translator, LANGUAGES   # Translator = does the actual translating, LANGUAGES = dict of all language codes/names
from gtts import gTTS                       # gTTS = converts text to speech (audio)
import io                                    # io = lets us handle the audio data in memory (no need to save a file)

# this sets the browser tab title, icon, and page width
st.set_page_config(page_title="Language Translator", page_icon="🌐", layout="centered")

st.title("🌐 Language Translation Tool")       # big heading at top of page
st.write("A simple translator I built using Python + Streamlit + Google Translate")  # subtext under heading

# LANGUAGES is a dict like {'en': 'english', 'fr': 'french', ...}
# .values() grabs just the language names, sorted() puts them alphabetically for the dropdown
lang_list = sorted(LANGUAGES.values())

# this flips the dict around so i can go from name -> code
# e.g. code_for["french"] gives me "fr"
code_for = {v: k for k, v in LANGUAGES.items()}

# splits the page into two side-by-side columns
col1, col2 = st.columns(2)

with col1:
    # dropdown for source language, with "Detect language" as an extra option at the top
    src_lang = st.selectbox("From", ["Detect language"] + lang_list)

with col2:
    # trying to default the target dropdown to "french" so it's not empty on first load
    if "french" in lang_list:
        default_idx = lang_list.index("french")   # find where "french" sits in the list
    else:
        default_idx = 0                            # fallback just in case "french" isn't in the list

    tgt_lang = st.selectbox("To", lang_list, index=default_idx)   # dropdown for target language

# big text box where the user types what they want translated
text = st.text_area("Enter your text here", height=150)

# the translate button - btn becomes True only when clicked
btn = st.button("Translate", type="primary")

# session_state keeps data around even after the page reruns (streamlit reruns the whole script on every click)
# so without this, the translated text would disappear the moment you click anything else
if "output" not in st.session_state:
    st.session_state.output = ""    # start with empty output the first time the app loads

# this whole block only runs when the Translate button is clicked
if btn:
    if text.strip() == "":              # .strip() removes spaces, so this checks if the box is actually empty
        st.warning("type something first lol")   # show a warning message, don't try to translate nothing
    else:
        try:                              # try/except so the app doesn't crash if something goes wrong (like no internet)
            t = Translator()               # create a translator object - this is what actually talks to Google Translate

            # figure out what source language code to use
            if src_lang == "Detect language":
                s_code = "auto"             # "auto" tells googletrans to figure out the language itself
            else:
                s_code = code_for[src_lang]  # otherwise look up the code for whatever they picked

            d_code = code_for[tgt_lang]      # look up the code for the target language they picked

            res = t.translate(text, src=s_code, dest=d_code)   # this is the actual translation call - sends text off and gets result back
            st.session_state.output = res.text                 # save the translated text so it survives the page rerun

            # if we used auto-detect, tell the user what language it guessed
            if s_code == "auto":
                st.info(f"Detected language: {LANGUAGES.get(res.src, res.src)}")  # res.src = the code it detected, look up its full name

        except Exception as e:                                  # e = whatever error happened
            st.error("Something went wrong, translation didn't work: " + str(e))   # show the error on screen instead of crashing

# only show the results section if we actually have a translation saved
if st.session_state.output != "":
    st.subheader("Result")                                       # smaller heading for the results section
    st.text_area("Translated text", value=st.session_state.output, height=150)   # show the translated text in a box

    # st.code() shows text in a code-style box, which happens to have a built-in copy icon
    # not a "real" copy button, just reusing this widget because it's convenient
    st.code(st.session_state.output)

    if st.button("Play audio 🔊"):                                # button to trigger text-to-speech
        try:
            tts = gTTS(text=st.session_state.output, lang=code_for[tgt_lang])  # create the speech audio from the translated text
            buf = io.BytesIO()             # make an empty in-memory file to hold the audio bytes
            tts.write_to_fp(buf)           # write the generated audio into that in-memory file
            buf.seek(0)                    # rewind to the start of the buffer so it can be read from the beginning
            st.audio(buf, format="audio/mp3")   # show an audio player on the page with the generated speech
        except Exception as e:
            st.error("couldn't generate audio: " + str(e))        # show error if TTS fails (e.g. bad language code)

st.write("---")                                                    # horizontal divider line
st.caption("Made for CodeAlpha AI Internship - Task 1 (Language Translation Tool)")   # small footer text