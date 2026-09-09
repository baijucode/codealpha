
from sklearn.feature_extraction.text import TfidfVectorizer  # text lai number (vector) ma convert garna
from sklearn.metrics.pairwise import cosine_similarity        # duita vector bich similarity nikalna

from preprocess import clean_text   # aghi banayeko cleaning function import garyo


class FAQMatcher:

    def __init__(self, faqs: list):

        self.faqs = faqs

        # sabai FAQ question haru lai clean garyo (preprocessing apply garyo)
        self.cleaned_questions = [clean_text(item["question"]) for item in self.faqs]

        # TfidfVectorizer object banayo - yesle chai text lai number
        # matrix ma convert garne kaam garcha
        self.vectorizer = TfidfVectorizer()

        # yaha nai "training" jasto huncha - sabai FAQ question haru
        # bata vocabulary banayera, tiniharu lai vector (number) ma convert garcha
        # fit_transform() = fit (vocabulary sikne) + transform (number ma badalne) dubai euta patak
        self.faq_vectors = self.vectorizer.fit_transform(self.cleaned_questions)

    def find_best_match(self, user_question: str, threshold: float = 0.3):
        """
        User ko question pathayo bhane, sabai bhanda best match huney
        FAQ ko answer (ra kati % similar thiyo) firta garcha.

        threshold = kati similarity vayo vane matra "valid match" manne.
        (0.3 vanda kam vayo vane, hami "sorry, bujhina" vanchau)
        """

        # step 1: user ko question pani same tarika le clean garne(training bela jasto formatमा nai huna paryo, natra compare garda garbage nikalcha)
        cleaned_input = clean_text(user_question)

        # step 2: user ko clean question lai pani number (vector) ma convert garne note: transform matra use garya, fit haina - kina ki vocabulary pahile nai FAQ bata banisakeko xa, naya vocabulary sikne haina
        user_vector = self.vectorizer.transform([cleaned_input])

        # step 3: user ko vector lai HAMRO sabai FAQ vector sanga compar garne - cosine_similarity le euta list of scores dincha (each FAQ sanga kati % similar xa vanera)
        similarity_scores = cosine_similarity(user_vector, self.faq_vectors)

        # step 4: sabai bhanda highest score bhayeko index (position) pattauune  .argmax() le list ma sabai bhanda thulo value kun index ma xa vanera dincha
        best_index = similarity_scores.argmax()

        # step 5: tyo best index ko actual score value nikalne
        best_score = similarity_scores[0][best_index]

        # step 6: score le threshold cross garyo vane, matching FAQ firta garne, natra "sorry bujhina" jasto response return garne
        if best_score >= threshold:
            matched_faq = self.faqs[best_index]
            return {
                "matched": True,
                "question": matched_faq["question"],
                "answer": matched_faq["answer"],
                "confidence": round(float(best_score) * 100, 2),  # % ma convert garyo
            }
        else:
            return {
                "matched": False,
                "question": None,
                "answer": "Sorry, I couldn't find a matching answer. Please contact support for more help.",
                "confidence": round(float(best_score) * 100, 2),
            }


# yo file direct chalayo bhane matra test garna ko lagi
if __name__ == "__main__":
    import json

    with open("data/faqs.json", "r", encoding="utf-8") as f:
        faqs_data = json.load(f)   # json file bata FAQ list load garyo

    matcher = FAQMatcher(faqs_data)   # class ko object banayo (vectors banaune process yehi bela huncha)

    test_question = "how can i get my money back"
    result = matcher.find_best_match(test_question)
    print(result)
