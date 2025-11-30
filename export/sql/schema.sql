CREATE TABLE words (
    id INTEGER NOT NULL PRIMARY KEY,
    word TEXT NOT NULL,
    level INTEGER NOT NULL,
    difficulty INTEGER NOT NULL,
    pos TEXT NOT NULL,
    pinyin TEXT NOT NULL,
    definitions TEXT NOT NULL
);

CREATE TABLE sentences (
    id INTEGER NOT NULL PRIMARY KEY,
    sentence TEXT NOT NULL,
    difficulty INTEGER NOT NULL
);

CREATE TABLE cloze (
    word_id INTEGER NOT NULL,
    sentence_id INTEGER NOT NULL,
    FOREIGN KEY (word_id) REFERENCES words(id),
    FOREIGN KEY (sentence_id) REFERENCES sentences(id)
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    hash TEXT NOT NULL,
    level INTEGER NOT NULL
);

CREATE TABLE missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE flashcards (
    user_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    due DATETIME NOT NULL,
    PRIMARY KEY(user_id, word_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (word_id) REFERENCES words(id)
);
