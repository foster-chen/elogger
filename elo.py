import argparse
import json
import os
from collections import defaultdict
from datetime import datetime

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
    9: 52
}
PERFORMANCE_SCORES = {
    2: {1: 1.0, 2: 0.0},
    3: {1: 1.0, 2: 0.5, 3: 0.0},
    4: {1: 1.0, 2: 0.6, 3: 0.3, 4: 0.0},
    5: {1: 1.0, 2: 0.7, 3: 0.4, 4: 0.2, 5: 0.0},
    6: {1: 1.0, 2: 0.75, 3: 0.5, 4: 0.3, 5: 0.15, 6: 0.0},
    7: {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.25, 6: 0.1, 7: 0.0},
    8: {1: 1.0, 2: 0.8, 3: 0.65, 4: 0.5, 5: 0.35, 6: 0.2, 7: 0.1, 8: 0.0},
    9: {1: 1.0, 2: 0.85, 3: 0.7, 4: 0.55, 5: 0.4, 6: 0.3, 7: 0.15, 8: 0.05, 9: 0.0},
}

# File storage
ELO_FILE = "elo_history.json"

def load_elo():
    """Loads all ELO history and returns the latest ratings for each player"""
    history = load_full_history()
    current_elo = {}
    for player in history:
        if history[player]:  # Check if player has any history
            latest_timestamp = sorted(history[player].keys())[-1]
            current_elo[player] = history[player][latest_timestamp]
    return current_elo

def load_full_history():
    """Loads complete ELO history with player-centric structure"""
    if os.path.exists(ELO_FILE):
        try:
            with open(ELO_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return defaultdict(dict)
    return defaultdict(dict)

def save_elo(elo_data, participants=None):
    """Saves current ELO ratings with timestamp, only updating participants if specified"""
    history = load_full_history()
    timestamp = datetime.now().isoformat()
    
    if participants is None:
        # Update all players (for init/reset cases)
        for player, rating in elo_data.items():
            if player not in history.keys():
                history[player] = {}
            history[player][timestamp] = round(rating, 1)
    else:
        # Only update participating players
        for player in participants:
            if player in elo_data:
                if player not in history.keys():
                    history[player] = {}
                history[player][timestamp] = round(elo_data[player], 1)
    
    with open(ELO_FILE, "w") as f:
        json.dump(history, f, indent=2)

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
    history = load_full_history()
    player_name = player_name.lower()
    
    if player_name in history:
        del history[player_name]
        with open(ELO_FILE, "w") as f:
            json.dump(history, f, indent=2)
        print(f"Deleted player {player_name} from history.")
    else:
        print(f"No records found for player {player_name}.")

def display_elo():
    """Displays current ELO rankings with games played"""
    current_elo = load_elo()
    history = load_full_history()
    
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
    history = load_full_history()
    player_name = player_name.lower()
    if player_name not in history:
        print(f"No records found for player {player_name}")
        return
    
    print(f"\nELO History for {player_name}:")
    print("Date                  ELO")
    print("--------------------- ---------")
    
    for timestamp in sorted(history[player_name].keys()):
        date_str = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
        print(f"{date_str}   {history[player_name][timestamp]:.1f}")

def reset_players():
    """Reset all players to default ELO"""
    history = load_full_history()
    timestamp = datetime.now().isoformat()
    
    for player in history:
        history[player] = {timestamp: DEFAULT_ELO}  # Clear history and set to default
    
    with open(ELO_FILE, "w") as f:
        json.dump(history, f, indent=2)
    print("Reset all player ELO to 1500.0")

def update_elo():
    """Update ELO ratings based on game results"""
    elo = load_elo()
    if not elo:
        print("No players initialized. Run `python main.py --init` first.")
        return

    print("Enter player id in finishing sequence (enter 'EOF' to finish):")
    entries = []
    participants = set()
    i = 1
    while True:
        entry = input().strip().lower()
        if entry.upper() == "EOF":
            break
        if entry:
            if entry in elo:
                entries.append((entry, i))
                participants.add(entry)
                i += 1
            else:
                print(f"Player '{entry}' does not exist. Run 'python main.py --init' to add new players.")

    if not entries:
        print("No results entered.")
        return

    num_players = len(entries)
    performance_scores = PERFORMANCE_SCORES.get(num_players, {})
    if not performance_scores:
        print(f"No performance scores defined for {num_players} players.")
        return

    # Calculate ELO changes
    elo_changes = defaultdict(float)
    for player, finish in entries:
        actual_score = performance_scores.get(finish, 0.0)
        expected_score = sum(
            1 / (1 + 10 ** ((elo[opponent] - elo[player]) / 400))
            for opponent, _ in entries if opponent != player
        ) / (num_players - 1)
        elo_changes[player] = K_FACTOR_TABLE[len(entries)] * (actual_score - expected_score)

    # Apply changes
    print("\nELO Changes:")
    print("------------")
    for pos, (player, change) in enumerate(elo_changes.items()):
        elo[player] += change
        print(f"({pos + 1}) {(player + ':').ljust(16)} {elo[player]:.1f} [{f'+{change:.1f}' if change >= 0 else f'{change:.1f}'}]")

    save_elo(elo, participants)
    print("\nRatings updated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Texas Hold'em ELO Tracker")
    parser.add_argument("--init", action="store_true", help="Initialize new players")
    parser.add_argument("--reset", action="store_true", help="Reset all player ELOs to default")
    parser.add_argument("-c", "--current", action="store_true", help="Display current ELO rankings")
    parser.add_argument("-p", "--player", help="Display ELO history for specific player")
    parser.add_argument("-d", "--delete_player", help="Delete a player history")
    args = parser.parse_args()

    if args.init:
        init_players()
    elif args.reset:
        reset_players()
    elif args.current:
        display_elo()
    elif args.player:
        display_player_history(args.player)
    elif args.delete_player:
        delete_player(args.delete_player)
    else:
        update_elo()