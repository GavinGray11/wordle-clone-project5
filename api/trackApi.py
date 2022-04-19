# v2

import logging.config
import sqlite3
import contextlib
from fastapi import FastAPI, Depends, Response, HTTPException, status
from pydantic import BaseModel, BaseSettings
from datetime import datetime
# connect database setting from .env file
# convert data from stats.db to populated.sql
# sqlite3 ./var/stats.db .dump > ./share/populated.sql


class Settings(BaseSettings):
    stats_database: str
    logging_config: str

    class Config:
        env_file = ".env"

# Base model for getting guess word


class GameResult(BaseModel):
    game_id: int
    finished: str
    guesses: int
    won: int


class UserStats(BaseModel):
    current_streak: int
    max_streak: int
    guesses: dict
    win_percentage: float
    games_played: int
    games_won: int
    average_guesses: int
# connect database with word_list.sql


def get_db():
    with contextlib.closing(sqlite3.connect(settings.stats_database)) as db:
        db.row_factory = sqlite3.Row
        yield db
# use for debug the code


def get_logger():
    return logging.getLogger(__name__)


settings = Settings()
app = FastAPI()
logging.config.fileConfig(settings.logging_config)
# getting all the word from the word_list database and display


@app.post("/game-result/{current_user}", status_code=status.HTTP_201_CREATED)
def post_result(current_user: int, game: GameResult, response: Response, db: sqlite3.Connection = Depends(get_db)):
    g = dict(game)
    g.update({"user_id": current_user})
    try:
        # add word into the list_word database
        add_game = db.execute(
            """
            INSERT INTO games(user_id, game_id, finished, guesses, won) 
            VALUES(:user_id, :game_id, :finished, :guesses, :won)
            """, g
        )
        db.commit()
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(error).__name__, "msg": str(error)}
        )
    g["id"] = add_game.lastrowid
    response.headers["Location"] = f"/game-result/{g['id']}"
    return g


@app.get("/wordle-statistics/{current_user}/{current_date}")
def game_stats(current_user: int, current_date: str, db: sqlite3.Connection = Depends(get_db)):
    current_stats = db.execute(
        """SELECT guesses,won FROM games WHERE user_id = ? ORDER BY finished """, [current_user]
    )
    streaks_stats = db.execute(
        """SELECT streak, beginning, ending FROM streaks WHERE user_id = ? ORDER BY streak DESC""", [current_user]
    )
    rows = current_stats.fetchall()
    streaks_rows = streaks_stats.fetchall()
    count_wins = 0
    guess_list = []
    # i = index, row = val
    guess_dict = dict.fromkeys(["1", "2", "3", "4", "5", "6", "fail"], 0)
    for row in rows:
        if str(row[0]) in guess_dict and row[1] == 1:
            guess_dict[str(row[0])] = guess_dict.get(str(row[0])) + 1
            guess_list.append(row[0])
            count_wins = count_wins + 1
        else:
            guess_dict["fail"] = guess_dict.get("fail") + 1

    max_streaks = 0
    current_streaks = 0
    current = datetime.fromisoformat(current_date)
    if len(streaks_rows) != 0:
        for s_row in streaks_rows:
            starting = datetime.fromisoformat(s_row[1])
            ending = datetime.fromisoformat(s_row[2])
            if starting < current < ending:
                current_streaks = s_row[0]
        max_streaks = streaks_rows[0][0]

    guess_list.sort()
    mid = int((len(guess_list) - 1) / 2)
    stats_data = {
        "current_streak": current_streaks,
        "max_streak": max_streaks,
        "guesses": guess_dict,
        "win_percentage": (count_wins / len(rows)) * 100,
        "games_played": len(rows),
        "games_won": count_wins,
        "average_guesses": guess_list[mid]
    }
    stats: UserStats = UserStats(**stats_data)
    return {"game-statistics": stats}


@app.get("/top-wins-users/")
def game_stats(db: sqlite3.Connection = Depends(get_db)):
    top_users = db.execute(
        """
        SELECT 
            *
        FROM 
            wins 
        INNER JOIN users ON users.user_id = wins.user_id
        LIMIT 10;
        """
    )
    return{"Top 10 Users": top_users.fetchall()}


@app.get("/top-streaks-users")
def game_stats(db: sqlite3.Connection = Depends(get_db)):
    top_users = db.execute(
        """
        SELECT 
            *
        FROM 
            streaks
        INNER JOIN users ON users.user_id = streaks.user_id
        ORDER BY
            streak DESC
        LIMIT 10;
        """
    )
    return {"Top 10 Users": top_users.fetchall()}

