from agents.always_duke import AlwaysDuke
from agents.honest_random import HonestRandom
from agents.random_agent import RandomAgent
from agents.passive_agent import PassiveAgent
from src.game import Game
from src.player import Player


def main():
    players = [
        # Player("1", "Player 1"),
        PassiveAgent("1", "Passive Agent"),
        RandomAgent("2", "Random Agent"),
        AlwaysDuke("3", "Always Duke"),
        HonestRandom("4", "HonestRandom"),
    ]

    game = Game(players)
    displayed_log_length = 0

    while game.winner is None:
        player = game.current

        print("\n" + "=" * 40)
        print(f"{player.name}'s turn")
        print(f"Coins: {player.coins}")
        print(f"Influence: {player.influence}")
        print("Cards: " + ", ".join(
            card.role.value if not card.revealed else f"{card.role.value} (revealed)"
            for card in player.cards
        ))

        for p in game.players:
            print(
                f"  {p.name}: "
                f"{p.coins} coins, "
                f"{p.influence} influence"
            )

        player.choose_action(game)
        for event in game.log[displayed_log_length:]:
            print(f"  {event}")
        displayed_log_length = len(game.log)

    print(f"\nWinner: {game.winner.name}")


if __name__ == "__main__":
    main()