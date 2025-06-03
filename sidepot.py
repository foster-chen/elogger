from typing import Dict, List, Set, Tuple

class Pot:
    def __init__(self, amount: int, num_players: int, num_runs: int, players_eligible: set, is_sidepot: bool = False):
        self.amount = amount
        self.num_players = num_players
        self.num_runs = num_runs
        self.players_eligible = players_eligible
        self.is_sidepot = is_sidepot
        self.entitled_chips = [0 for _ in range(num_players)]
        self.entitled_chips_per_run = [[0 for _ in range(num_players)] for _ in range(num_runs)]

    def _verbose(self):
        print(f"\n{'Side' if self.is_sidepot else 'Main'} pot with {self.amount} chips, eligible to {self.players_eligible}")
        print("-" * (13 + self.num_players * 10))
        print(f"{'| Player ID'.ljust(11)} | ", end='')
        for i in range(self.num_players):
            message = f"{('Player ' + str(i) + ' ').ljust(10)}"
            if i not in self.players_eligible:
                message = '\033[90m' + message + '\033[0m'
            print(f"{message}", end='')
        print()
        for run_idx in range(self.num_runs):
            print(f"{('| Run ' + str(run_idx + 1)).ljust(11)} | ", end='')
            for i in range(self.num_players):
                message = f"{str(self.entitled_chips_per_run[run_idx][i]).ljust(10)}"
                if i not in self.players_eligible:
                    message = '\033[90m' + message + '\033[0m'
                print(message, end='')
            print()
        print('\033[90m' + "-" * (13 + self.num_players * 10) + '\033[0m')
        print(f"{'| Total'.ljust(11)} | ", end='')
        for i in range(self.num_players):
            message = f"{str(self.entitled_chips[i]).ljust(10)}"
            if i not in self.players_eligible:
                message = '\033[90m' + message + '\033[0m'
            print(message, end='')
        print()
        print("-" * (13 + self.num_players * 10))

    def distribute(self, run_results: List[Dict[int, Set[int]]]) -> List[int]:
        """
        Computes how this pot should be distributed to players

        Args:
            run_result (List[Dict[int, Set[int]]]): A list with run_id as index. Each list element is a dictionary with integer-Set[int] key-value pairs.
                                                    The key signifys hand strength, lower value has higher priority; the Set[int] contains player indices
                                                    with equivalent hand strength. Each list typically only has one element, but might have multiple if
                                                    there are tied hands.

        Returns:
            List[int]: A list with player_id as index. Each element is the amount of chips Each player is entitled to.
        """
        num_runs = len(run_results)
        chips_each_run = [0 for _ in range(num_runs)]
        amount = self.amount
        # Calculate chips for each run (divide as evenly as possible)
        for i in range(num_runs):
            chips_each_run[i] = amount // (num_runs - i)
            amount -= amount // (num_runs - i)
        del amount
        # distribution calculation
        for run_idx in range(num_runs):
            run_result = run_results[run_idx]
            chips = chips_each_run[run_idx]

            for i in range(len(run_result)):
                if not chips:
                    break  # sub-pot for this run already distributed
                entitled_ids = [id for id in run_result[i] if id in self.players_eligible]
                if entitled_ids:
                    for j, id in enumerate(entitled_ids):
                        # deal with chops. when len(entitled_ids) is 1, it effectively just gives all the chips to entitled_ids[0]
                        self.entitled_chips[id] += chips // (len(entitled_ids) - j)
                        self.entitled_chips_per_run[run_idx][id] += chips // (len(entitled_ids) - j)
                        chips -= chips // (len(entitled_ids) - j)
        self._verbose()
        return self.entitled_chips

