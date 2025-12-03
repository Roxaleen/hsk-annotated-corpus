"""
Tag the words and characters present in each sentence.
"""

import hanlp, math

# Standardized POS labels
from words import POS_PKU

# HanLP tokenizer
# Documentation: https://hanlp.hankcs.com/docs/api/hanlp/pretrained/tok.html
tok = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)

# HanLP POS tagger
# Documentation: https://hanlp.hankcs.com/docs/api/hanlp/pretrained/pos.html
pos = hanlp.load(hanlp.pretrained.pos.PKU_POS_ELECTRA_SMALL)

# Processing batch sizes
FEED_SIZE = 480
BATCH_SIZE = 32


def tag_sentences(sentences, words, characters):
    """
    Tokenize and tag every sentence in the collection.
    """
    sentence_list = list(sentences.keys())
    
    for sentence_list_batch in generate_sentence_feed(sentence_list):
        # Tokenize all sentences
        print("Tokenizing sentences...")
        tokens = tok(sentence_list_batch, batch_size=BATCH_SIZE)

        # Tag all sentences
        print("Tagging parts of speech...")
        tags = pos(tokens, batch_size=BATCH_SIZE)

        print("Tagging complete!")

        # Record tagged words
        for (index, sentence) in enumerate(sentence_list_batch):
            sentence_tokens = tokens[index]
            sentence_tags = tags[index]
            sentences[sentence]["tags"] = []

            for (index, word) in enumerate(sentence_tokens):
                if word not in words:
                    continue
                sentences[sentence]["tags"].append((word, POS_PKU[sentence_tags[index].lower()[0]]))

            # Compute sentence level
            (character_level, word_level) = compute_sentence_level(sentence, sentences, words, characters)
            sentences[sentence]["character_level"] = character_level
            sentences[sentence]["word_level"] = word_level


def generate_sentence_feed(sentence_list, feed_size=FEED_SIZE):
    """
    Split sentence list into small batches.
    """
    batch_count = math.ceil(len(sentence_list) / feed_size)

    for i in range(batch_count):
        print(f"Batch {i + 1} of {batch_count}:")
        yield sentence_list[i * feed_size : (i + 1) * feed_size]


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
