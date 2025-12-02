"""
Tag the words and characters present in each sentence.
"""

import hanlp

# Standardized POS labels
from words import POS_PKU

# HanLP tokenizer
# Documentation: https://hanlp.hankcs.com/docs/api/hanlp/pretrained/tok.html
tok = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)

# HanLP POS tagger
# Documentation: https://hanlp.hankcs.com/docs/api/hanlp/pretrained/pos.html
pos = hanlp.load(hanlp.pretrained.pos.PKU_POS_ELECTRA_SMALL)


def tag_sentences(sentences, words, characters):
    """
    Tokenize and tag every sentence in the collection.
    """
    sentence_list = list(sentences.keys())

    # Tokenize all sentences
    print("Tokenizing sentences...")
    tokens = tok(sentence_list)

    # Tag all sentences
    print("Tagging parts of speech...")
    tags = pos(tokens)

    print("Tagging complete!")

    # Record tagged words
    for (index, sentence) in enumerate(sentence_list):
        sentence_tokens = tokens[index]
        sentence_tags = tags[index]
        sentences["tags"] = []

        for (index, word) in enumerate(sentence_tokens):
            if word not in words:
                continue
            sentences[sentence]["tags"].append((word, POS_PKU[sentence_tags[index].lower()[0]]))

            # Compute sentence level
            (character_level, word_level) = compute_sentence_level(sentence, sentences, words, characters)
            sentences[sentence]["character_level"] = character_level
            sentences[sentence]["word_level"] = word_level


def compute_sentence_level(sentence, sentences, words, characters):
    """
    Compute the HSK level of a sentence.

    Highest character level = highest HSK level among the characters present in the sentence.
    Highest word level = highest HSK level among the HSK words present in the sentence.
    """
    # Compute highest character level
    character_level = 0
    for character in set(sentence):
        character_level = min(character_level, characters[character])

    # Compute highest word level
    word_level = 0
    for (word, pos_tag) in sentences[sentence]["tags"]:
        word_level = min(word_level, words[word]["level"])
    
    return (character_level, word_level)
