from dataclasses import dataclass, field

from cards import Card


@dataclass
class Player:
    id: str
    name: str
    coins: int = 2
    cards: list[Card] = field(default_factory=list)

    @property
    def alive(self):
        return any(not card.revealed for card in self.cards)

    @property
    def influence(self):
        return sum(not card.revealed for card in self.cards)

    def choose_action(self, game):
        valid_actions = ["Income", "Aid"]

        if self.coins >= 7:
            valid_actions.append("Coup")

        valid_actions.append("Duke")

        if self.coins >= 3:
            valid_actions.append("Assassin")

        valid_actions.extend(["Ambassador", "Captain"])

        if self.coins >= 10:
            action = "coup"
            print(f"\n {self.name} has 10 or more coins and must coup.")

        else:
            print("\nChoose an action:")
            for i in range(len(valid_actions)):
                print(f"  [{i + 1}] {valid_actions[i]}")
            action = input(f"\nAction: ").strip().lower()
            if action.isdigit() and 1 <= int(action) <= len(valid_actions):
                action = valid_actions[int(action) - 1].lower()

        try:
            if action == "income":
                game.income(self.id)

            elif action == "aid":
                game.foreign_aid(self.id)

            elif action == "coup":
                target = input("Target: ").strip()
                game.coup(self.id, target)

            elif action == "duke":
                challenge = input("Challenge? [y/n]: ").strip().lower()
                if challenge == "y":
                    challenge_player_id = input("Challenger ID: ").strip()
                    game.challenge(challenge_player_id, self.id, "duke")
                game.tax(self.id)

            elif action == "assassin":
                target = input("Target: ").strip()
                challenge = input("Challenge? [y/n]: ").strip().lower()
                if challenge == "y":
                    challenge_player_id = input("Challenger ID: ").strip()
                    game.challenge(challenge_player_id, self.id, "assassin")
                game.assassinate(self.id, target)

            elif action == "ambassador":
                challenge = input("Challenge? [y/n]: ").strip().lower()
                if challenge == "y":
                    challenge_player_id = input("Challenger ID: ").strip()
                    game.challenge(challenge_player_id, self.id, "ambassador")
                game.exchange(self.id)

            elif action == "captain":
                target = input("Target: ").strip()
                challenge = input("Challenge? [y/n]: ").strip().lower()
                if challenge == "y":
                    challenge_player_id = input("Challenger ID: ").strip()
                    game.challenge(challenge_player_id, self.id, "captain")
                game.steal(self.id, target)

            else:
                print("Unknown action.")
                self.choose_action(game)

        except ValueError as e:
            print(f"Invalid action: {e}")
            self.choose_action(game)


    def reveal_card(self, index: int):
        if index < 0 or index >= len(self.cards):
            raise ValueError("Invalid card index.")

        card = self.cards[index]

        if card.revealed:
            raise ValueError("That card is already revealed.")

        print(f"{self.name} reveals {card.role.value}.")

        card.revealed = True
        return card

    def lose_influence(self):
        if self.influence == 0:
            raise ValueError("Player has no remaining influence.")
        if self.influence == 1:
            print(f"{self.name} has only one influence left and must reveal it.")
            return self.reveal_card(next(i for i, card in enumerate(self.cards) if not card.revealed))
        for i in range(self.influence):
            print(f"  [{i + 1}] {self.cards[i].role.value}")
        choice = input(f"Choose a card to reveal [1-{self.influence}]: ").strip()
        while not choice.isdigit() or int(choice) < 1 or int(choice) > self.influence:
            choice = input(f"Invalid choice. Choose a card to reveal [1-{self.influence}]: ").strip()
        return self.reveal_card(int(choice) - 1)