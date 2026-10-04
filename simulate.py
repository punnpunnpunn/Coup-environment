from agents.always_duke import AlwaysDuke
from agents.honest_random import HonestRandom
from agents.random_agent import RandomAgent
from agents.passive_agent import PassiveAgent
from agents.weighted_param_bot import WeightedParamBot
from src.game import Game

import random

def main():
    players = [
        WeightedParamBot("1", "Passive", bluff_percent=0, challenge_percent=0.5),
        WeightedParamBot("2", "Random Agent", bluff_percent=0, challenge_percent=0.5),
        WeightedParamBot("3", "Always Duke", bluff_percent=0, challenge_percent=0.5),
        WeightedParamBot("4", "Honest Random", bluff_percent=0, challenge_percent=0),
    ]

    winners = {players[i].name: 0 for i in range(len(players))}
    order = {players[i].name: [0,0,0,0] for i in range(len(players))}
    games = 1000
    for _ in range(games):
        random.shuffle(players)
        for j in range(len(players)):
            order[players[j].name][j] += 1
        game = Game(players)
        displayed_log_length = 0

        while game.winner is None:
            player = game.current

            player.choose_action(game)
            for event in game.log[displayed_log_length:]:
                print(f"  {event}")
            displayed_log_length = len(game.log)

        print(f"\nWinner: {game.winner.name}")
        winners[game.winner.name] += 1

    print("\nNumber of wins:", winners)
    print("Turn order Amounts:", order)
    print("Win percentages")
    for i in winners:
        print(f"{i}: {winners[i]/games}")


if __name__ == "__main__":
    main()