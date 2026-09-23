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

    def reveal_card(self, index: int):
        if index < 0 or index >= len(self.cards):
            raise ValueError("Invalid card index.")

        card = self.cards[index]

        if card.revealed:
            raise ValueError("That card is already revealed.")

        card.revealed = True
        return card

    def lose_influence(self):
        """
        Prototype behavior: automatically reveal the first
        unrevealed card. A real UI can ask the human which
        card to reveal later.
        """
        for i, card in enumerate(self.cards):
            if not card.revealed:
                return self.reveal_card(i)

        raise ValueError("Player has no remaining influence.")
