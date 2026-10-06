from dataclasses import dataclass, field

from src.cards import Card


@dataclass
class Player:
    id: str
    name: str
    coins: int = 2
    cards: list[Card] = field(default_factory=list)
    print_turns: bool = True

    @property
    def alive(self):
        return any(not card.revealed for card in self.cards)

    @property
    def influence(self):
        return sum(not card.revealed for card in self.cards)

    def choose_action(self, game):
        valid_actions = ["Income", "Foreign Aid"]

        if self.coins >= 7:
            valid_actions.append("Coup")

        valid_actions.append("Duke")

        if self.coins >= 3:
            valid_actions.append("Assassin")

        valid_actions.extend(["Ambassador", "Captain"])

        if self.coins >= 10:
            action = "coup"
            if self.print_turns:
                print(f"\n {self.name} has 10 or more coins and must coup.")

        else:
            if self.print_turns:
                print("\nChoose an action:")
            for i in range(len(valid_actions)):
                if self.print_turns:
                    print(f"  [{i + 1}] {valid_actions[i]}")
            action = input(f"\nAction: ").strip().lower()
            if action.isdigit() and 1 <= int(action) <= len(valid_actions):
                action = valid_actions[int(action) - 1].lower()

        try:
            target_id = None
            if action in ("coup", "assassin", "captain"):
                target_id = input("Target: ").strip()
            game.perform_action(self.id, action, target_id)

        except ValueError as e:
            if self.print_turns:
                print(f"Invalid action: {e}")
            self.choose_action(game)

    def observe(self, kind: str, context: dict[str, object]) -> None:
        """Receive a public game event; agents may override this to track state."""
        pass

    def reveal_card(self, index: int):
        if index < 0 or index >= len(self.cards):
            raise ValueError("Invalid card index.")

        card = self.cards[index]

        if card.revealed:
            raise ValueError("That card is already revealed.")

        card.revealed = True
        return card

    def lose_influence(self):
        if self.influence == 0:
            raise ValueError("Player has no remaining influence.")
        if self.influence == 1:
            if self.print_turns:
                print(f"{self.name} has only one influence left and must reveal it.")
            return self.reveal_card(next(i for i, card in enumerate(self.cards) if not card.revealed))
        for i in range(self.influence):
            if self.print_turns:
                print(f"  [{i + 1}] {self.cards[i].role.value}")
        choice = input(f"Choose a card to reveal [1-{self.influence}]: ").strip()
        while not choice.isdigit() or int(choice) < 1 or int(choice) > self.influence:
            choice = input(f"Invalid choice. Choose a card to reveal [1-{self.influence}]: ").strip()
        return self.reveal_card(int(choice) - 1)