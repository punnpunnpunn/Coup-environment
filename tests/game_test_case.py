import unittest

from src.game import Game
from src.player import Player


class GameTestCase(unittest.TestCase):
    def setUp(self):
        self.players = [
            Player("p1", "Player 1"),
            Player("p2", "Player 2"),
            Player("p3", "Player 3"),
        ]
        self.game = Game(self.players)

    @staticmethod
    def no_challenges(kind, context):
        if kind == "challenge":
            return False
        if kind == "block":
            return None
        if kind == "reveal_influence":
            return context["cards"][0]["index"]
        if kind == "exchange":
            return list(range(context["keep_count"]))
        raise AssertionError(f"Unexpected decision: {kind}")