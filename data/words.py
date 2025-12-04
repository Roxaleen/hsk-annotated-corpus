"""
Process word datasets.

HSK headwords and CC-CEDICT definitions: https://github.com/drkameleon/complete-hsk-vocabulary
Wiktionary dataset: https://kaikki.org/dictionary/Chinese/index.html
"""

import chinese_converter, csv, json, re

from pos import tag_definition_pos


# Standardized POS labels
POS_PKU = {
    "a": "adjective",
    "b": "adjective",
    "c": "conjunction",
    "d": "adverb",
    "e": "interjection",
    "f": "postposition",
    "g": "other",
    "h": "other",
    "i": "idiom",
    "j": "other",
    "k": "other",
    "l": "idiom",
    "m": "numeral",
    "n": "noun",
    "o": "other",
    "p": "preposition",
    "q": "classifier",
    "r": "pronoun",
    "s": "noun",
    "t": "noun",
    "u": "particle",
    "v": "verb",
    "w": "other",
    "x": "other",
    "y": "particle",
    "z": "adjective",
}
POS_WIKTIONARY = {
    "adj": "adjective",
    "adv": "adverb",
    "conj": "conjunction",
    "classifier": "classifier",
    "det": "pronoun",
    "intj": "interjection",
    "noun": "noun",
    "num": "numeral",
    "particle": "particle",
    "phrase": "idiom",
    "postp": "postposition",
    "prep": "preposition",
    "pron": "pronoun",
    "proverb": "idiom",
    "verb": "verb",
}


# Process word data
def process_words(words, characters, export=False):
    """
    Process raw word datasets.
    """
    # Load word set by drkameleon
    try:
        with open("tagged/words_drkameleon.json", "r", encoding="utf-8") as words_json:
            words_drkameleon = json.load(words_json)
    except:
        words_drkameleon = load_words_drkameleon(words, characters)
    
    # Load Wiktionary dataset
    try:
        with open("tagged/words_kaikki.json", "r", encoding="utf-8") as words_json:
            words_kaikki = json.load(words_json)
    except:
        words_kaikki = load_words_kaikki(words)
        with open("tagged/words_kaikki.json", "w", encoding="utf-8") as words_json:
            json.dump(words_kaikki, words_json, ensure_ascii=False)
    
    # Tag drkameleon definitions by part of speech
    words_drkameleon = tag_definition_pos(words_drkameleon, words_kaikki, POS_PKU)

    return

    with open("tagged/words_drkameleon.json", "w", encoding="utf-8") as words_json:
        json.dump(words_drkameleon, words_json, ensure_ascii=False)

    # Merge word datasets
    merge_word_sources(words, words_drkameleon, words_kaikki)

    # Export processed data
    if export:
        export_word_data(words, characters)


def load_words_drkameleon(words, characters, export_csv=False):
    """
    Load word set by drkameleon.

    Source: https://github.com/drkameleon/complete-hsk-vocabulary
    """
    words_drkameleon = {}

    # Read full word data from JSON file
    with open("raw/words/drkameleon_hsk-vocabulary-complete.json", "r", encoding="utf-8") as words_json:
        words_full = json.load(words_json)

        # Extract needed fields
        for word in words_full:
            word_level = int(re.sub(r"[a-zA-Z\+\-]", "", word["level"][0]))
            words[word["simplified"]] = {
                "level": word_level,
                "difficulty": int(word["frequency"]),
            }

            # Discard proper noun forms
            word_forms = [form for form in word["forms"] if (not re.search(r"[A-Z]", form["transcriptions"]["numeric"])) or len(word["forms"]) == 1]
            
            # Discard Taiwan-specific or trivial definitions
            word_meanings = [
                re.sub(r" \(Taiwan pr\. .*\)", "", meaning)
                for form in word_forms for meaning in form["meanings"] if not (
                    meaning.startswith(("Taiwan", "(Taiwan", "Beijing pr. ", "also ", "used in ", "(used ", "equivalent ", "(indicates ", "abbr. ", "see ", "Kangxi radical ")) or
                    any(substring in meaning for substring in ["(Tw)", "(Taiwan)", "variant of"])
                )
            ]
            if len(word_meanings) == 0:
                continue
            
            # Standardize parts of speech
            pos_set = {POS_PKU[key.lower()[0]] for key in word["pos"]}
            if len(pos_set) > 1:
                pos_set -= {"other"}
            
            # Compile word data
            word_data = {
                "pos": ", ".join(sorted(list(pos_set))),
                "pinyin": " | ".join({form["transcriptions"]["pinyin"] for form in word_forms}),
                "definitions": " | ".join(word_meanings),
                "source": "drkameleon"
            }            
            words_drkameleon[word["simplified"]] = [word_data]
            
            # Record character level
            for character in set(word["simplified"]):
                if character in characters:
                    characters[character] = min(characters[character], word_level)
                else:
                    characters[character] = words[word["simplified"]]["level"]
    
    # Export cleaned data to CSV
    if export_csv:
        with open("cleaned/words_drkameleon.csv", "w", encoding="utf-8") as words_csv:
            writer = csv.DictWriter(words_csv, ["word", "level", "difficulty", 
                                    "pos", "pinyin", "definitions"])
            writer.writeheader()
            for word in words_drkameleon:
                writer.writerow({
                    "word": word
                } | {
                    key : words[word][key] for key in ["level", "difficulty"]
                } | {
                    key : words_drkameleon[word][0][key] for key in ["pos", "pinyin", "definitions"]
                })

    return words_drkameleon


