from inquirer import Text, prompt, List, Checkbox
import requests_cache
import json

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
                Text(
                    name=f"pokemon_{i + 1}", message=f"Which Pokemon do you want for slot {i + 1} (ID/name)?"),
            ]
            pokemon_answer = prompt(questions)
            pokemon = get_pokemon(pokemon_answer[f"pokemon_{i + 1}"])
            if pokemon:
                ability = select_ability(pokemon)
                moves = select_moves(pokemon)
                team.append({"id": pokemon['id'], "name": pokemon["name"], "types": format_types(pokemon), "stats": format_stats(
                    pokemon), "evs": set_evs(), "ivs": set_ivs(), "moves": moves, "ability": ability})
                break
            else:
                print(
                    f"Invalid Pokemon name/ID: {pokemon_answer[f'pokemon_{i + 1}']}. Please try again.")

    save_team(team)


def get_pokemon(pokemon_id):
    print(f"Query with {pokemon_id}")
    response = requests_cache.CachedSession().get(
        f"{BASE_URL}/pokemon/{pokemon_id}")
    print(response.status_code)

    if response.status_code != 200:
        return None

    return response.json()


def format_stats(pokemon):
    return {stat['stat']['name']: stat['base_stat'] for stat in pokemon['stats']}


def format_types(pokemon):
    return [t['type']['name'] for t in pokemon['types']]


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
    abilities = [(ability["ability"]["name"], ability["ability"])
                 for ability in pokemon["abilities"]]
    questions = [
        List(name="ability",
             message=f"Select an ability for {pokemon['name']}", choices=abilities)
    ]
    answers = prompt(questions)
    return get_ability_info(answers['ability'])


def get_ability_info(ability):
    ability_response = requests_cache.CachedSession().get(ability['url'])

    if ability_response.status_code != 200:
        return None
    ability_info = ability_response.json()

    effect_entries = [
        entry for entry in ability_info['effect_entries']
        if entry['language']['name'] == 'en'
    ]

    effect_changes = [
        {
            "effect_entries": [
                entry for entry in change['effect_entries']
                if entry['language']['name'] == 'en'
            ],
            "version_group": change['version_group']
        }
        for change in ability_info['effect_changes']
    ]

    return {
        "id": ability_info['id'],
        "name": ability_info['name'],
        "effect_entries": effect_entries,
        "effect_changes": effect_changes,
    }


def select_held_item():
    pass


def set_ivs():
    MAX_IV = 31
    ivs = {
        'hp': 0,
        'attack': 0,
        'defense': 0,
        'special-attack': 0,
        'special-defense': 0,
        'speed': 0
    }

    for stat in ivs.keys():
        questions = [
            Text(name='iv', message=f'How many IV points do you want to invest in {stat}? (0-{MAX_IV})', validate=lambda _, x: x.isdigit(
            ) and 0 <= int(x) <= MAX_IV)
        ]
        answers = prompt(questions)
        ivs[stat] = int(answers['iv'])

    return ivs


def set_evs():
    MAX_EVS = 508  # Actual maximum is 510 but due to EVs incrementing a stat every 4 points the effective max is 508
    MAX_STAT_EV = 252
    invested_evs = 0
    evs = {
        'hp': 0,
        'attack': 0,
        'defense': 0,
        'special-attack': 0,
        'special-defense': 0,
        'speed': 0
    }

    while invested_evs < MAX_EVS:
        for stat in evs.keys():
            remaining_evs = MAX_EVS - invested_evs
            questions = [
                Text(name='ev', message=f'How many EV points do you want to invest in {stat}? (0-{min(MAX_STAT_EV, remaining_evs)}) \nAvailable EVs remaining {remaining_evs}', validate=lambda _, x: x.isdigit(
                ) and 0 <= int(x) <= min(MAX_STAT_EV, remaining_evs))
            ]
            answers = prompt(questions)
            ev = int(answers['ev'])

            if invested_evs + ev > MAX_EVS:
                print(
                    f"Total EVs cannot exceed {MAX_EVS}. You have {remaining_evs} EVs remaining.")
                continue

            evs[stat] += ev
            invested_evs += ev

            if invested_evs >= MAX_EVS:
                break

    return evs


def save_team(team):
    questions = [
        Text(name='name', message='Please name your team.')
    ]
    answers = prompt(questions)
    with open(f'out/{answers["name"]}.json', 'w') as f:
        json.dump(team, f, indent=2)


if __name__ == '__main__':
    main()
