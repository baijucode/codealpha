import re                              # yesle chai text bata punctuation/number jasta cha haru clean garna helps garcha (regex use garera)
import nltk                            # NLTK bhaneko Natural Language Toolkit ho — text processing ko lagi library
from nltk.corpus import stopwords      # yesle chai stopwords ko list dincha (is, the, a, an jasta words)
from nltk.stem import WordNetLemmatizer  # yesle chai word lai euta "root form" ma lyaunxa (running -> run)
from nltk.tokenize import word_tokenize  # yesle chai sentence lai individual word haru ma todcha (tokenize garcha)

def download_nltk_data():
    """Yesle chai NLTK ko required data haru download garxa (first time matra)."""
    required = [
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/stopwords", "stopwords"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),
    ]
    for path, name in required:
        try:
            nltk.data.find(path)        # check garcha yo data already xa ki nai
        except LookupError:
            nltk.download(name, quiet=True)   # xaina bhane silently download garcha


download_nltk_data()   # file import hune bittikai euta patak download check garxa

# yesle chai English stopwords ko set banauxa — set() use garya kina bhane
# set ma "in" check garna list bhanda fast huncha
STOP_WORDS = set(stopwords.words("english"))

# lemmatizer object banayo — yo reuse garna ko lagi euta patak matra banaune
lemmatizer = WordNetLemmatizer()


def clean_text(text: str) -> str:
    """
    Yo main function ho — ek line ma text pathayo bhane, clean vaera
    firta aauxa.

    Step by step yesle yo garxa:
    1. Sabai lowercase garxa           -> "How Are You" => "how are you"
    2. Punctuation/number hataauxa      -> "hello?!" => "hello"
    3. Tokenize garxa (word haru ma todcha)
    4. Stopwords hataauxa               -> "is", "the", "a" jasta
    5. Lemmatize garxa                  -> "running" => "run"
    6. Sabai word haru joडेra firta clean string dincha
    """

    # step 1: lowercase - kina garne vaneko "Return" ra "return" lai
    # computer le different word thandaina vanera
    text = text.lower()

    # step 2: punctuation ra number hataune - re.sub le pattern match
    # vayeko jaga ma replace garcha. [^a-z\s] bhaneko "a-z ra space
    # bahek aru sabai" - tyo sabai lai empty string ("") le replace garcha
    text = re.sub(r"[^a-z\s]", "", text)

    # step 3: tokenize - "how do i reset password" -> ["how","do","i","reset","password"]
    tokens = word_tokenize(text)

    # step 4 + 5: stopwords hataune ra lemmatize garne - euta line ma dubai
    # (list comprehension) - loop chalayera each word check garcha,
    # stopword nabhaye lemmatize garera naya list ma rakhcha
    cleaned_tokens = [
        lemmatizer.lemmatize(word) for word in tokens if word not in STOP_WORDS
    ]

    # step 6: sabai token haru back joडेra euta string banauxa (space le separate garera)
    return " ".join(cleaned_tokens)


# yo part le chai yo file lai direct chalayo bhane matra test garcha,
# aru file bata import garda yo run hudaina
if __name__ == "__main__":
    sample = "How do I RESET my Password?!"
    print("Original :", sample)
    print("Cleaned  :", clean_text(sample))
