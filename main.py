from game import Game
from player import Player


def main():
    players = [
        Player("p1", "Player 1"),
        Player("p2", "Player 2"),
        Player("p3", "Player 3"),
        Player("p4", "Player 4"),
    ]

    game = Game(players)

    while game.winner is None:
        player = game.current

        print("\n" + "=" * 40)
        print(f"{player.name}'s turn")
        print(f"Coins: {player.coins}")
        print(f"Influence: {player.influence}")

        for p in game.players:
            print(
                f"  {p.name}: "
                f"{p.coins} coins, "
                f"{p.influence} influence"
            )

        action = input("\nAction [income/aid/coup]: ").strip().lower()

        try:
            if action == "income":
                game.income(player.id)

            elif action == "aid":
                game.foreign_aid(player.id)

            elif action == "coup":
                target = input("Target: ").strip()
                game.coup(player.id, target)

            else:
                print("Unknown action.")

        except ValueError as e:
            print(f"Invalid action: {e}")

    print(f"\nWinner: {game.winner.name}")


if __name__ == "__main__":
    main()