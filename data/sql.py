"""
Export all data to a SQLite database.
"""

import sqlite3

# Standardized POS labels
from pos import POS_PKU

# Join separator for definition lists
JOIN_STRING = " | "


def export_sql(sentences, words, characters, rewrite=True):
    """
    Export all data to a SQLite database.
    """
    # Connect to database
    con = sqlite3.connect("../export/sql/data.db")
    cur = con.cursor()

    # Drop existing tables and views
    if rewrite:
        cur.executescript("""
            DROP VIEW IF EXISTS word_definition_view;
            DROP VIEW IF EXISTS character_match_view;
            DROP VIEW IF EXISTS word_match_view;
            DROP TABLE IF EXISTS character_matches;
            DROP TABLE IF EXISTS word_matches;
            DROP TABLE IF EXISTS word_definitions;
            DROP TABLE IF EXISTS pos;
            DROP TABLE IF EXISTS characters;
            DROP TABLE IF EXISTS words;
            DROP TABLE IF EXISTS sentences;
        """)

    # Create tables
    with open("../export/sql/schema.sql", "r") as schema_sql:
        schema = schema_sql.read()
    cur.executescript(schema)

    # Write parts of speech
    print("Writing parts of speech...")
    cur.executemany(
        "INSERT INTO pos (pos_label) VALUES (?);",
        [(pos,) for pos in sorted(set(POS_PKU.values())) + ["multiple"]]
    )
    con.commit()

    # Write characters
    print("Writing characters...")
    cur.executemany(
        "INSERT INTO characters (character, level) VALUES (?, ?);",
        [(character, characters[character]) for character in characters]
    )
    cur.execute("CREATE INDEX IF NOT EXISTS character_index ON characters (character);")
    con.commit()

    # Write words
    print("Writing words...")
    cur.executemany(
        "INSERT INTO words (word, level, frequency_ranking) VALUES (?, ?, ?);",
        [(word, words[word]["level"], words[word]["frequency_ranking"]) for word in words]
    )
    cur.execute("CREATE INDEX IF NOT EXISTS word_index ON words (word);")
    con.commit()

    # Write word definitions
    print("Writing word definitions...")
    cur.executemany(
        """
            INSERT INTO word_definitions (word_id, pos_id, pinyin, definitions, source)
            VALUES (
                (SELECT id FROM words WHERE word = ?),
                (SELECT id FROM pos WHERE pos_label = ?),
                ?, ?, ?
            );
        """,
        [
            (
                word,
                entry["pos"] if entry["pos"] in set(POS_PKU.values()) else "multiple",
                entry["pinyin"],
                JOIN_STRING.join(entry["definitions"]),
                entry["source"]
            )
            for word in words
            for entry in words[word]["entries"]
        ]
    )
    con.commit()
    
    # Write sentences
    print("Writing sentences...")
    cur.executemany(
        "INSERT INTO sentences (sentence, character_level, word_level, source) VALUES (?, ?, ?, ?);",
        [
            (sentence, sentences[sentence]["character_level"], sentences[sentence]["word_level"], sentences[sentence]["source"])
            for sentence in sentences
        ]
    )
    cur.execute("CREATE INDEX IF NOT EXISTS sentence_index ON sentences (sentence);")
    con.commit()

    # Write character matches
    print("Writing character matches...")
    cur.executemany(
        """
            INSERT INTO character_matches (sentence_id, character_id)
            VALUES (
                (SELECT id FROM sentences WHERE sentence = ?),
                (SELECT id FROM characters WHERE character = ?)
            )
            ON CONFLICT DO NOTHING;
        """,
        [
            (sentence, character)
            for sentence in sentences
            for character in set(sentence) & set(characters.keys())
        ]
    )
    con.commit()

    # Write word matches
    print("Writing word matches...")
    cur.executemany(
        """
            INSERT INTO word_matches (sentence_id, word_id, pos_id)
            VALUES (
                (SELECT id FROM sentences WHERE sentence = ?),
                (SELECT id FROM words WHERE word = ?),
                (SELECT id FROM pos WHERE pos_label = ?)
            )
            ON CONFLICT DO NOTHING;
        """,
        [
            (sentence, tag[0], tag[1])
            for sentence in sentences
            for tag in sentences[sentence]["tags"]
        ]
    )
    con.commit()

    # Close connection
    con.close()
