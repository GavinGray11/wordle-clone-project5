import json
import logging.config
import sqlite3
import contextlib
import redis
from fastapi import FastAPI, Depends, Response, HTTPException, status, Request
from pydantic import BaseModel, BaseSettings
import httpx

class Settings(BaseSettings):
    stats_database: str
    stats_database_s1: str
    stats_database_s2: str
    stats_database_s3: str
    user_database: str
    logging_config: str

    class Config:
        env_file = ".env"


def get_db():
    with contextlib.closing(sqlite3.connect(settings.user_database)) as db:
        db.row_factory = sqlite3.Row
        yield db


def get_logger():
    return logging.getLogger(__name__)


settings = Settings()
app = FastAPI()
db = redis.Redis(host="localhost", port=6379)


@app.get("/app")
def read_main(request: Request):
    return {"message": "Hello World", "root_path": request.scope.get("root_path")}


@app.post("/start-new-game")
def start_game(current_user: int, current_game: int):
    # insert into the redis database first, key would be current user and game, init the list and counter
    #db.flushall()
    delim: str = ":"
    cur_id = f"{current_user}{delim}{current_game}"
    guess_list = f"{cur_id}{delim}guessList"
    count = f"{cur_id}{delim}counter"
    if db.exists(guess_list) or db.exists(count):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Already exists"
        )
    else:
        db.lpush(guess_list, "", "", "", "", "", "NOSQLStores")
        db.set(count, 0)
    cur = db.lrange(guess_list, 0, -1)
    cur_count = db.get(count)
    return {"current_id": cur_id, "list": cur, "counter": cur_count}


@app.put("/update-game/{current_game}")
def update_game(current_user: int, current_game: int, guess_word: str):
    delim: str = ":"
    cur_id = f"{current_user}{delim}{current_game}"
    guess_list = f"{cur_id}{delim}guessList"
    count = f"{cur_id}{delim}counter"
    if not db.exists(guess_list) or not db.exists(count):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND"
        )
    num = int(db.get(count).decode())
    if num < 6:
        db.lset(guess_list, num, guess_word)
        db.incr(count)
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="reach the limit"
        )
    cur = db.lrange(guess_list, 0, -1)
    cur_count = db.get(count)
    return {"current_id": cur_id, "guesses": cur, "current guesses": cur_count}


@app.get("/get-state-game/")
def get_state_game(current_user: int, current_game: int):
    delim: str = ":"
    cur_id = f"{current_user}{delim}{current_game}"
    guess_list = f"{cur_id}{delim}guessList"
    count = f"{cur_id}{delim}counter"
    if not db.exists(guess_list) or not db.exists(count):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND"
        )
    cur = db.lrange(guess_list, 0, -1)
    cur_count = db.get(count)
    return {"current_id": cur_id, "guess-list": cur, "guess-count": cur_count}


@app.get("/get-user-id")
def get_user_id(current_user: str, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT user_id FROM users WHERE username = ?", (current_user,))
    rows = cur.fetchall()


    return rows
