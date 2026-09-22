from player import Player
import random

class Game:
    def __init__(self, num_players = 4):
        self.deck = self.initialize_deck()
        self.players = self.initialize_players(num_players)
        self.log = []
        self.current_player = 0
        self.is_over = False

    def initialize_deck(self):
        deck = ["Duke", "Assassin", "Captain", "Ambassador", "Contessa"] * 3
        random.shuffle(deck)
        return deck

    def initialize_players(self, num_players):
        players = []
        for _ in range(num_players):
            cards = [self.deck.pop(), self.deck.pop()]
            player = Player(cards)
            players.append(player)
        return players