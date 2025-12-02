import json

from words import process_words
from sentences import process_sentences


def main():
    characters = {}
    words = {}
    sentences = {}

    # Import word and character data
    try:
        with open("../export/json/words.json", "r", encoding="utf-8") as words_json:
            words = json.load(words_json)
        with open("../export/json/characters.json", "r", encoding="utf-8") as characters_json:
            characters = json.load(characters_json)
    except:
        process_words(words, characters, export=True)

    # Import sentence data
    try:
        with open("../export/json/sentences.json", "r", encoding="utf-8") as sentences_json:
            sentences = json.load(sentences_json)
    except:
        process_sentences(sentences, words, characters, export=True)


# Run program
if __name__ == "__main__":
    main()