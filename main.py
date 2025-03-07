from inquirer import Text, prompt, List, Checkbox
import requests_cache
import json
from enum_items import Item

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
            print(f'Selected {pokemon['name']}')
            if pokemon:
                team.append({
                    "id": pokemon['id'],
                    "name": pokemon["name"],
                    "types": format_types(pokemon),
                    "stats": format_stats(pokemon),
                    "nature": select_nature(),
                    "evs": set_evs(),
                    "ivs": set_ivs(),
                    "level": set_level(),
                    "moves": select_moves(pokemon),
                    "ability": select_ability(pokemon),
                    "held_item": select_held_item(),
                })
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
    item_array = []
    for i in Item:
        item_array.append(i.name)
        print(i.name)
    
    questions = [
        List(name="held_item", message="Select an Item for your Pokémon to hold", choices=item_array)
    ]
    answers = prompt(questions)
    return answers['held_item']



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


pokemon_natures = {
    'hardy': {},
    'lonely': {'UP': 'attack', 'DOWN': 'defense'},
    'brave': {'UP': 'attack', 'DOWN': 'speed'},
    'adamant': {'UP': 'attack', 'DOWN': 'special-attack'},
    'naughty': {'UP': 'attack', 'DOWN': 'special-defense'},
    'bold': {'UP': 'defense', 'DOWN': 'attack'},
    'docile': {},
    'relaxed': {'UP': 'defense', 'DOWN': 'speed'},
    'impish': {'UP': 'defense', 'DOWN': 'special-attack'},
    'lax': {'UP': 'defense', 'DOWN': 'special-defense'},
    'timid': {'UP': 'speed', 'DOWN': 'attack'},
    'hasty': {'UP': 'speed', 'DOWN': 'defense'},
    'serious': {},
    'jolly': {'UP': 'speed', 'DOWN': 'special-attack'},
    'naive': {'UP': 'speed', 'DOWN': 'special-defense'},
    'modest': {'UP': 'special-attack', 'DOWN': 'attack'},
    'mild': {'UP': 'special-attack', 'DOWN': 'defense'},
    'quiet': {'UP': 'special-attack', 'DOWN': 'speed'},
    'bashful': {},
    'rash': {'UP': 'special-attack', 'DOWN': 'special-defense'},
    'calm': {'UP': 'special-defense', 'DOWN': 'attack'},
    'gentle': {'UP': 'special-defense', 'DOWN': 'defense'},
    'sassy': {'UP': 'special-defense', 'DOWN': 'speed'},
    'careful': {'UP': 'special-defense', 'DOWN': 'special-attack'},
    'quirky': {}
}


def set_level():
    questions = [
        Text(name='level', message='Set the level for your Pokémon (1-100)',
             validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 100)
    ]
    answers = prompt(questions)
    return int(answers['level'])


def select_nature():
    natures = list(pokemon_natures.keys())
    questions = [
        List(name="nature", message="Select a nature for your Pokémon", choices=natures)
    ]
    answers = prompt(questions)
    return answers['nature']


def save_team(team):
    questions = [
        Text(name='name', message='Please name your team.')
    ]
    answers = prompt(questions)
    with open(f'out/{answers["name"]}.json', 'w') as f:
        json.dump(team, f, indent=2)


if __name__ == '__main__':
    main()
