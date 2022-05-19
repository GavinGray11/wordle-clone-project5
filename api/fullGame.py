import json
import logging.config
import contextlib
from fastapi import FastAPI, Depends, Response, HTTPException, status, Request
from pydantic import BaseModel, BaseSettings
import httpx
import asyncio
from random import randint



app = FastAPI()

@app.get("/current-words")
def read_main(request: Request):
    r = httpx.get('http://127.0.0.1:5200/list-words/')
    r.json()
    print(r.json())
    return r.json()
#
# @app.post("/start-new-game")
# def start_game(current_user: int, current_game: int):
#     # insert into the redis database first, key would be current user and game, init the list and counter
#     #db.flushall()
#     delim: str = ":"
#     cur_id = f"{current_user}{delim}{current_game}"
#     guess_list = f"{cur_id}{delim}guessList"
#     count = f"{cur_id}{delim}counter"
#     if db.exists(guess_list) or db.exists(count):
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT, detail="Already exists"
#         )
#     else:
#         db.lpush(guess_list, "", "", "", "", "", "NOSQLStores")
#         db.set(count, 0)
#     cur = db.lrange(guess_list, 0, -1)
#     cur_count = db.get(count)
#     return {"current_id": cur_id, "list": cur, "counter": cur_count}


@app.post("/game/new")
def new_game(current_user: str):
    params = {'current_user': current_user}
    r = httpx.get('http://127.0.0.1:5000/get-user-id', params=params)
    print(r)
    print(r.text)
    print(r.json())
    json_object = r.json()
    dict_value = json_object[0]
    users_id = dict_value['user_id']
    print(users_id)
    game_id =  randint(0, 1000000000)
    params = {'current_user': users_id, 'current_game': game_id}
    with httpx.Client(params=params) as client:
        grab_userid = client.put('http://127.0.0.1:5000/get-user-id',data={'key': 'current_user'})
        r = client.post('http://127.0.0.1:5000/start-new-game',params=params)
    print(r.json())
    return {"status": "new", "user_id": users_id, "game_id": game_id}

@app.get("/game/{game_id}")
def game_progress(user_id: int, guess: str):

    # step 1: check the guess is a word in the word list_word

    # step 2: check that the user has guesses remaining

    #########IF BOTH STEPS 1 AND 2 ARE TRUE -> move on to step 3

    # step 3: Record the guess and update the number of guesses remaining.

    # step 4: check to see if guess is correct.

    ######### If it is correct:

    # step 5: record the win

    # Step 6: return the users score

    ######### If the guess is incorrect and no guesses remain:

    # step 5: Record the loss

    # Step 6: Return the user’s score

    ######### If the guess is incorrect and additional guesses remain:

    # step 5: Return which letters are included in the word and which are correctly placed





    r = httpx.get("http://127.0.0.1:5100/wordle-statistics/{current_user}/{current_date}")
    r.json()
    print(r.json())
    return r.json()
