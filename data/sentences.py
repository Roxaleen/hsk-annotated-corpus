"""
Process sentence datasets.

Tatoeba dataset: https://tatoeba.org/en/downloads
Wiktionary dataset: https://kaikki.org/dictionary/Chinese/index.html
Leipzig 2015 Chinese web corpus: https://corpora.uni-leipzig.de/en?corpusId=zho_news_2020
"""

import chinese_converter, csv, json, re

from tags import tag_sentences


# Sentence length limits (including punctuation)
MIN_SENTENCE_LENGTH = 5
MAX_SENTENCE_LENGTH = 36


# Permitted punctuation marks
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
PUNCT_TERMINAL = {"。", "！", "？", "…", "」", "》"}
PUNCT_NONTERMINAL = {"、", "，", "；", "：", "（", "）", "《", "》", "「", "–", "⸺", "～"}
PUNCT_NONINITIAL = PUNCT_TERMINAL | {"、", "，", "；", "：", "–", "⸺", "～"}
MATH = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "%", "$"}
ALLOWED_SYMBOLS = PUNCT_TERMINAL | PUNCT_NONTERMINAL | MATH


# Process sentences data
def process_sentences(sentences, words, characters, export=False):
    """
    Process raw sentence datasets.
    """
    # Load and tag Tatoeba sentence set
    try:
        with open("tagged/sentences_tatoeba.json", "r", encoding="utf-8") as sentences_json:
            sentences_tatoeba = json.load(sentences_json)
    except:
        print("Processing Tatoeba sentences...")
        sentences_tatoeba = load_sentences_tatoeba(characters)
        tag_sentences(sentences_tatoeba, words, characters)
        with open("tagged/sentences_tatoeba.json", "w", encoding="utf-8") as sentences_json:
            json.dump(sentences_tatoeba, sentences_json, ensure_ascii=False)
    
    # Load and tag Wiktionary example sentences
    try:
        with open("tagged/sentences_kaikki.json", "r", encoding="utf-8") as sentences_json:
            sentences_kaikki = json.load(sentences_json)
    except:
        print("Processing Kaikki sentences...")
        sentences_kaikki = load_sentences_kaikki(characters)
        tag_sentences(sentences_kaikki, words, characters)
        with open("tagged/sentences_kaikki.json", "w", encoding="utf-8") as sentences_json:
            json.dump(sentences_kaikki, sentences_json, ensure_ascii=False)
    
    # Load and tag Leipzig corpus sentences
    try:
        with open("tagged/sentences_leipzig.json", "r", encoding="utf-8") as sentences_json:
            sentences_leipzig = json.load(sentences_json)
    except:
        print("Processing Leipzig sentences...")
        sentences_leipzig = load_sentences_leipzig(characters)
        tag_sentences(sentences_leipzig, words, characters)
        with open("tagged/sentences_leipzig.json", "w", encoding="utf-8") as sentences_json:
            json.dump(sentences_leipzig, sentences_json, ensure_ascii=False)

    # Merge sentence datasets
    sentences.update(sentences_tatoeba)
    sentences.update(sentences_kaikki)
    sentences.update(sentences_leipzig)

    # Export processed data
    if export:
        export_sentence_data(sentences)


def load_sentences_tatoeba(characters, export_csv=False):
    """
    Load Tatoeba sentence set.

    Source: https://tatoeba.org/en/downloads
    """
    sentences_tatoeba = {}

    # Read raw sentence data from TSV file
    with open("raw/sentences/tatoeba_cmn_sentences.tsv", "r") as sentences_tsv:
        reader = csv.reader(sentences_tsv, delimiter="\t")
        for row in reader:
            # Read sentence
            sentence = row[2]
            
            # Clean sentence
            sentence = clean_sentence(sentence, characters)
            if sentence is None:
                continue
            
            sentences_tatoeba[sentence] = {"source": "tatoeba"}

    # Export cleaned data to CSV
    if export_csv:
        with open("cleaned/sentences_tatoeba.csv", "w") as sentences_csv:
            writer = csv.writer(sentences_csv)
            writer.writerow(["sentence"])
            for sentence in sentences_tatoeba:
                writer.writerow([sentence])
    
    return sentences_tatoeba


def load_sentences_kaikki(characters, export_csv=False):
    """
    Load Wiktionary example sentences.

    Source: https://kaikki.org/dictionary/Chinese/index.html
    """
    sentences_kaikki = {}

    # Read raw data from JSONL file
    with open("raw/words/kaikki_dictionary-Chinese.jsonl", "r", encoding="utf-8") as data_jsonl:
        for line in data_jsonl:
            # Read entry data
            entry = json.loads(line)

            # Check if headword contains non-HSK characters
            entry_headword = chinese_converter.to_simplified(entry["word"])
            if set(entry_headword) - set(characters.keys()):
                continue
            
            # Extract examples
            examples = {
                example.get("text", "")
                for sense in entry.get("senses", [])
                for example in sense.get("examples", [])
                if "tags" in example and "Classical-Chinese" not in example["tags"]
            }

            # Clean examples
            examples = {clean_sentence(example, characters) for example in examples} - {None}
            
            # Record cleaned sentences
            for sentence in examples:
                sentences_kaikki[sentence] = {"source": "kaikki"}

    # Export cleaned data to CSV
    if export_csv:
        with open("cleaned/sentences_kaikki.csv", "w") as sentences_csv:
            writer = csv.writer(sentences_csv)
            writer.writerow(["sentence"])
            for sentence in sentences_kaikki:
                writer.writerow([sentence])
    
    return sentences_kaikki


