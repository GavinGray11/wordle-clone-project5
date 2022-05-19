# wordle-api
# CPSC 449 - Project 4: Microservice

Team Members:

Gavin Gray: graygavin11@csu.fullerton.edu

## Project Description
Created Project 3 with a python file that shards the stats database into three databases.
This project also implements traefik as a reverse-proxy and uses foreman to create three instances of the trackApi.


## Project Requirements
This project will run using Tuffix 2020 using Python 3.8.10 and will be implemented using fastapi and sqlite3.
require user install fastapi, ruby-foreman, sqlite3, and httpie, faker,

## Run the Program
### 1. install pip package installer and other tools:
    sudo apt update
    sudo apt install --yes python3-pip ruby-foreman httpie sqlite3 redis python3-hiredis

### 2. Install FastAPI:
    python3 -m pip install 'fastapi[all]'

### 3. Project 4 => Then run the command:
    ### To initialize the database, type:
        cd into the api folder directory wordle-project3/api
        ./bin/init_s1.sh
        ./bin/init_s2.sh
        python3 shard.py
    ### To start the uvicorn servers, type:
        foreman start -m api=1,answersApi=1,trackApi=3
    ### To start the Traefik files type:
        ./traefik --configFile=traefik.toml

### 4. Project 4 => Run the command:
      cd into the wordle-clone/api/bin
  ### Get sql data and transport to redis:
      python3 materialize.py
  ### crontab initialization for every 10 minutes:
      crontab -e
  ### copy this into the terminal:
      */10 * * * * cd /home/student/wordle-clone/api/bin/ && /usr/bin/python3 materialize.py >> check.log
  ### This will show the above command is working:
      crontab -l


api: uvicorn --port $PORT api:app --reload --root-path /api/v1
answers: uvicorn --port $PORT answersApi:app --reload --root-path /answers/v2
track: uvicorn --port $PORT trackApi:app --reload --root-path /track/v3
state: uvicorn --port $PORT currentState:app --reload --root-path /state/v4
