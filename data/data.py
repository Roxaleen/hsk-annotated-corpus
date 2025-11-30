# Process raw data files
# ---
# Data sources:
# Word list: https://github.com/drkameleon/complete-hsk-vocabulary
# Sentence list: https://tatoeba.org/en/downloads

import csv, json

from words import process_words
from sentences import process_sentences


characters = set()
words = {}
sentences = []

def main():
    # Import word data
    try:
        with open("../export/json/words.json", "r", encoding="utf-8") as words_json:
            words = json.load(words_json)
        characters = {character for word in words for character in set(word)}
    except:
        process_words(words, characters)

    # Import sentence data
    # process_sentences(sentences, characters)

    # cloze = []
    # match_cloze(words, sentences, cloze)


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


# # Determine the frequency score of a sentence
# def compute_difficulty(sentence, words):

#     # Default value for words not present in word list
#     MAX_DIFFICULTY = 1000000

#     # Remove punctuation and numbers
#     sentence = re.sub(r"[0-9。\.，、,：:；;？\?！\!“ ”\"「 」《》〈〉…·\(\)]", "", sentence)
#     difficulty = 0
#     for word in words:
#         if word["word"] in sentence:
#             sentence = sentence.replace(word["word"], "")
#             if word["difficulty"] > difficulty:
#                 difficulty = word["difficulty"]

#     # If there are still words remaining, set difficulty to max value
#     if sentence:
#         difficulty = MAX_DIFFICULTY * len(sentence)

#     return difficulty


# Run program
if __name__ == "__main__":
    main()