def load_sentences_leipzig(characters, export_csv=False):
    """
    Load Leipzig corpus sentences.

    Source: https://corpora.uni-leipzig.de/en?corpusId=zho_news_2020
    """
    sentences_leipzig = {}

    # Read raw data from TXT file
    with open("raw/sentences/leipzig_zho-cn_web_2015_1M-sentences.txt", "r", encoding="utf-8") as sentences_txt:
        lines = sentences_txt.readlines()

        for line in lines:
            # Read sentence
            sentence = line.strip().split("\t")[1]

            # Clean sentence
            sentence = clean_sentence(sentence, characters)
            if sentence is None:
                continue
            
            sentences_leipzig[sentence] = {"source": "leipzig"}

    # Export cleaned data to CSV
    if export_csv:
        with open("cleaned/sentences_leipzig.csv", "w") as sentences_csv:
            writer = csv.writer(sentences_csv)
            writer.writerow(["sentence"])
            for sentence in sentences_leipzig:
                writer.writerow([sentence])
    
    return sentences_leipzig


def clean_sentence(sentence, characters):
    """
    Standardize and check the validity of a sentence.
    Return processed sentence if valid, else None.
    """
    # Convert to simplified characters
    sentence = chinese_converter.to_simplified(sentence)

    # Standardize punctuation
    sentence = sentence.translate(PUNCT_STANDARDIZE)
    sentence = re.sub(r"([0-9])。([0-9])", r"\1\.\2", sentence)

    # If any brackets are opened but not closed, trim sentence up to the opening brackets
    match = re.search(r"(（(?![^）]*）))|(「(?![^」]*」))|(《(?![^》]*》))", sentence)
    if match:
        sentence = sentence[match.end():]
    
    # If sentence ends with a closing bracket with no opening bracket, trim the trailing bracket
    if (sentence.endswith("」") and "「" not in sentence) or (sentence.endswith("》") and "《" not in sentence):
        sentence = sentence[:-1]
    
    # If sentence begins and ends with matching brackets, trim both brackets
    if (sentence.endswith("」") and sentence.startswith("「")) or (sentence.endswith("》") and sentence.startswith("《")):
        sentence = sentence[1:-1]
    
    # Reject sentences with invalid starting or ending punctuation
    if sentence.startswith(tuple(PUNCT_NONINITIAL)) or not sentence.endswith(tuple(PUNCT_TERMINAL)):
        return None

    # Reject sentences starting with enumeration (which also tend to be incomplete)
    if re.search(r"^(第?[一二三四五六七八九十0-9]+[、，。是则])|(（[一二三四五六七八九十0-9]+）)", sentence):
        return None

    # Reject sentences containing Latin alphabet characters or non-HSK characters:
    character_set = set(characters.keys())
    if re.search(r"[a-zA-Z]", sentence) or set(sentence) - character_set - ALLOWED_SYMBOLS:
        return None

    # Reject sentences that are too long or too short
    if len(sentence) > MAX_SENTENCE_LENGTH or len(sentence) < MIN_SENTENCE_LENGTH:
        return None
    
    # Reject sentences with only two unique characters (or fewer)
    if len(set(sentence) & character_set) <= 2:
        return None
    
    return sentence


def export_sentence_data(sentences):
    """
    Export processed sentence data.
    """
    # Export to JSON
    with open("../export/json/sentences.json", "w", encoding="utf-8") as sentences_json:
        json.dump(sentences, sentences_json, ensure_ascii=False)

    # Export to CSV
    with open("../export/csv/sentences.csv", "w", encoding="utf-8") as sentences_csv:
        writer = csv.DictWriter(sentences_csv, ["sentence", "character_level", "word_level", "source"])
        writer.writeheader()
        for sentence in sentences:
            if "tags" not in sentences[sentence]:
                continue
            writer.writerow({
                "sentence": sentence
            } | {
                key : sentences[sentence][key] for key in ["character_level", "word_level", "source"] 
            })

    with open("../export/csv/tags.csv", "w", encoding="utf-8") as tags_csv:
        writer = csv.DictWriter(tags_csv, ["sentence", "word", "pos"])
        writer.writeheader()
        for sentence in sentences:
            if "tags" not in sentences[sentence]:
                continue
            for tag in sentence["tags"]:
                writer.writerow({
                    "sentence": sentence,
                    "word": tag[0],
                    "pos": tag[1]
                })
