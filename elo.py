import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta

# Constants
DEFAULT_ELO = 1500
K_FACTOR_TABLE = {
    2: 22,
    3: 26,
    4: 30,
    5: 36,
    6: 40,
    7: 44,
    8: 48,
    9: 52,
    10: 56
}

def polynomial_score(position, num_players, curve=1):
    normalized = (position - 1) / (num_players - 1)
    return 1 - normalized**curve

def normalize_score(score_table: list) -> list:
    zero_sum_score_target = len(score_table) / 2
    scale_factor = zero_sum_score_target / sum(score_table)
    return [scale_factor * score for score in score_table]

def get_score_table(num_players, relation: str, **kwargs) -> list:
    assert relation in ['polynomial'], "must be one of ['polynomial']"
    if relation == 'polynomial':
        score_table = normalize_score([polynomial_score(i + 1, num_players, **kwargs) for i in range(num_players)])
        return {i + 1: score_table[i] for i in range(num_players)}

# File storage
ELO_FILE = "elo_history.json"

def load_data():
    """Loads all data from JSON file"""
    if os.path.exists(ELO_FILE):
        try:
            with open(ELO_FILE, "r") as f:
                data = json.load(f)
                # Ensure the data structure has both elo and rank
                if "elo" not in data:
                    data["elo"] = defaultdict(dict)
                if "rank" not in data:
                    data["rank"] = {}
                return data
        except (json.JSONDecodeError, IOError):
            return {"elo": defaultdict(dict), "rank": {}}
    return {"elo": defaultdict(dict), "rank": {}}

def load_elo():
    """Loads all ELO history and returns the latest ratings for each player"""
    data = load_data()
    history = data["elo"]
    current_elo = {}
    for player in history:
        if history[player]:  # Check if player has any history
            latest_timestamp = sorted(history[player].keys())[-1]
            current_elo[player] = history[player][latest_timestamp]
    return current_elo

