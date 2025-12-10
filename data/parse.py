"""
Parse and tag each sentence using HanLP's NLP tools.

HanLP documentation: https://hanlp.hankcs.com/docs/index.html
Argos Translate documentation: https://argos-translate.readthedocs.io/en/latest/
"""

import deep_translator, hanlp, json, math


# Standardized POS labels
from pos import POS_PKU

# HanLP constituency parser
# Documentation: https://hanlp.hankcs.com/docs/api/hanlp/pretrained/constituency.html
con = hanlp.load(hanlp.pretrained.constituency.CTB9_CON_FULL_TAG_ELECTRA_SMALL)

# HanLP tokenizer
# Documentation: https://hanlp.hankcs.com/docs/api/hanlp/pretrained/tok.html
tok = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)

# HanLP POS tagger
# Documentation: https://hanlp.hankcs.com/docs/api/hanlp/pretrained/pos.html
pos = hanlp.load(hanlp.pretrained.pos.PKU_POS_ELECTRA_SMALL)

# deep_translator GoogleTranslator instance
# Documentation: https://deep-translator.readthedocs.io/en/latest/
translator = deep_translator.GoogleTranslator(source='zh-CN', target='en')

# Processing batch sizes
FEED_SIZE = 480
BATCH_SIZE = 32


def parse_sentences(sentences, words, characters):
    """
    Tokenize, parse, and tag every sentence in the collection.
    """
    sentence_list = list(sentences.keys())
    
    for sentence_list_batch in generate_sentence_feed(sentence_list):
        # Tokenize all sentences
        print("Tokenizing sentences...")
        tokens = tok(sentence_list_batch, batch_size=BATCH_SIZE)

        # Perform constituency parsing to validate each sentence
        print("Parsing sentences...")
        validate_sentences(sentences, sentence_list_batch, tokens)

        # Perform POS tagging
        print("Tagging parts of speech...")
        tags = pos(tokens, batch_size=BATCH_SIZE)

        # Record tagged words
        print("Recording tagged words...")
        record_tags(sentences, words, characters, sentence_list_batch, tokens, tags)


def generate_sentence_feed(sentence_list, feed_size=FEED_SIZE):
    """
    Split sentence list into small batches.
    """
    batch_count = math.ceil(len(sentence_list) / feed_size)

    for i in range(batch_count):
        print(f"Batch {i + 1} of {batch_count}:")
        yield sentence_list[i * feed_size : (i + 1) * feed_size]


def validate_sentences(sentences, sentence_list, tokens):
    """
    Perform constituency parsing to validate each sentence.
    """
    # Omit final token (terminal punctuation) as it can skew the output
    trees = con(
        [token[:-1] for token in tokens],
        batch_size=BATCH_SIZE
    )

    # Check sentence validity
    invalid = {}
    for (index, sentence) in enumerate(sentence_list):
        # Check if top node is a clause ("CP" or "IP")
        try:
            if any(clause_label in trees[index][0].label() for clause_label in ["CP", "IP"]):
                continue
        except:
            pass
        # If top node is not a clause, mark sentence for deletion (sentence is incomplete)
        invalid[index] = sentence
    
    # Discard incomplete sentences 
    for index in reversed(list(invalid.keys())):
        sentence_list.pop(index)
        tokens.pop(index)
        sentences.pop(invalid[index])


def record_tags(sentences, words, characters, sentence_list, tokens, tags):
    """
    Record tagged words and characters.
    """
    for (index, sentence) in enumerate(sentence_list):
        sentence_tokens = tokens[index]
        sentence_tags = tags[index]
        sentences[sentence]["tags"] = []

        for (index, word) in enumerate(sentence_tokens):
            if word not in words:
                continue
            sentences[sentence]["tags"].append([word, POS_PKU[sentence_tags[index].lower()[0]]])

        # Compute sentence level
        (character_level, word_level) = compute_sentence_level(sentence, sentences, words, characters)
        sentences[sentence]["character_level"] = character_level
        sentences[sentence]["word_level"] = word_level
        sentences[sentence]["level"] = max(character_level, word_level)


def compute_sentence_level(sentence, sentences, words, characters):
    """
    Compute the HSK level of a sentence.

    Highest character level = highest HSK level among the characters present in the sentence.
    Highest word level = highest HSK level among the HSK words present in the sentence.
    """
    # Compute highest character level
    character_level = 0
    for character in set(sentence):
        if character not in characters:
            continue
        character_level = max(character_level, characters[character])

    # Compute highest word level
    word_level = 0
    for (word, pos_tag) in sentences[sentence]["tags"]:
        word_level = max(word_level, words[word]["level"])
    
    return (character_level, word_level)


def translate_sentences(sentences):
    """
    Supply translations for each sentence in the collection.
    """
    # Load existing progress log
    try:
        with open("working/translations.json", "r", encoding="utf-8") as translations_json:
            translations = json.load(translations_json)
    except:
        translations = {}

    # List all sentences with no recorded translation
    sentence_list = [
        sentence for sentence in sentences
        if "translation" not in sentences[sentence]
        or not sentences[sentence]["translation"]
    ]

    # Process sentences in batches
    skipped = False

    for sentence_list_batch in generate_sentence_feed(sentence_list, feed_size=100):
        # Translate sentences
        for sentence in sentence_list_batch:
            new_translation = False

            if sentence in translations:
                translation = translations[sentence]
            else:
                try:
                    translation = translator.translate(sentence)
                except:
                    skipped = True
                    continue
                translation = translation[0].upper() + translation[1:]  # Capitalize first letter
                translations[sentence] = translation
                new_translation = True
            
            sentences[sentence]["translation"] = translation
        
        # Save current progress log
        if not new_translation:
            continue
        with open("working/translations.json", "w", encoding="utf-8") as translations_json:
            json.dump(translations, translations_json, ensure_ascii=False)
    
    # Re-run until all sentences are translated successfully
    if skipped:
        translate_sentences(sentences)
