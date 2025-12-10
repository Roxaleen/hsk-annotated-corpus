-- CREATE DATA TABLES

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
-- CREATE INDEX IF NOT EXISTS character_index ON characters (character);

-- Words
CREATE TABLE IF NOT EXISTS words (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    level INTEGER NOT NULL,
    frequency_ranking INTEGER NOT NULL
);
-- CREATE INDEX IF NOT EXISTS word_index ON words (word);

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
-- CREATE INDEX IF NOT EXISTS sentence_index ON sentences (sentence);

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


-- CREATE VIEWS

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
    -- If there's no exact POS match, list all available definitions
    OR NOT EXISTS (
        SELECT 1
        FROM word_definition_view
        WHERE word_matches.word_id = word_definition_view.word_id
        AND word_matches.pos_id = word_definition_view.pos_id
    );
