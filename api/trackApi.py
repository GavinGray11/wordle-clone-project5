import logging.config
import sqlite3
import contextlib
import redis
from fastapi import FastAPI, Depends, Response, HTTPException, status, Request
from pydantic import BaseModel, BaseSettings
import uuid
from datetime import datetime
DATABASE_user = './var/user.db'
# connect database setting from .env file
# convert data from stats.db to populated.sql
# sqlite3 ./var/stats.db .dump > ./share/track/populated.sql


class Settings(BaseSettings):
    stats_database: str
    stats_database_s1: str
    stats_database_s2: str
    stats_database_s3: str
    user_database: str
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
    with contextlib.closing(sqlite3.connect(settings.user_database)) as db:
        db.row_factory = sqlite3.Row
        yield db
# use for debug the code


def get_logger():
    return logging.getLogger(__name__)


settings = Settings()
app = FastAPI()
    # servers=[{"url": "http://127.0.0.1:9999/api/v1/docs", "description": "dictionary"},
    # {"url": "http://127.0.0.1:9999/answers/v2", "description": "guesses"},
    # {"url": "http://127.0.0.1:9999/track/v3", "description": "track stats"}]


@app.get("/app")
def read_main(request: Request):
    return {"message": "Hello World", "root_path": request.scope.get("root_path")}

logging.config.fileConfig(settings.logging_config)
# getting all the word from the word_list database and display


@app.post("/game-result/{current_user}", status_code=status.HTTP_201_CREATED)
def post_result(current_user: int, game: GameResult, response: Response, db: sqlite3.Connection = Depends(get_db)):
    sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
    sqlite3.register_adapter(uuid.UUID, lambda u: u.bytes_le)
    if int(current_user) % 3 == 0:
        db.execute("ATTACH './var/stats_s1.db' as stats")
    elif int(current_user) % 3 == 1:
        db.execute("ATTACH './var/stats_s2.db' as stats")
    else:
        db.execute("ATTACH './var/stats_s3.db' as stats")

    cur = db.execute("SELECT user_uuid FROM users WHERE user_id = ?", [current_user])
    uid = cur.fetchone()[0]
    g = dict(game)
    g.update({"user_id": current_user})
    g.update({"user_uuid": uid})
    try:
        # first find the uuid from the user table and then transfer to games table
        add_game = db.execute(
            """
            INSERT INTO stats.games(user_uuid, user_id, game_id, finished, guesses, won)
            VALUES(:user_uuid, :user_id, :game_id, :finished, :guesses, :won)
            """, g
        )
        db.commit()

    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(error).__name__, "msg": str(error)}
        )
    g["id"] = add_game.lastrowid
    g["user_uuid"] = str(uid)
    response.headers["Location"] = f"/game-result/{g['id']}"
    return g


@app.get("/wordle-statistics/{current_user}/{current_date}")
def game_stats(current_user: int, current_date: str, db: sqlite3.Connection = Depends(get_db)):
    # find the uuid using the user id from the user table and then find it from the game table
    sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
    sqlite3.register_adapter(uuid.UUID, lambda u: u.bytes_le)
    if int(current_user) % 3 == 0:
        db.execute("ATTACH './var/stats_s1.db' as stats")
    elif int(current_user) % 3 == 1:
        db.execute("ATTACH './var/stats_s2.db' as stats")
    else:
        db.execute("ATTACH './var/stats_s3.db' as stats")

    cur = db.execute("SELECT user_uuid FROM users WHERE user_id = ?", [current_user])
    uid = cur.fetchone()[0]

    current_stats = db.execute(
        """SELECT guesses,won FROM stats.games WHERE user_uuid = ? ORDER BY finished """, [uid]
    )
    streaks_stats = db.execute(
        """SELECT streak, beginning, ending FROM stats.streaks WHERE user_uuid = ? ORDER BY streak DESC""", [uid]
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
def win_stats(db: sqlite3.Connection = Depends(get_db)):
    db = redis.Redis(host="localhost", port=6379)
    curr = db.zrevrange("Top-wins", 0, 9, withscores=True)
    res = []
    for user in curr:
        res.append({'username': user[0], 'wins': user[1]})
    return {"Top-10 Users": res}


@app.get("/top-streaks-users")
def streak_stats(db: sqlite3.Connection = Depends(get_db)):
    db = redis.Redis(host="localhost", port=6379)
    curr = db.zrevrange("Top-streaks", 0, 9, withscores=True)
    res = []
    for user in curr:
        res.append({'username': user[0], 'streaks': user[1]})
    return {"Top-10 Users": res}
