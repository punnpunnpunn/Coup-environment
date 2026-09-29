import unittest
from unittest.mock import patch

from agents.random_agent import RandomAgent
from src.game import Game
from src.player import Player


class RandomAgentTests(unittest.TestCase):
    def setUp(self):
        self.players = [
            Player("p1", "Player 1"),
            Player("p2", "Player 2"),
            Player("p3", "Player 3"),
        ]
        self.game = Game(self.players)

    def test_agent_completes_its_turn(self):
        agent = RandomAgent("p1", seed=19)

        state = agent.choose_action(self.game)

        self.assertEqual(self.game.current.id, "p2")
        self.assertEqual(state["current_player"], "p2")
        self.assertNotEqual(state["players"][0]["cards"], ["hidden", "hidden"])

    def test_agent_can_be_added_directly_to_game_players(self):
        agent = RandomAgent("ai", "Random player", seed=19)
        human = Player("human", "Human player")
        game = Game([agent, human])
        self.assertIsInstance(agent, Player)

        def human_response(prompt):
            if "Choose a card to reveal" in prompt:
                return "1"
            return "n"

        with patch("builtins.input", side_effect=human_response):
            game.current.choose_action(game)

        self.assertGreaterEqual(agent.coins, 0)
        self.assertEqual(game.current.id, "human")

    def test_agent_forces_coup_at_ten_coins(self):
        players = [
            RandomAgent("p1", seed=4),
            RandomAgent("p2", seed=5),
            RandomAgent("p3", seed=6),
        ]
        game = Game(players)
        players[0].coins = 10
        influence_before = sum(player.influence for player in players[1:])
        agent = players[0]

        agent.choose_action(game)

        self.assertEqual(players[0].coins, 3)
        self.assertEqual(
            sum(player.influence for player in players[1:]),
            influence_before - 1,
        )

    def test_agent_rejects_playing_out_of_turn(self):
        agent = RandomAgent("p2", seed=0)

        with self.assertRaisesRegex(ValueError, "not this agent's turn"):
            agent.choose_action(self.game)

    def test_seeded_agents_finish_games(self):
        for seed in range(5):
            with self.subTest(seed=seed):
                players = [
                    RandomAgent(
                        f"p{index}", f"Player {index}", seed=seed * 10 + index
                    )
                    for index in range(4)
                ]
                game = Game(players)

                for _turn in range(2000):
                    if game.winner is not None:
                        break
                    game.current.choose_action(game)
                else:
                    self.fail(f"Seed {seed} did not finish within 2000 turns")

                self.assertIsNotNone(game.winner)


if __name__ == "__main__":
    unittest.main()