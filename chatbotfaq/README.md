# FAQ Chatbot (Retrieval-based, TF-IDF + Cosine Similarity)

Yo project le task 2 ko requirement pura garcha:
- FAQ collect garyo (data/faqs.json)
- NLTK use garera text preprocess garyo (preprocess.py)
- Cosine similarity use garera best matching FAQ khojyo (match.py)
- Matching answer display garyo (chatbot.py — terminal, ra app.py — web UI)

---

## 📁 Folder Structure (Tree Diagram)

```
faq_chatbot/
│
├── data/
│   └── faqs.json          # sabai FAQ question-answer haru yehi ma huncha
│
├── preprocess.py           # text clean garne (tokenize, stopwords hataune, lemmatize)
├── match.py                 # TF-IDF + cosine similarity use garera best FAQ khojne
├── chatbot.py                # MAIN file - terminal ma chat garna ko lagi
├── app.py                    # OPTIONAL - Streamlit use garera web chat UI
├── requirements.txt          # kun kun library install garne, tyo list
└── README.md                 # yo file - instructions
```

**Kina yesari arrange garya:**
- `data/` bhitra matra data raख्यौं (code bata data alag rakhnu ramro
  practice ho, pachi FAQ update garna easy huncha, code touch garnu pardaina).
- `preprocess.py` ra `match.py` chai alag-alag "logic" file haru ho —
  euta le text clean garcha, arkole matching garcha. Yesari alag-alag
  garda code padhna ra debug garna easy huncha.
- `chatbot.py` le tiniharu lai import garera use garcha (terminal version).
- `app.py` le pani ustai `match.py` use garcha, tara web UI dinxa.

---

## ⚙️ Kun kun install garne (Setup)

### Step 1: Python install xa ki check garnus
Terminal ma yo chalaunus:
```bash
python --version
```
(Python 3.8 ya tyo bhanda maathi vaye huncha)

### Step 2: Project folder ma janus
```bash
cd faq_chatbot
```

### Step 3: (Optional tara recommended) Virtual environment banaunus
Yesle chai yo project ko library haru, computer ko aru project sanga
mix nahos vanera alag rakhcha:
```bash
python -m venv venv

# Windows ma activate garna:
venv\Scripts\activate

# Mac/Linux ma activate garna:
source venv/bin/activate
```

### Step 4: Required library haru install garnus
```bash
pip install -r requirements.txt
```
Yesle yo sabai install garcha:
- **nltk** → text preprocessing (tokenize, stopwords, lemmatize) ko lagi
- **scikit-learn** → TF-IDF vectorizer ra cosine similarity ko lagi
- **streamlit** → optional web chat UI ko lagi

(First run ma `preprocess.py` le automatic NLTK ko data — punkt,
stopwords, wordnet — download garcha. Internet connection chahincha.)

---

## ▶️ Kasari Chalaune (How to Run)

### Option A: Terminal chatbot
```bash
python chatbot.py
```
Terminal ma nai question type garera answer herna milxa. `quit` type
garda bot band huncha.

### Option B: Web chat UI (optional part)
```bash
streamlit run app.py
```
Yesle browser ma automatic euta page kholcha jaha chat box dekhincha —
tyaha type garera question sodhna milxa.

---

## 🧠 Yo chatbot le internally kasari kaam garcha (short summary)

1. **FAQ load** → `data/faqs.json` bata sabai question-answer haru load huncha.
2. **Preprocessing** → sabai FAQ question ra user ko question lai
   lowercase, punctuation-free, stopword-free, lemmatized form ma
   convert garincha (`preprocess.py`).
3. **Vectorization** → clean text lai TF-IDF le number (vector) ma
   convert garincha.
4. **Similarity check** → user ko question vector lai sabai FAQ vector
   sanga cosine similarity le compare garincha — jun FAQ sanga score
   sabai bhanda high aaucha, tyo "best match" huncha.
5. **Response** → best match ko answer user lai dekhaincha. Score
   threshold (0.3) bhanda kam vayo bhane, "sorry bujhina" jasto
   response dincha.

---

## ✏️ FAQ thapna/change garna

`data/faqs.json` bhitra naya object thapdiye pugcha:
```json
{
  "question": "your question here",
  "answer": "your answer here"
}
```
Code ma kehi change garnu pardaina — auto handle huncha.

---

## 📝 Note (Task requirement ma ke ke cover vayo)

| Requirement | Kaha cover vayo |
|---|---|
| Collect FAQs | `data/faqs.json` |
| Preprocess text (NLTK) | `preprocess.py` |
| Match using cosine similarity | `match.py` |
| Display best matching answer | `chatbot.py` |
| Optional: simple chat UI | `app.py` (Streamlit) |
