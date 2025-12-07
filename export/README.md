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
    "character [string]": HSK level [integer],
}
```

[`sentences.json`](./json/sentences.json): List of all sentences and tagged HSK words

```json
{
    "sentence text [string]": {
        "translation": "translation text [string]",
        "level": HSK level, determined by the higher value between `character_level` and `word_level` [integer],
        "character_level": highest HSK level among all the characters present in the sentence [integer],
        "word_level": highest HSK level among all the HSK words identified in the sentence [integer],
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
        "level": HSK level [integer],
        "frequency_ranking": frequency ranking (lower value = higher frequency) [integer],
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
```sql
-- DATA TABLES

-- Part of speech labels
CREATE TABLE IF NOT EXISTS pos (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    pos_label TEXT NOT NULL
);

-- Characters
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    character TEXT NOT NULL,
    level INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS character_index ON characters (character);

-- Words
CREATE TABLE IF NOT EXISTS words (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    level INTEGER NOT NULL,
    frequency_ranking INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS word_index ON words (word);

-- Word definitions
CREATE TABLE IF NOT EXISTS word_definitions (
    word_id INTEGER NOT NULL,
    pos_id INTEGER NOT NULL,
    pinyin TEXT NOT NULL,
    definitions TEXT NOT NULL,
    source TEXT NOT NULL,
    FOREIGN KEY (word_id) REFERENCES words(id),
    FOREIGN KEY (pos_id) REFERENCES pos(id),
    PRIMARY KEY (word_id, pos_id)
);

-- Sentences
CREATE TABLE IF NOT EXISTS sentences (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    sentence TEXT NOT NULL,
    translation TEXT NOT NULL,
    character_level INTEGER NOT NULL,
    word_level INTEGER NOT NULL,
    level INTEGER NOT NULL,
    source TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS sentence_index ON sentences (sentence);

-- Sentence-character matches
CREATE TABLE IF NOT EXISTS character_matches (
    sentence_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    FOREIGN KEY (sentence_id) REFERENCES sentences(id),
    FOREIGN KEY (character_id) REFERENCES words(id),
    PRIMARY KEY (sentence_id, character_id)
);

-- Sentence-words matches with POS tags
CREATE TABLE IF NOT EXISTS word_matches (
    sentence_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    pos_id INTEGER NOT NULL,
    FOREIGN KEY (sentence_id) REFERENCES sentences(id),
    FOREIGN KEY (word_id) REFERENCES words(id),
    FOREIGN KEY (pos_id) REFERENCES pos(id),
    PRIMARY KEY (sentence_id, word_id, pos_id)
);


-- VIEWS

-- Word definition view
CREATE VIEW IF NOT EXISTS word_definition_view AS
SELECT word_id, pos_id,
       word, level, frequency_ranking,
       pos_label,
       pinyin, definitions, source
FROM word_definitions
INNER JOIN words
    ON word_definitions.word_id = words.id
INNER JOIN pos
    ON word_definitions.pos_id = pos.id;

-- Sentence-character view
CREATE VIEW IF NOT EXISTS character_match_view AS
SELECT sentence_id, character_id,
       sentence, translation,
       character,
       characters.level AS character_level,
       sentences.level AS sentence_level,
       source AS sentence_source
FROM character_matches
INNER JOIN sentences
    ON character_matches.sentence_id = sentences.id
INNER JOIN characters
    ON character_matches.character_id = characters.id;

-- Sentence-word view
CREATE VIEW IF NOT EXISTS word_match_view AS
SELECT sentence_id, word_matches.word_id, word_matches.pos_id,
       sentence, translation,
       word,
       pos.pos_label AS sentence_pos,
       word_definition_view.pos_label AS definition_pos,
       pinyin, definitions,
       word_definition_view.level AS word_level,
       sentences.level AS sentence_level,
       sentences.source AS sentence_source,
       word_definition_view.source AS definition_source
FROM word_matches
INNER JOIN pos
    ON word_matches.pos_id = pos.id
INNER JOIN sentences
    ON word_matches.sentence_id = sentences.id
INNER JOIN word_definition_view
    ON word_matches.word_id = word_definition_view.word_id
WHERE word_matches.pos_id = word_definition_view.pos_id
    OR NOT EXISTS (
        SELECT 1
        FROM word_definition_view
        WHERE word_matches.word_id = word_definition_view.word_id
        AND word_matches.pos_id = word_definition_view.pos_id
    );
```