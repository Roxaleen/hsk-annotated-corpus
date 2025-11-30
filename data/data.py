import json

from words import process_words
from sentences import process_sentences


def main():
    characters = set()
    words = {}
    sentences = set()

    # Import word data
    try:
        with open("../export/json/words.json", "r", encoding="utf-8") as words_json:
            words = json.load(words_json)
        characters = {character for word in words for character in set(word)}
    except:
        process_words(words, characters)

    # Import sentence data
    process_sentences(sentences, characters)


# Run program
if __name__ == "__main__":
    main()