def load_words_kaikki(words, export_csv=False):
    """
    Load Wiktionary dataset.

    Source: https://kaikki.org/dictionary/Chinese/index.html
    """
    words_kaikki = {}

    # Read word data from JSONL file
    with open("raw/words/kaikki_dictionary-Chinese.jsonl", "r", encoding="utf-8") as words_jsonl:
        for line in words_jsonl:
            # Read word data
            word_full = json.loads(line)

            # Check if word is in word list
            word = chinese_converter.to_simplified(word_full["word"])
            if word not in words:
                continue

            # Discard proper nouns and incomplete entries
            word_pos = word_full["pos"]
            if word_pos in ["character", "name", "soft-redirect"]:
                continue
            
            # Start recording word data
            if word not in words_kaikki:
                words_kaikki[word] = []
            word_data = {
                "pos": POS_WIKTIONARY[word_pos],
                "source": "kaikki"
            }

            # Extract definitions
            word_definitions = []
            for sense in word_full["senses"]:
                if "glosses" not in sense:
                    continue
                word_definition = "; ".join([
                    re.sub(r" \(Classifier: .*\)", "", gloss)
                    for gloss in sense["glosses"] if not(
                        gloss.lower().startswith(("alternative ", "synonym of", "short for", "erhua"))
                    )
                ])
                if word_definition:
                    word_definitions.append(word_definition)
            if len(word_definitions) == 0:
                continue
            word_data["definitions"] = " | ".join(word_definitions)
            
            # Extract pinyin
            if "sounds" not in word_full:
                continue
            for sound in word_full["sounds"]:  
                if "tags" not in sound or any(tag not in sound["tags"] for tag in ["Mandarin", "Pinyin"]):
                    continue
                if re.search(r"[¹²³⁴⁵]", sound["zh_pron"]):
                    continue
                word_data["pinyin"] = sound["zh_pron"]
                break
            else:
                continue
            
            # Check if an entry already exists for the same POS
            for i in range(len(words_kaikki[word])):
                if words_kaikki[word][i]["pos"] == word_data["pos"]:
                    words_kaikki[word][i]["pinyin"] += "" if word_data["pinyin"] in words_kaikki[word][i]["pinyin"] else " | " + word_data["pinyin"]
                    words_kaikki[word][i]["definitions"] += " | " + word_data["definitions"]
                    break
            else:
                words_kaikki[word].append(word_data)
    
    # Export cleaned data to CSV
    if export_csv:
        with open("cleaned/words_kaikki.csv", "w") as words_csv:
            writer = csv.DictWriter(words_csv, ["word", "level", "difficulty", 
                                    "pos", "pinyin", "definitions"])
            writer.writeheader()
            for word in words_kaikki:
                for word_entry in words_kaikki.get(word):
                    writer.writerow({
                        "word": word
                    } | {
                        key : words[word][key] for key in ["level", "difficulty"]
                    } | {
                        key : word_entry[key] for key in ["pos", "pinyin", "definitions"]
                    })

    return words_kaikki


def merge_word_sources(words, words_drkameleon, words_kaikki):
    """
    Merge processed datasets.

    For single-character words, use drkameleon set.
    For multi-character words, use Kaikki entries whenever available (with drkameleon set as fallback).
    """
    for word in list(words.keys()):
        if len(word) > 1 and word in words_kaikki:
            words[word]["entries"] = words_kaikki[word]
        elif word in words_drkameleon:
            words[word]["entries"] = words_drkameleon[word]
        else:
            words.pop(word)


def export_word_data(words, characters):
    """
    Export processed word and character data.
    """
    # Export to JSON
    with open("../export/json/words.json", "w", encoding="utf-8") as words_json:
        json.dump(words, words_json, ensure_ascii=False)
    
    with open("../export/json/characters.json", "w", encoding="utf-8") as characters_json:
        json.dump(characters, characters_json, ensure_ascii=False)

    # Export to CSV
    with open("../export/csv/words.csv", "w", encoding="utf-8") as words_csv:
        writer = csv.DictWriter(words_csv, ["word", "level", "difficulty", 
                                "pos", "pinyin", "definitions", "source"])
        writer.writeheader()
        for word in words:
            for word_entry in words[word]["entries"]:
                writer.writerow({
                    "word": word
                } | {
                    key : words[word][key] for key in ["level", "difficulty"] 
                } | word_entry)
    
    with open("../export/csv/characters.csv", "w", encoding="utf-8") as characters_csv:
        writer = csv.DictWriter(characters_csv, ["character", "level"])
        writer.writeheader()
        for character in characters:
            writer.writerow({
                "character": character,
                "level": characters[character]
            })
