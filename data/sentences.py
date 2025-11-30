"""
Process sentence datasets.

Tatoeba dataset: https://tatoeba.org/en/downloads
Wiktionary dataset: https://kaikki.org/dictionary/Chinese/index.html
"""

import chinese_converter, csv, json, re


# Sentence length limits (including punctuation)
MIN_SENTENCE_LENGTH = 5
MAX_SENTENCE_LENGTH = 36


# Punctuation marks
PUNCT_STANDARDIZE = str.maketrans(
    {
        " ": "　",
        ",": "，",
        ";": "；",
        ":": "：",
        ".": "。",
        "⋯": "…",
        "!": "！",
        "?": "？",
        "(": "（",
        ")": "）",
        "“": "「",
        "”": "」",
        "~": "～",
    }
)
PUNCT_TERMINAL = {"。", "！", "？", "…", "」"}
PUNCT_NONTERMINAL = {"　", "、", "，", "；", "：", "（", "）", "《", "》", "「", "–", "⸺", "～"}
PUNCT = PUNCT_TERMINAL | PUNCT_NONTERMINAL


# Process sentences data
def process_sentences(sentences, characters):
    # Process Tatoeba sentence set
    sentences_tatoeba = process_sentences_tatoeba(characters)
    
    # Process Wiktionary example sentences
    sentences_kaikki = process_sentences_kaikki(characters)


def process_sentences_tatoeba(characters, export_csv=True):
    """
    Process Tatoeba sentence set.

    Source: https://tatoeba.org/en/downloads
    """
    sentences_tatoeba = set()

    # Read raw sentence data from TSV file
    with open("raw/sentences/tatoeba_cmn_sentences.tsv", "r") as sentences_tsv:
        reader = csv.reader(sentences_tsv, delimiter="\t")
        for row in reader:
            # Read sentence
            sentence = row[2]
            
            # Process sentence
            sentence = process_sentence(sentence, characters)
            if sentence is None:
                continue
            
            sentences_tatoeba.add(sentence)

    # Export cleaned data to CSV
    if export_csv:
        with open("cleaned/sentences_tatoeba.csv", "w") as sentences_csv:
            writer = csv.DictWriter(sentences_csv, ["id", "sentence"])
            writer.writeheader()
            for (index, sentence) in enumerate(sentences_tatoeba):
                writer.writerow({
                    "id": index + 1,
                    "sentence": sentence
                })
    
    return sentences_tatoeba


def process_sentences_kaikki(characters, export_csv=True):
    """
    Process Wiktionary example sentences.

    Source: https://kaikki.org/dictionary/Chinese/index.html
    """
    sentences_kaikki = set()

    # Read raw data from JSONL file
    with open("raw/words/kaikki_dictionary-Chinese.jsonl", "r", encoding="utf-8") as words_jsonl:
        for line in words_jsonl:
            # Read entry data
            entry = json.loads(line)

            # Check if headword contains non-HSK characters
            entry_headword = chinese_converter.to_simplified(entry["word"])
            if set(entry_headword) - characters:
                continue
            
            # Extract examples
            examples = {
                example.get("text", "")
                for sense in entry.get("senses", [])
                for example in sense.get("examples", [])
                if "tags" in example and "Classical-Chinese" not in example["tags"]
            }

            # Process examples
            examples = {process_sentence(example, characters) for example in examples} - {None}
            
            sentences_kaikki |= examples

    # Export cleaned data to CSV
    if export_csv:
        with open("cleaned/sentences_kaikki.csv", "w") as sentences_csv:
            writer = csv.DictWriter(sentences_csv, ["id", "sentence"])
            writer.writeheader()
            for (index, sentence) in enumerate(sentences_kaikki):
                writer.writerow({
                    "id": index + 1,
                    "sentence": sentence
                })
    
    return sentences_kaikki


def process_sentence(sentence, characters):
    """
    Standardize and check the validity of a sentence.
    Return processed sentence if valid, else None.
    """
    # Reject sentences that are too long or too short
    if len(sentence) > MAX_SENTENCE_LENGTH or len(sentence) < MIN_SENTENCE_LENGTH:
        return None
    
    # Reject sentences that contain alphabet letters or are incomplete
    if re.search(r"[a-zA-Z]", sentence) or not sentence.endswith(tuple(PUNCT_TERMINAL)):
        return None

    # Convert to simplified characters
    sentence = chinese_converter.to_simplified(sentence)

    # Standardize punctuation
    sentence = sentence.translate(PUNCT_STANDARDIZE)

    # Reject sentences containing any non-HSK characters
    if set(sentence) - characters - PUNCT:
        return None
    
    # Reject sentences with only two unique characters (or fewer)
    if len(set(sentence) & characters) <= 2:
        return None
    
    return sentence
