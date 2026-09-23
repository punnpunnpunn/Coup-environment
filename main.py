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

        action = input("\nAction [income/aid/coup/duke/assassin/ambassador/captain]: ").strip().lower()

        try:
            if action == "income":
                game.income(player.id)

            elif action == "aid":
                game.foreign_aid(player.id)

            elif action == "coup":
                target = input("Target: ").strip()
                game.coup(player.id, target)

            elif action == "duke":
                game.tax(player.id)

            elif action == "assassin":
                target = input("Target: ").strip()
                game.assassinate(player.id, target)

            elif action == "ambassador":
                game.exchange(player.id)

            elif action == "captain":
                target = input("Target: ").strip()
                game.steal(player.id, target)

            else:
                print("Unknown action.")

        except ValueError as e:
            print(f"Invalid action: {e}")

    print(f"\nWinner: {game.winner.name}")


if __name__ == "__main__":
    main()