PRAGMA foreign_keys = OFF;

DROP VIEW IF EXISTS wins;
DROP VIEW IF EXISTS streaks;
DROP TABLE IF EXISTS games;

CREATE TABLE games(
    user_uuid GUID NOT NULL,
    user_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    finished DATE DEFAULT CURRENT_TIMESTAMP,
    guesses INTEGER,
    won BOOLEAN,
    PRIMARY KEY(game_id)
);

CREATE INDEX games_won_idx ON games(won);

CREATE VIEW wins
AS
    SELECT
        user_uuid,
        COUNT(won) AS count_wins
    FROM
        games
    WHERE
        won = TRUE
    GROUP BY
        user_uuid
    ORDER BY
        COUNT(won) DESC;

CREATE VIEW streaks
AS
    WITH ranks AS (
        SELECT DISTINCT
            user_uuid,
            finished,
            RANK() OVER(PARTITION BY user_uuid ORDER BY finished) AS rank
        FROM
            games
        WHERE
            won = TRUE
        ORDER BY
            user_uuid,
            finished
    ),
    groups AS (
        SELECT
            user_uuid,
            finished,
            rank,
            DATE(finished, '-' || rank || ' DAYS') AS base_date
        FROM
            ranks
    )
    SELECT
        user_uuid,
        COUNT(*) AS streak,
        MIN(finished) AS beginning,
        MAX(finished) AS ending
    FROM
        groups
    GROUP BY
        user_uuid, base_date
    HAVING
        streak > 1
    ORDER BY
        user_uuid,
        finished;

PRAGMA analysis_limit=1000;
PRAGMA optimize;