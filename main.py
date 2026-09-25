from game import Game
from player import Player


def main():
    players = [
        Player("1", "Player 1"),
        Player("2", "Player 2"),
        Player("3", "Player 3"),
        Player("4", "Player 4"),
    ]

    game = Game(players)

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

    print(f"\nWinner: {game.winner.name}")


if __name__ == "__main__":
    main()