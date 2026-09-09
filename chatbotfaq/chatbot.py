import json                     # json file (faqs.json) read garna ko lagi
from match import FAQMatcher    # aghi banayeko matching class import garyo


def load_faqs(path: str = "data/faqs.json") -> list:

    with open(path, "r", encoding="utf-8") as f:   # "with" le automatic file close garidincha, kaam sakepachi
        return json.load(f)


def run_chatbot():

    print("=" * 50)
    print(" FAQ Chatbot - malai sodhnus, ma answer dinxu!")
    print(" (exit garna 'quit' ya 'exit' type garnus)")
    print("=" * 50)

    # step 1: FAQ data load garne
    faqs = load_faqs()

    # step 2: matcher taiyar garne (vectorizer + vectors sabai yehi banxa)
    matcher = FAQMatcher(faqs)

    # step 3: infinite loop - user le "quit" nabhaneko samma chaltai rahancha
    while True:
        # user bata input linne
        user_input = input("\nYou: ").strip()   # .strip() le extra space hataucha

        # khali message aayo bhane skip garne (kehi nagareko)
        if not user_input:
            continue

        # user le exit garna khojyo bhane loop bata bahira niskane
        if user_input.lower() in ("quit", "exit", "bye"):
            print("Bot: Dhanyabad! Feri bhetaula. 👋")
            break

        # step 4: best matching FAQ khojne
        result = matcher.find_best_match(user_input)

        # step 5: result dekhauune
        print(f"Bot: {result['answer']}")
        # confidence pani dekhauxa - yesle chai user lai bujhauxa
        # kati "sure" xa chatbot answer ma (debugging ko lagi ni useful)
        print(f"     (confidence: {result['confidence']}%)")


# yo standard python pattern ho - yo file directly run garyo bhane
# matra run_chatbot() chalcha, aru file bata import garda chaldaina
if __name__ == "__main__":
    run_chatbot()
