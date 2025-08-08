import random

game_state = {}
correct_word_score = 10



def gen_word():
    words = ["Watermelon", "Kangaroo", "Jurassic", "Monster", "Malevolent", "Situational", "Motivational", "Iceberg", "Eclipse", "Outrageous"]
    return random.choice(words)

def start_game(room):
    game_state[room] = {
        "word": gen_word(),
        "attempts_left": 5,
        "scores": {},
        "guessed": False,
        "winner": None
    }
    return {
        "action": "game_update",
        "room": room,
        "message": "New word selected! Start guessing!",
        "attempts_left": game_state[room]["attempts_left"]
    }

def process_guess(room, username, guess):
    if room not in game_state:
        return {"action": "error", "message": f"Room {room} has no active game!"}
    
    state = game_state[room]
    if state["guessed"] or state["attempts_left"] == 0:
        return {"action": "game_update", "message": "Round is over! Start a new game.", "attempts_left": 0}

    if username not in state["scores"]:
        state["scores"][username] = 0
    
    if guess.lower() == state["word"].lower():
        state["guessed"] = True
        state["scores"][username] += correct_word_score
        if state["scores"][username] >= 50:
            state["winner"] = username
            return {
                "action": "game_win",
                "room": room,
                "message": f"{username} wins the game with {state['scores'][username]} points!",
                "word": state["word"],
                "scores": state["scores"]
            }
        state["word"] = gen_word()
        state["attempts_left"] = 10
        state["guessed"] = False
        return {
            "action": "game_update",
            "room": room,
            "message": f"Correct! {username} guessed the word. New word selected!",
            "attempts_left": state["attempts_left"],
            "scores": state["scores"]
        }
    else:
        state["attempts_left"] -= 1
        if state["attempts_left"] <= 0:
            return {
                "action": "game_update",
                "room": room,
                "attempts_left": 0,
                "message": f"Out of attempts! The word was {state['word']}. New word selected!",
                "scores": state["scores"]
            }
        return {
            "action": "game_update",
            "room": room,
            "attempts_left": state["attempts_left"],
            "message": f"{guess} is incorrect",
            "scores": state["scores"]
        }

def get_game_state(room):
    if room in game_state:
        return {
            "action": "game_state",
            "room": room,
            "word": game_state[room]['word'],
            "attempts_left": game_state[room]["attempts_left"],
            "scores": game_state[room]["scores"],
            "guessed": game_state[room]["guessed"],
            "winner": game_state[room]["winner"]
        }
    return {"action": "error", "message": f"No game in room {room}"}