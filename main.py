from inquirer import Text, prompt, List, Checkbox
import requests_cache

BASE_URL = "https://pokeapi.co/api/v2"


def main():
    questions = [
        Text(name="team_size", message="How many Pokemon on your team? (1-6)",
             validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 6),
    ]
    answers = prompt(questions)
    team_size = int(answers['team_size'])

    team = []
    for i in range(team_size):
        while True:
            questions = [
                Text(name=f"pokemon_{i + 1}", message=f"Which Pokemon do you want for slot {i + 1} (ID/name)?"),
            ]
            pokemon_answer = prompt(questions)
            pokemon = get_pokemon(pokemon_answer[f"pokemon_{i + 1}"])
            if pokemon:
                ability = select_ability(pokemon)
                moves = select_moves(pokemon)
                team.append({"name": pokemon["name"], "moves": moves, "ability": ability})
                break
            else:
                print(f"Invalid Pokemon name/ID: {pokemon_answer[f'pokemon_{i + 1}']}. Please try again.")

    print(f"Your team: {team}")


def get_pokemon(pokemon_id):
    print(f"Query with {pokemon_id}")
    response = requests_cache.CachedSession().get(f"{BASE_URL}/pokemon/{pokemon_id}")
    print(response.status_code)

    if response.status_code != 200:
        return None

    return response.json()


def select_moves(pokemon):
    moves = [(move["move"]["name"], move["move"]) for move in pokemon["moves"] if
             any(version["version_group"]["name"] == "scarlet-violet" for version in move["version_group_details"])]
    questions = [
        Checkbox(name="moves", message=f"Select 1-4 moves for {pokemon['name']}", choices=moves,
                 validate=lambda _, x: 1 <= len(x) <= 4),
    ]
    answers = prompt(questions)
    return [get_move_info(move) for move in answers["moves"]]


def get_move_info(move):
    move_response = requests_cache.CachedSession().get(move['url'])

    if move_response.status_code != 200:
        return None
    move_info = move_response.json()

    return {
        "id": move_info['id'],
        "name": move_info['name'],
        "power": move_info['power'],
        "pp": move_info['pp'],
        "priority": move_info['priority'],
        "accuracy": move_info['accuracy'],
        "damage_class": move_info['damage_class']['name'],
        "meta": move_info['meta'],
        "stat_changes": move_info['stat_changes'],
        "target": move_info['target']['name'],
        "type": move_info['type']['name']
    }


def select_ability(pokemon):
    abilities = [(ability["ability"]["name"], ability["ability"]) for ability in pokemon["abilities"]]
    questions = [
        List(name="ability", message=f"Select an ability for {pokemon['name']}", choices=abilities)
    ]
    answers = prompt(questions)
    return answers["ability"]


def select_held_item():
    pass


if __name__ == '__main__':
    main()
