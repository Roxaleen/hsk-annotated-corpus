import chinese_converter, csv, re


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

    # Read raw sentence data from TSV file
    with open("raw/sentences/tatoeba_cmn_sentences.tsv", "r") as sentences_tsv:
        reader = csv.reader(sentences_tsv, delimiter="\t")
        for row in reader:
            # Read sentence
            id = int(row[0])
            sentence = row[2]
            
            # Filter sentence
            sentence = filter_sentence(sentence, characters)
            if sentence is None:
                return
            
            sentences.append({"id": id, "sentence": sentence})

    # Write cleaned up data to new CSV file
    with open("cleaned/sentences_tatoeba.csv", "w") as sentences_csv:
        writer = csv.DictWriter(sentences_csv, ["id", "sentence"])
        writer.writeheader()
        writer.writerows(sentences)


# Filter sentence
def filter_sentence(sentence, characters):
    """
    Standardize and check the validity of a sentence.
    Return processed sentence if valid, else None.
    """
    # Reject sentences that contain alphabet letters or aren't complete
    if re.search(r"[a-zA-Z]", sentence) or not sentence.endswith(tuple(PUNCT_TERMINAL)):
        return None

    # Convert sentence from traditional to simplified Chinese
    # https://pypi.org/project/chinese-converter/
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