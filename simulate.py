from agents.always_duke import AlwaysDuke
from agents.belief_honest_random import BeliefHonestRandom
from agents.duke_fish import DukeFish
from agents.honest_random import HonestRandom
from agents.random_agent import RandomAgent
from agents.passive_agent import PassiveAgent
from src.game import Game

import random

def main():
    players = [
        PassiveAgent("Passive Agent"),
        HonestRandom("Honest Random"),
        BeliefHonestRandom("Belief Honest Random"),
        DukeFish("Duke Fish"),
    ]

    winners = {
        "Passive Agent": 0,
        "Honest Random": 0,
        "Belief Honest Random": 0,
        "Duke Fish": 0
        }
    order = {
        "Passive Agent": [0,0,0,0],
        "Honest Random": [0,0,0,0],
        "Belief Honest Random": [0,0,0,0],
        "Duke Fish": [0,0,0,0]
    }
    games = 10000
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