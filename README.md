# HSK Annotated Corpus

This project is an annotated collection of over 10,000 words and 250,000 sentences for Mandarin Chinese language learning.

## Key Features

The following information is included for every word and sentence in the collection:

- **Words:** All words are marked with definitions, pinyin, HSK level, and a frequency ranking.

    The definitions are classified by part of speech. This makes it easier to look up the meaning of a word as it is used in a specific context.

- **Sentences:** Each sentence comes with an English translation and is graded by HSK level.

    The HSK words present in each sentence are identified and tagged by the parts of speech corresponding to each specific usage.

## Exported Formats

The full collection can be downloaded in CSV or JSON formats or as a SQL database.

Download files and schemas can be found in the [`export`](/export/) directory.

## Word Processing

### Data Sources

This project builds on [drkameleon's HSK vocabulary collection](https://github.com/drkameleon/complete-hsk-vocabulary), which includes HSK levels, frequency rankings, and CC-CEDICT definitions for all words. Wiktionary data (as extracted and pre-processed by [Kaikki.org](https://kaikki.org/dictionary/Chinese/index.html)) are used to enhance the definitions and part-of-speech classifications.

- For multi-character words, Wiktionary definitions are preferred as they tend to be more concise and are labeled by parts of speech.

- For single-character words, however, Wiktionary data have been found to be lacking: the part of speech is simply "character", and there's no distinction between the meanings of a character when used to create compound words and the meanings of that character as a standalone, single-character word. Thus, the CC-CEDICT definitions (included in drkameleon's dataset) are preferred for these words.

### Part-of-Speech Classification

Unlike Wiktionary, CC-CEDICT does not include part of speech in its dictionary entries.

To fill this gap, a neural network has been trained to classify word definitions by part of speech. The model takes headword–definition pairs as input and is trained on the complete Chinese Wiktionary dataset. It is then used to assign part-of-speech labels to the CC-CEDICT definitions.

## Sentence Processing

### Data Sources

The sentence collection contains sentences from three sources:

- **[Tatoeba.org](https://tatoeba.org/en/downloads)**: This is a crowd-sourced database of multilingual sentence translations. While the sentences cover a broad range of linguistic complexity suitable for language learners, the crowd-sourced nature means that there can be some inappropriate content. Additionally, as the sentences are often written in a different language before being translated to Chinese, they may sometimes contain oddities that aren't natural or native to the Chinese language.

- **Wiktionary (via [Kaikki.org](https://kaikki.org/dictionary/Chinese/index.html)):** Many Wiktionary entries include example sentences to illustrate the headwords. Some examples are sourced from literature, films, or other media, and others feature regional or colloquial language, which adds a sprinkling of linguistic diversity to the collection.

- **Leipzig Corpora Collection ([Chinese 2015 web corpus](https://corpora.uni-leipzig.de/en?corpusId=zho_news_2020)):** This corpus contains 1,000,000 sentences gathered by scraping Chinese websites. Most entries are longer sentences featuring advanced vocabulary, useful for higher HSK levels. This is a great source of natural "in-the-wild" language, though the content can sometimes be relatively formal and/or political.

During pre-processing, all sentences are converted to Simplified Chinese characters. Additionally, the following entries are omitted from the collection:

- Sentences with invalid or non-HSK characters
- Sentences with invalid punctuation (signaling sentence fragments or incomplete sentences)
- Sentences that are too long or too short

The remaining sentences then proceed to the next stage for tokenization and tagging.

### Natural Language Processing (NLP)

The [HanLP NLP library](https://hanlp.hankcs.com/docs/index.html) is used to perform the following tasks:

- **Tokenization:** Each sentence is broken down into semantic units (tokens).

- **Constituency parsing:** This is used to check the syntactic structure of each sentence. Sentences not containing a clause as the largest subtree are deemed grammatically incomplete and are omitted from the collection.

- **Part-of-speech tagging:** Lastly, each token in every sentence is tagged by its part of speech.

For sentences that don't already come with English translations (some sentences from Wiktionary, and all sentences from Leipzig), translations are generated with [deep_translator](https://deep-translator.readthedocs.io/en/latest/).

## Acknowledgements

This project relies heavily on the following tools and resources:

- Data sources:

    - Word lists and definitions: [drkameleon/complete-hsk-vocabulary](https://github.com/drkameleon/complete-hsk-vocabulary), [Kaikki.org](https://kaikki.org/dictionary/Chinese/index.html)

    - Sentence collections: [Tatoeba.org](https://tatoeba.org/en/downloads), [Leipzig Corpora Collection](https://corpora.uni-leipzig.de/en?corpusId=zho_news_2020)

- Traditional to simplified character conversion: [zachary822/chinese-converter](https://github.com/zachary822/chinese-converter)

- NLP and machine learning libraries: [HanLP](https://hanlp.hankcs.com/docs/index.html), [TensorFlow](https://www.tensorflow.org/)

- Translation: [deep_translator](https://deep-translator.readthedocs.io/en/latest/)