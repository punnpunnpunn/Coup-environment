import unittest
from unittest.mock import patch

from agents.passive_agent import PassiveAgent
from src.cards import Card, Role
from src.game import Game
from src.player import Player


class PassiveAgentTests(unittest.TestCase):
    def test_passive_agents_take_income_on_each_turn(self):
        players = [
            PassiveAgent("p1", "Passive 1"),
            PassiveAgent("p2", "Passive 2"),
        ]
        game = Game(players)

        for _turn in range(4):
            game.current.choose_action(game)

        self.assertEqual([player.coins for player in players], [4, 4])
        self.assertTrue(all("takes Income" in event for event in game.log if "takes" in event))

    def test_passive_agent_only_coups_at_ten_and_targets_first_opponent(self):
        agent = PassiveAgent("p1", "Passive 1")
        target = PassiveAgent("p2", "Target")
        other = Player("p3", "Other")
        game = Game([agent, target, other])
        agent.coins = 10
        target.cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
        other_influence_before = other.influence

        agent.choose_action(game)

        self.assertEqual(agent.coins, 3)
        self.assertEqual(target.influence, 1)
        self.assertEqual(other.influence, other_influence_before)

    def test_passive_agent_never_challenges_or_blocks(self):
        agent = PassiveAgent("p1")

        self.assertIs(agent.decide("challenge", {}), False)
        self.assertIsNone(agent.decide("block", {}))

    def test_passive_agent_does_not_challenge_another_players_claim(self):
        passive = PassiveAgent("p1", "Passive")
        actor = Player("p2", "Actor")
        game = Game([passive, actor])
        passive.choose_action(game)

        with patch("builtins.input", side_effect=AssertionError("unexpected prompt")):
            game.perform_action(actor.id, "tax")

        self.assertEqual(actor.coins, 5)
        self.assertFalse(any("challenges Passive's" in event for event in game.log))

    def test_passive_agent_does_not_block_another_players_foreign_aid(self):
        passive = PassiveAgent("p1", "Passive")
        actor = Player("p2", "Actor")
        game = Game([passive, actor])
        passive.choose_action(game)

        with patch("builtins.input", side_effect=AssertionError("unexpected prompt")):
            game.perform_action(actor.id, "foreign_aid")

        self.assertEqual(actor.coins, 4)
        self.assertTrue(any("No one blocks foreign aid" in event for event in game.log))

    def test_passive_agent_reveals_first_available_influence(self):
        agent = PassiveAgent("p1")

        self.assertEqual(
            agent.decide(
                "reveal_influence",
                {"cards": [{"index": 1}, {"index": 4}]},
            ),
            1,
        )

    def test_passive_agent_rejects_playing_out_of_turn(self):
        players = [PassiveAgent("p1"), PassiveAgent("p2")]
        game = Game(players)

        with self.assertRaisesRegex(ValueError, "not this agent's turn"):
            players[1].choose_action(game)


if __name__ == "__main__":
	unittest.main()