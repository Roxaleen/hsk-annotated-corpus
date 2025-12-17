# Export Schemas

The full word and sentence collections can be downloaded in CSV and JSON formats or as a SQL database.

In the HSK level fields, the number value `7` is used to collectively represent the HSK7–9 levels.

## CSV

[`characters.csv`](./csv/characters.csv): List of all characters and corresponding HSK levels

| `character` | `level` |
| --- | --- |
| Character | HSK level, identified by the lowest-level HSK word that contains the given character |

[`sentences.csv`](./csv/sentences.csv): List of all sentences in the collection

| `sentence` | `translation` | `level` | `character_level` | `word_level` | `source` |
| --- | --- | --- | --- | --- | --- |
| Sentence text | English translation | The HSK level of the sentence, determined by the higher value between `character_level` and `word_level` | The highest HSK level among all the characters present in the sentence | The highest HSK level among all the HSK words identified in the sentence | The source sentence collection (one of `tatoeba`, `kaikki`, or `leipzig`)

[`tags.csv`](./csv/tags.csv): List of HSK words identified in each sentence

| `sentence` | `word` | `pos` |
| --- | --- | --- |
| Sentence text | Word | Part of speech of the word, as used in the sentence |

[`words.csv`](./csv/words.csv): List of all HSK words included in the collection

| `word` | `level` | `frequency_ranking` | `pos` | `pinyin` | `definitions` | `source` |
| --- | --- | --- | --- | --- | --- | --- |
| Word | HSK level | Frequency ranking (lower value = higher frequency) | Part of speech | Pinyin transliteration | Definitions for the given part of speech | Source of definitions (one of `drkameleon` or `kaikki`) |

## JSON

[`characters.json`](./json/characters.json): List of all characters and corresponding HSK levels

```json
{
    "character [string]": "HSK level [integer]",
}
```

[`sentences.json`](./json/sentences.json): List of all sentences and tagged HSK words

```json
{
    "sentence text [string]": {
        "translation": "translation text [string]",
        "level": "HSK level, determined by the higher value between `character_level` and `word_level` [integer]",
        "character_level": "highest HSK level among all the characters present in the sentence [integer]",
        "word_level": "highest HSK level among all the HSK words identified in the sentence [integer]",
        "tags": [
            [
                "word [string]",
                "part of speech [string]"
            ],
        ],
        "source": "source sentence collection (one of `tatoeba`, `kaikki`, or `leipzig`) [string]"
    },
}
```

[`words.json`](./json/words.json): List of all words and associated data

```json
{
    "word [string]": {
        "level": "HSK level [integer]",
        "frequency_ranking": "frequency ranking (lower value = higher frequency) [integer]",
        "forms": {
            "part of speech [string]": {
                "pinyin": [
                    "pinyin transliteration [string]",
                ],
                "definitions": [
                    "definitions for the given part of speech [string]",
                ],
                "source": "source of definitions (one of `drkameleon` or `kaikki`) [string]"
            },
        }
    },
}
```

## SQL

[`data.db`](./sql/data.db): SQLite database with populated data tables and views, as described in [`schema.sql`](./sql/schema.sql)
