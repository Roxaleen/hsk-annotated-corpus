"""
Process word datasets.

HSK headwords and CC-CEDICT definitions: https://github.com/drkameleon/complete-hsk-vocabulary
Wiktionary dataset: https://kaikki.org/dictionary/Chinese/index.html
"""

import chinese_converter, csv, json, re


# Standardized POS labels
from pos import POS_PKU, POS_WIKTIONARY, predict_pos

# Join separator for definition lists
from sql import JOIN_STRING


# Process word data
def process_words(words, characters, export=False):
    """
    Process raw word datasets.
    """
    # Load word set by drkameleon
    words_drkameleon = load_words_drkameleon(words, characters)
    
    # Load Wiktionary dataset
    words_kaikki = load_words_kaikki(words)

    # Merge word datasets
    merge_word_sources(words, words_drkameleon, words_kaikki)

    # Export processed data
    if export:
        export_word_data(words, characters)


def load_words_drkameleon(words, characters, export=True):
    """
    Load word set by drkameleon.

    Source: https://github.com/drkameleon/complete-hsk-vocabulary
    """
    words_drkameleon = {}

    # Read full word data from JSON file
    with open("raw/words/drkameleon_hsk-vocabulary-complete.json", "r", encoding="utf-8") as words_json:
        words_full = json.load(words_json)

        # Extract headword fields
        for word in words_full:

            # Compile headword fields
            word_level = int(re.sub(r"[a-zA-Z\+\-]", "", word["level"][0]))
            words[word["simplified"]] = {
                "level": word_level,
                "frequency_ranking": int(word["frequency"])
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
            
            # Compile word data
            word_data = {
                "pinyin": list({form["transcriptions"]["pinyin"] for form in word_forms}),
                "definitions": word_meanings,
                "source": "drkameleon"
            }

            # Record word data
            words_drkameleon[word["simplified"]] = {}

            word_pos_set = {POS_PKU[pos_code.lower()[0]] for pos_code in word["pos"]}
            if len(word_pos_set) == 1:
                words_drkameleon[word["simplified"]][word_pos_set.pop()] = word_data
            else:
                words_drkameleon[word["simplified"]]["unsorted"] = word_data
            
            # Record character level
            for character in set(word["simplified"]):
                if character in characters:
                    characters[character] = min(characters[character], word_level)
                else:
                    characters[character] = words[word["simplified"]]["level"]
    
    # Extract all unsorted definitions for POS tagging
    input = [(word, definition) for word in words_drkameleon for definition in words_drkameleon[word].get("unsorted", {}).get("definitions", [])]
    labels = predict_pos(input)
    labels = {input[index] : labels[index] for index in range(len(input))}
    
    # Reorganize definitions by POS
    for word in words_drkameleon:
        if "unsorted" not in words_drkameleon[word]:
            continue

        for definition in words_drkameleon[word]["unsorted"]["definitions"]:
            # Get predicted POS label
            label = labels[((word, definition))]
            
            # Check if an entry already exists with the same POS
            if label in words_drkameleon[word]:
                words_drkameleon[word][label]["definitions"].append(definition)
            else:
                words_drkameleon[word][label] = {
                    "definitions": [definition],
                    "pinyin": words_drkameleon[word]["unsorted"]["pinyin"],
                    "source": words_drkameleon[word]["unsorted"]["source"],
                }
        
        words_drkameleon[word].pop("unsorted")

    # Export cleaned data
    if export:
        with open("cleaned/words_drkameleon.csv", "w", encoding="utf-8") as words_csv:
            writer = csv.DictWriter(words_csv, ["word", "level", "frequency_ranking", 
                                    "pos", "pinyin", "definitions"])
            writer.writeheader()
            for word in words_drkameleon:
                for pos in words_drkameleon[word]:
                    writer.writerow({
                        "word": word,
                        "level": words[word]["level"],
                        "frequency_ranking": words[word]["frequency_ranking"],
                        "pos": pos,
                        "pinyin": JOIN_STRING.join(words_drkameleon[word][pos]["pinyin"]),
                        "definitions": JOIN_STRING.join(words_drkameleon[word][pos]["definitions"])
                    })
        
        with open("tagged/words_drkameleon.json", "w", encoding="utf-8") as words_json:
            json.dump(words_drkameleon, words_json, ensure_ascii=False)

    return words_drkameleon


def load_words_kaikki(words, export=True):
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
            word_pos = POS_WIKTIONARY[word_pos]
            
            # Start recording word data
            if word not in words_kaikki:
                words_kaikki[word] = {}
            word_data = {
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
            word_data["definitions"] = word_definitions
            
            # Extract pinyin
            if "sounds" not in word_full:
                continue
            for sound in word_full["sounds"]:  
                if "tags" not in sound or any(tag not in sound["tags"] for tag in ["Mandarin", "Pinyin"]):
                    continue
                if re.search(r"[¹²³⁴⁵]", sound["zh_pron"]):
                    continue
                word_data["pinyin"] = [sound["zh_pron"]]
                break
            else:
                continue
            
            # Check if an entry already exists for the same POS
            if word_pos in words_kaikki[word]:
                words_kaikki[word][word_pos]["pinyin"].extend(word_data["pinyin"])
                words_kaikki[word][word_pos]["pinyin"] = list(dict.fromkeys(words_kaikki[word][word_pos]["pinyin"]))
                words_kaikki[word][word_pos]["definitions"].extend(word_data["definitions"])
            else:
                words_kaikki[word][word_pos] = word_data
    
    # Export cleaned data
    if export:
        with open("cleaned/words_kaikki.csv", "w") as words_csv:
            writer = csv.DictWriter(words_csv, ["word", "level", "frequency_ranking", 
                                    "pos", "pinyin", "definitions"])
            writer.writeheader()
            for word in words_kaikki:
                for pos in words_kaikki[word]:
                    writer.writerow({
                        "word": word,
                        "level": words[word]["level"],
                        "frequency_ranking": words[word]["frequency_ranking"],
                        "pos": pos,
                        "pinyin": JOIN_STRING.join(words_kaikki[word][pos]["pinyin"]),
                        "definitions": JOIN_STRING.join(words_kaikki[word][pos]["definitions"])
                    })

        with open("tagged/words_kaikki.json", "w", encoding="utf-8") as words_json:
            json.dump(words_kaikki, words_json, ensure_ascii=False)

    return words_kaikki


def merge_word_sources(words, words_drkameleon, words_kaikki):
    """
    Merge processed datasets.

    For single-character words, use drkameleon set whenever possible.
    For other words, merge entries while prioritizing Kaikki set.
    """
    for word in list(words.keys()):
        if len(word) == 1 and word in words_drkameleon:
            words[word]["forms"] = words_drkameleon[word]
        elif word in words_kaikki:
            words[word]["forms"] = words_drkameleon.get(word, {}) | words_kaikki[word]
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
        writer = csv.DictWriter(words_csv, ["word", "level", "frequency_ranking", 
                                "pos", "pinyin", "definitions", "source"])
        writer.writeheader()
        for word in words:
            for pos in words[word]["forms"]:
                writer.writerow({
                    "word": word,
                    "level": words[word]["level"],
                    "frequency_ranking": words[word]["frequency_ranking"],
                    "pos" : pos,
                    "pinyin" : JOIN_STRING.join(words[word]["forms"][pos]["pinyin"]),
                    "definitions" : JOIN_STRING.join(words[word]["forms"][pos]["definitions"]),
                    "source" : words[word]["forms"][pos]["source"]
                })
    
    with open("../export/csv/characters.csv", "w", encoding="utf-8") as characters_csv:
        writer = csv.DictWriter(characters_csv, ["character", "level"])
        writer.writeheader()
        for character in characters:
            writer.writerow({
                "character": character,
                "level": characters[character]
            })
