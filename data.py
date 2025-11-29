# Process raw data files
# ---
# Data sources:
# Word list: https://github.com/drkameleon/complete-hsk-vocabulary
# Sentence list: https://tatoeba.org/en/downloads

import chinese_converter
import csv
import json
import re


def main():
    words = []
    process_words(words)

    sentences = []
    process_sentences(words, sentences)

    cloze = []
    match_cloze(words, sentences, cloze)


# Process word data
def process_words(words):

    # Encoded values for parts of speech
    POS = {"a":	"adjective",
           "b": "non-predicate adjective",
           "c":	"conjunction",
           "d":	"adverb",
           "e":	"interjection",
           "f": "directional locality",
           "g": "morpheme",
           "h": "prefix",
           "i": "idiom",
           "j": "abbreviation",
           "k":	"suffix",
           "l": "fixed expressions",
           "m": "numeral",
           "n": "noun",
           "o":	"onomatopoeia",
           "p":	"preposition",
           "q":	"classifier",
           "r":	"pronoun",
           "s": "space word",
           "t": "time word",
           "u": "auxiliary",
           "v": "verb",
           "w": "symbol and non-sentential punctuation",
           "x": "unclassified",
           "y": "modal particle",
           "z":	"descriptive",
           }

    # Read full word data from JSON file
    with open("raw/hsk-vocabulary-complete.json", "r") as words_json:
        words_full = json.load(words_json)

        # Extract needed fields
        for word in words_full:
            words.append(
                {
                    "word": word["simplified"],
                    "level": int(re.sub(r"[a-zA-Z\+\-]", "", word["level"][0])),
                    "difficulty": int(word["frequency"]),
                    "pos": ", ".join([POS[key.lower()[0]] for key in word["pos"]]),
                    "pinyin": " | ".join(form["transcriptions"]["pinyin"] for form in word["forms"]),
                    "definitions": " | ".join(" | ".join(form["meanings"]) for form in word["forms"])
                }
            )
        # Generate word id
        for i in range(len(words)):
            words[i]["id"] = i + 1

    # Write cleaned up word data to new CSV file
    with open("words.csv", "w") as words_csv:
        writer = csv.DictWriter(words_csv, ["id", "word", "level",
                                "difficulty", "pos", "pinyin", "definitions"])
        writer.writeheader()
        writer.writerows(words)


# Process sentences data
def process_sentences(words, sentences):

    # Create an OpenCC converter object
    # Read raw sentence data from TSV file
    with open("raw/cmn_sentences.tsv", "r") as sentences_tsv:
        reader = csv.reader(sentences_tsv, delimiter="\t")
        for row in reader:
            id = int(row[0])
            sentence = row[2]

            # Reject sentences that contain alphabet letters or aren't complete
            if contains_letters(sentence) or not sentence.endswith(("。", ".", "！", "!", "？", "?", "…", "”")):
                continue

            # Convert sentence from traditional to simplified Chinese
            # https://pypi.org/project/chinese-converter/
            sentence = chinese_converter.to_simplified(sentence)

            # Determine difficulty score
            difficulty = compute_difficulty(sentence, words)
            sentences.append({"id": id, "sentence": sentence, "difficulty": difficulty})

    # Write cleaned up data to new CSV file
    with open("sentences.csv", "w") as sentences_csv:
        writer = csv.DictWriter(sentences_csv, ["id", "sentence", "difficulty"])
        writer.writeheader()
        writer.writerows(sentences)


# Find matches between words and sentences
def match_cloze(words, sentences, cloze):

    # Find sentences containing each word
    for word in words:
        for sentence in sentences:
            if word["word"] in sentence["sentence"]:
                cloze.append({"word_id": word["id"], "sentence_id": sentence["id"]})

    # Write match data to CSV file
    with open("cloze.csv", "w") as cloze_csv:
        writer = csv.DictWriter(cloze_csv, ["word_id", "sentence_id"])
        writer.writeheader()
        writer.writerows(cloze)


# Check if string contains Latin alphabet letters
def contains_letters(string):
    match = re.search(r"[a-zA-Z]", string)
    if match:
        return True
    return False


# Determine the frequency score of a sentence
def compute_difficulty(sentence, words):

    # Default value for words not present in word list
    MAX_DIFFICULTY = 1000000

    # Remove punctuation and numbers
    sentence = re.sub(r"[0-9。\.，、,：:；;？\?！\!“ ”\"「 」《》〈〉…·\(\)]", "", sentence)
    difficulty = 0
    for word in words:
        if word["word"] in sentence:
            sentence = sentence.replace(word["word"], "")
            if word["difficulty"] > difficulty:
                difficulty = word["difficulty"]

    # If there are still words remaining, set difficulty to max value
    if sentence:
        difficulty = MAX_DIFFICULTY * len(sentence)

    return difficulty


# Run program
main()