class SidePotCalculator:
    def __init__(self, debug=False):
        self.pots = []
        if debug:
            self._debug()
        else:
            self._collect_data()

    def _collect_data(self):
        self.num_players = int(input("Enter number of players in the pot: "))
        self.money_in_pot = int(input("Enter amount already in the pot: "))
        self.player_stacks = [int(input(f"Enter stack for player {i}: ")) for i in range(self.num_players)]
        self.num_runs = int(input("Enter number of board runs: "))
        self.run_results = []  # list, with index corresponding to the run number
        for i in range(self.num_runs):
            run_result = {}  # dictionary, with key as hand tier and value as set of player indices

            # Get per-run result
            hands_to_count = set([i for i in range(self.num_players)])
            hand_tier = 0
            print(f"Enter 0-based player indices in descending order of hand strength for run {i + 1}, space-separate in case of ties.")
            while len(hands_to_count) > 0:
                try:
                    player_indices = input(f"Enter tier {hand_tier + 1} player IDs: ")
                    if not player_indices:
                        continue
                    player_indices = list(map(int, player_indices.split()))
                    # assert to prevent segmentation fault
                    assert all(0 <= idx < self.num_players for idx in player_indices) \
                        and len(set(player_indices)) == len(player_indices) \
                        and all(idx in hands_to_count for idx in player_indices)
                    run_result[hand_tier] = set(player_indices)
                    hand_tier += 1
                    for index in player_indices:
                        hands_to_count.remove(index)
                except AssertionError:
                    print('\033[93m' + f"Player indices must be within the range of [0, {self.num_players - 1}] and non-repetitive. Available indices: {hands_to_count}" + '\033[0m')
                    continue
                except KeyError:
                    print('\033[93m' + f"Available indices: {hands_to_count}" + '\033[0m')
                    continue
            self.run_results.append(run_result)

    def _debug(self):
        self.num_players = 4
        self.money_in_pot = 1000
        self.player_stacks = [300, 150, 100, 600]
        self.num_runs = 3
        self.run_results = [{0: set([1]), 1: set([2]), 2: set([0]), 3: set([3])},
                            {0: set([2]), 1: set([1, 3]), 2: set([0])},
                            {0: set([0, 1]), 1: set([2]), 2: set([3])}]
        # self.run_results = []
        # for i in range(self.num_runs):
        #     run_result = {}  # dictionary, with key as hand tier and value as set of player indices

        #     # Get per-run result
        #     hands_to_count = set([i for i in range(self.num_players)])
        #     hand_tier = 0
        #     print(f"Enter 0-based player indices in descending order of hand strength for run {i + 1}, space-separate in case of ties.")
        #     while len(hands_to_count) > 0:
        #         try:
        #             player_indices = input(f"Enter tier {hand_tier + 1} player IDs: ")
        #             if not player_indices:
        #                 continue
        #             player_indices = list(map(int, player_indices.split()))
        #             # assert to prevent segmentation fault
        #             assert all(0 <= idx < self.num_players for idx in player_indices) \
        #                 and len(set(player_indices)) == len(player_indices) \
        #                 and all(idx in hands_to_count for idx in player_indices)
        #             run_result[hand_tier] = set(player_indices)
        #             hand_tier += 1
        #             for index in player_indices:
        #                 hands_to_count.remove(index)
        #         except AssertionError:
        #             print('\033[93m' + f"Player indices must be within the range of [0, {self.num_players - 1}] and non-repetitive. Available indices: {hands_to_count}" + '\033[0m')
        #             continue
        #         except KeyError:
        #             print('\033[93m' + f"Available indices: {hands_to_count}" + '\033[0m')
        #             continue
        #     self.run_results.append(run_result)

    def _allocate_pot(self) -> List[Tuple[int, int]]:
        """
        populates self.pots with Pot instances by calculating main pot and side pots
        based on player contributions and eligible players for each pot

        Returns:
            List[Tuple[int, int]]: Returns remaining stack of players in the form of (player_index, stack) tuples
        """
        # Create a list of (player_index, stack) tuples sorted by stack size (ascending)
        sorted_players = sorted([(i, stack) for i, stack in enumerate(self.player_stacks)], key=lambda x: x[1])

        # main pot, everyone is eligible
        self.pots.append(Pot(self.money_in_pot + sorted_players[0][1] * self.num_players,
                             self.num_players,
                             self.num_runs,
                             set(range(self.num_players)),
                             is_sidepot=False))
        # delete each players' stacks by the amount of shortest stack. Remove player with empty stack.
        sorted_players = [(element[0], element[1] - sorted_players[0][1]) for element in sorted_players if element[1] - sorted_players[0][1] > 0]

        # side pot calculation
        while len(sorted_players) > 1:  # need at least 2 stacks for another side-pot, otherwise remaining stacks of deepest player won't be involved
            # no sorting necessary as sorted_players is already in stack-size ascending order
            self.pots.append(Pot(sorted_players[0][1] * len(sorted_players),
                                self.num_players,
                                self.num_runs,
                                set([element[0] for element in sorted_players]),
                                is_sidepot=True))
            sorted_players = [(element[0], element[1] - sorted_players[0][1]) for element in sorted_players if element[1] - sorted_players[0][1] > 0]
        return sorted_players

    def _verbose(self):
        print(f"\nChips in pot before all-in: {self.money_in_pot}; Running {self.num_runs} {'time' if self.num_runs == 1 else 'times'}.")
        print("-" * (13 + self.num_players * 10))
        print(f"{'| Player ID'.ljust(11)} | ", end='')
        for i in range(self.num_players):
            print(f"{('Player ' + str(i) + ' ').ljust(10)}", end='')
        print()
        print(f"{'| Stack'.ljust(11)} | ", end='')
        for i in range(self.num_players):
            print(f"{str(self.player_stacks[i]).ljust(10)}", end='')
        print()
        print("-" * (13 + self.num_players * 10))

    def calculate(self) -> List[int]:
        """
        Create

        Returns:
            List[int]: Returns the final stack of each player
        """
        self._verbose()

        resultant_stack = [0] * self.num_players
        remaining_stacks = self._allocate_pot()
        for element in remaining_stacks:
            resultant_stack[element[0]] += element[1]

        # Distribute each pot
        for pot in self.pots:
            distribution = pot.distribute(self.run_results)
            for player_id in range(self.num_players):
                resultant_stack[player_id] += distribution[player_id]
        return resultant_stack

if __name__ == "__main__":
    calculator = SidePotCalculator(debug=True)
    winnings = calculator.calculate()

    print("\nFinal winnings:")
    for player, amount in enumerate(winnings):
        print(f"Player {player}: {amount} chips")