import json
import logging.config
import contextlib
from fastapi import FastAPI, Depends, Response, HTTPException, status, Request
from pydantic import BaseModel, BaseSettings
import httpx
import asyncio
from random import randint
from fastapi.testclient import TestClient
from trackApi import app
client = TestClient(app)
from datetime import date



app = FastAPI()

@app.get("/current-words")
def read_main(request: Request):
    r = httpx.get('http://127.0.0.1:5200/list-words/')
    r.json()
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
def check_guess(list_letter_color, user_guess):
    letter_dict = {}
    correct_list = []
    present_list = []
    pos = 0
    for item in list_letter_color:
        if item == 'Green':
            correct_list.append(user_guess[pos])
        elif item == 'Yellow':
            present_list.append(user_guess[pos])
        else:
            print("All Letters Guessed Incorrect")
        pos +=1
    letter_dict["correct"] = correct_list
    letter_dict["present"] = present_list
    return letter_dict

def calculate_score(score_dict):

    correct_score = len(score_dict["correct"]) * 100
    present_score = len(score_dict["present"]) * 50

    score = correct_score + present_score
    return score

@app.post("/game/new")
def new_game(current_user: str):
    params = {'current_user': current_user}
    r = httpx.get('http://127.0.0.1:5000/get-user-id', params=params)
    json_object = r.json()
    dict_value = json_object[0]
    users_id = dict_value['user_id']
    game_id =  randint(0, 1000000000)
    params = {'current_user': users_id, 'current_game': game_id}
    with httpx.Client(params=params) as client:
        grab_userid = client.put('http://127.0.0.1:5000/get-user-id',data={'key': 'current_user'})
        r = client.post('http://127.0.0.1:5000/start-new-game',params=params)
    return {"status": "new", "user_id": users_id, "game_id": game_id}

@app.get("/game/{game_id}")
def game_progress(user_id: int, guess: str, game_id: int):

    # step 1: check the guess is a word in the word list_word
    total_scores = 0
    validate_guess = httpx.get(f'http://127.0.0.1:5200/validate-guess/{guess}')
    valid_guess = validate_guess.json()
    if not valid_guess['validGuess']:
        return {"400 bad request"}
    # step 2: check that the user has guesses remaining
    params = {'current_user': user_id, 'current_game': game_id}
    game_state = httpx.get('http://127.0.0.1:5000/get-state-game/', params=params)
    game_dict = game_state.json()
    guess_amount = game_dict['guess-count']
    if guess_amount != '6':
    #########IF BOTH STEPS 1 AND 2 ARE TRUE -> move on to step 3
        if not valid_guess['validGuess']:
            return {"400 bad request"}
    # step 3: Record the guess and update the number of guesses remaining.
        r = httpx.put(f'http://127.0.0.1:5000/update-game/{game_id}?current_user={user_id}&guess_word={guess}')
        json_object = r.json()
        guess_remaining = 5-int(guess_amount)
        json_object["remaining"] = guess_remaining
        # step 4: check to see if guess is correct.
        answer_req = httpx.get(f'http://127.0.0.1:5300/validate-answer/{guess}')
        word_dict = answer_req.json()
        word_list = word_dict['CompareAnswer']
        json_object["letters"] = check_guess(word_list, guess)
        ######### If the guess is incorrect and no guesses remain:
        json_object["status"] = "in progress"
        scores = calculate_score(check_guess(word_list, guess))
        json_object["score"] = scores
    ######### If it is correct:
    # step 5: record the win
        check_win = check_guess(word_list, guess)
        if len(check_win["correct"]) == 5:
            json_object["status"] = "win"
            statistics_req = httpx.get(f'http://127.0.0.1:5100/wordle-statistics/{user_id}/{str(date.today())}')
            # statistics_req = client.get(f'http://127.0.0.1:5100/wordle-statistics/', {'current_user': game_id, 'current_date': date.today()})
            # statistics_req = client.get(f'http://127.0.0.1:5100/wordle-statistics/{game_id}{date.today()}')
            win_json = statistics_req.json()
            win_json["status"] = "win"
            win_json["remaining"] = guess_remaining
            win_scores = calculate_score(check_guess(word_list, guess))
            win_json["score"] = win_scores
            return win_json
    ######### If the guess is incorrect and no guesses remain:
    # step 5: Record the loss
    # Step 6: Return the user’s score
    if guess_amount == '6':
        guess_remaining = 5-int(guess_amount)
        data = {"game_id": game_id, "finished": "yes", "guesses": 6, "won": 0}
        game_loss_post = client.post(f"http://127.0.0.1:5100/game-result/{user_id}", json=data)
        statistics_req_loss = httpx.get(f'http://127.0.0.1:5100/wordle-statistics/{user_id}/{str(date.today())}')
        loss_results = statistics_req_loss.json()
        loss_results["status"] = "loss"
        loss_results["remaining"] = guess_remaining
        loss_results["score"] = 0
        return loss_results

    return json_object