def save_data(data):
    """Saves complete data structure to file"""
    with open(ELO_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_elo(elo_data, participants=None, timestamp=None):
    """Saves current ELO ratings with timestamp, only updating participants if specified"""
    data = load_data()
    timestamp = timestamp if timestamp else datetime.now().isoformat()

    if participants is None:
        # Update all players (for init/reset cases)
        for player, rating in elo_data.items():
            if player not in data["elo"].keys():
                data["elo"][player] = {}
            data["elo"][player][timestamp] = round(rating, 1)
    else:
        # Only update participating players
        for player in participants:
            if player in elo_data:
                if player not in data["elo"].keys():
                    data["elo"][player] = {}
                data["elo"][player][timestamp] = round(elo_data[player], 1)

    # Store rank information if provided
    if participants is not None:
        data["rank"][timestamp] = participants

    save_data(data)

def init_players():
    """Initialize new players with default ELO"""
    elo = load_elo()
    print("Enter player IDs (one per line, enter 'EOF' to finish):")
    while True:
        player_id = input().strip().lower()
        if player_id.upper() == "EOF":
            break
        if player_id:
            if player_id not in elo:
                elo[player_id] = DEFAULT_ELO
                print(f"Added {player_id} (ELO: {DEFAULT_ELO})")
            else:
                print(f"{player_id} already exists (ELO: {elo[player_id]})")
    save_elo(elo)
    print("Initialization complete.")

def delete_player(player_name):
    """Delete a player's ELO history"""
    data = load_data()
    player_name = player_name.lower()

    if player_name in data["elo"]:
        del data["elo"][player_name]
        save_data(data)
        print(f"Deleted player {player_name} from history.")
    else:
        print(f"No records found for player {player_name}.")

def display_elo():
    """Displays current ELO rankings with games played"""
    current_elo = load_elo()
    history = load_data()["elo"]

    if not current_elo:
        print("No players initialized.")
        return

    # Count games played for each player
    games_played = {player: len(timestamps) - 1 for player, timestamps in history.items()}

    # Sort players by ELO (descending)
    sorted_players = sorted(current_elo.items(), key=lambda x: (-x[1], x[0]))

    print("\n     Current ELO Rankings:")
    print("     -------------------")
    print(f"     {'Player'.ljust(10)} {'ELO'.ljust(9)} Games")
    print(f"{'     ------'.ljust(15)} {'---'.ljust(9)} -----")
    for pos, (player, rating) in enumerate(sorted_players):
        print(f"({str(pos + 1).ljust(2)}) {(player + ':').ljust(10)} {rating:.1f}".ljust(26) + str(games_played.get(player, 0)))
    print()

def display_player_history(player_name):
    """Displays ELO history for a specific player"""
    data = load_data()
    player_name = player_name.lower()
    if player_name not in data["elo"]:
        print(f"No records found for player {player_name}")
        return

    print(f"\nELO History for {player_name}:")
    print("Date                  ELO")
    print("--------------------- ---------")

    for timestamp in sorted(data["elo"][player_name].keys()):
        date_str = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
        print(f"{date_str}   {data['elo'][player_name][timestamp]:.1f}")

def reset_players():
    """Reset all players to default ELO"""
    data = load_data()
    if data.get("rank", {}):
        timestamp = (datetime.fromisoformat(next(iter(data["rank"]))) - timedelta(hours=1)).isoformat()
    else:
        timestamp = datetime.now().isoformat()

    for player in data["elo"]:
        data["elo"][player] = {timestamp: DEFAULT_ELO}  # Clear history and set to default

    save_data(data)
    print("Reset all player ELO to 1500.0")

def update_elo(order_of_finish: list = None, timestamp=None):
    """Update ELO ratings based on game results"""
    elo = load_elo()
    if not elo:
        print("No players initialized. Run `python main.py --init` first.")
        return

    print("Enter player id in finishing sequence (enter 'EOF' to finish):")
    entries = []
    if not order_of_finish:
        while True:
            entry = input().strip().lower()
            if entry.upper() == "EOF":
                break
            if entry:
                if entry in elo:
                    if entry not in entries:
                        entries.append(entry)
                else:
                    print(f"Player '{entry}' does not exist. Run 'python main.py --init' to add new players.")
    else:
        entries = order_of_finish

    if not entries:
        print("No results entered.")
        return

    num_players = len(entries)
    performance_scores = get_score_table(num_players, relation='polynomial', curve=0.5)

    # Calculate ELO changes
    elo_changes = defaultdict(float)
    for i, player in enumerate(entries):
        rank = i + 1
        actual_score = performance_scores.get(rank, 0.0)
        expected_score = sum(
            1 / (1 + 10 ** ((elo[opponent] - elo[player]) / 400))
            for opponent in entries if opponent != player
        ) / (num_players - 1)
        elo_changes[player] = K_FACTOR_TABLE[len(entries)] * (actual_score - expected_score)

    # Apply changes
    print("\nELO Changes:")
    print("------------")
    for pos, (player, change) in enumerate(elo_changes.items()):
        elo[player] += change
        print(f"({pos + 1}) {(player + ':').ljust(16)} {elo[player]:.1f} [{f'+{change:.1f}' if change >= 0 else f'{change:.1f}'}]")

    save_elo(elo, entries, timestamp=timestamp)
    print("\nRatings updated.")

def rebuild_elo():
    """Rebuild ELO ratings from match history"""
    data = load_data()

    if not data["rank"]:
        print("No match history found to rebuild from.")
        return

    print("Resetting all ELO ratings and rebuilding from match history...")

    reset_players()
    for timestamp in data["rank"]:
        update_elo(data["rank"][timestamp], timestamp=timestamp)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Texas Hold'em ELO Tracker")
    parser.add_argument("--init", action="store_true", help="Initialize new players")
    parser.add_argument("--reset", action="store_true", help="Reset all player ELOs to default")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild ELO ratings from match history")
    parser.add_argument("-c", "--current", action="store_true", help="Display current ELO rankings")
    parser.add_argument("-p", "--player", help="Display ELO history for specific player")
    parser.add_argument("-d", "--delete_player", help="Delete a player history")
    args = parser.parse_args()

    if args.init:
        init_players()
    elif args.reset:
        reset_players()
    elif args.rebuild:
        rebuild_elo()
    elif args.current:
        display_elo()
    elif args.player:
        display_player_history(args.player)
    elif args.delete_player:
        delete_player(args.delete_player)
    else:
        update_elo()
