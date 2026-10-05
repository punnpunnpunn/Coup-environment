from agents.always_duke import AlwaysDuke
from agents.honest_random import HonestRandom
from agents.random_agent import RandomAgent
from agents.passive_agent import PassiveAgent
from agents.weighted_param_bot import WeightedParamBot
from agents.weighted_param_bot_v2 import WeightedParamBotV2
from src.game import Game

import random

def main():
    # players = [
    #     WeightedParamBot("1", "Anti-PassiveAgent", 
    #                      bluff_percent=0.5,
    #                      challenge_percent=0.5,
    #                      income_weight= 0.49577042683363554,
    #                      foreign_aid_weight=0.6822759904371777,
    #                      coup_weight=1.3664507026090351,
    #                      tax_weight=0.602641812582586,
    #                      assassinate_weight=2.3416001150134598,
    #                      exchange_weight=0.17586871034649856,
    #                      steal_weight=1.8635749319614827,
    #                      print_turns=False
    #                      ),
    #     PassiveAgent("2", "PassiveAgent", print_turns=False),
    #     PassiveAgent("3", "PassiveAgent", print_turns=False),
    #     PassiveAgent("4", "PassiveAgent", print_turns=False),
    # ]

    players = [
            WeightedParamBotV2("1", "Anti-AlwaysDuke",
                            bluff_percent=0.5,
                            challenge_percent=0.5,
                            income_weight=0.3467823038415602,
                            foreign_aid_weight=23.792409359516586, 
                            coup_weight=0.6133564111276301, 
                            tax_weight=0.05711895673435105, 
                            assassinate_weight=1.0229489699492933, 
                            exchange_weight=0.21238830627248242, 
                            steal_weight=0.18407510924825848,
                            print_turns=False
                            ),
            AlwaysDuke("2", "AlwaysDuke 1", print_turns=False),
            AlwaysDuke("3", "AlwaysDuke 2", print_turns=False),
            # AlwaysDuke("4", "AlwaysDuke 3", print_turns=False),
            # AlwaysDuke("5", "AlwaysDuke 4", print_turns=False)
        ]

    winners = {players[i].name: 0 for i in range(len(players))}
    order = {players[i].name: [0 for i in range(len(players))] for i in range(len(players))}
    games = 50000
    for _ in range(games):
        random.shuffle(players)
        for j in range(len(players)):
            order[players[j].name][j] += 1
        game = Game(players)

        while game.winner is None:
            player = game.current

            player.choose_action(game)

        print(f"\nWinner: {game.winner.name}")
        winners[game.winner.name] += 1

    print("\nNumber of wins:", winners)
    print("Turn order Amounts:", order)
    print("Win percentages")
    for i in winners:
        print(f"{i}: {winners[i]/games}")


if __name__ == "__main__":
    main()