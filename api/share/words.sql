PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS words;

CREATE TABLE words(
id INTEGER PRIMARY KEY,
word VARCHAR,
UNIQUE(word)
)