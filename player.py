class Player:
    def __init__(self, cards):
        self.cards = cards
        self.coins = 2

    def __str__(self):
        return f"Player: {self.cards}, Coins: {self.coins}"

    def lose_card(self, card):
        if card in self.cards:
            self.cards.remove(card)
        else:
            raise ValueError(f"Player does not have the card: {card}")

    def gain_coins(self, amount):
        self.coins += amount

    def lose_coins(self, amount):
        self.coins -= amount
        if self.coins < 0:
            self.coins = 0

    def choose_action(self, action):
        pass