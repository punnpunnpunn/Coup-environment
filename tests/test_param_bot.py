import unittest

from agents.param_bot import ParamBot
from src.cards import Card, Role
from src.game import Game
from src.player import Player


class ParamBotTests(unittest.TestCase):
    def test_choose_action_honest_when_bluff_probability_is_zero(self):
        bot = ParamBot("p1", "Param1", seed=7, bluff_percent=0.0)
        game = Game([bot, Player("p2", "Player 2")])
        bot.cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
        bot.coins = 2

        def fake_perform_action(player_id, action, target_id=None):
            return {
                "player_id": player_id,
                "action": action,
                "target_id": target_id,
            }

        game.perform_action = fake_perform_action

        result = bot.choose_action(game)

        self.assertEqual(result["player_id"], "p1")
        self.assertIn(result["action"], {"income", "foreign_aid", "tax", "steal"})

    def test_choose_action_bluffs_when_bluff_probability_is_one(self):
        bot = ParamBot("p1", "Param1", seed=7, bluff_percent=1.0)
        game = Game([bot, Player("p2", "Player 2")])
        bot.cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
        bot.coins = 2

        def fake_perform_action(player_id, action, target_id=None):
            return {
                "player_id": player_id,
                "action": action,
                "target_id": target_id,
            }

        game.perform_action = fake_perform_action

        result = bot.choose_action(game)

        self.assertEqual(result["action"], "exchange")
        self.assertIsNone(result["target_id"])

    def test_block_rejects_ineligible_players_even_with_high_bluff_probability(self):
        bot = ParamBot("p1", "Param1", seed=7, bluff_percent=1.0)

        decision = bot.decide(
            "block",
            {
                "eligible_blockers": ["p2"],
                "action": "foreign_aid",
                "allowed_roles": [Role.DUKE.value],
            },
        )

        self.assertIsNone(decision)

    def test_block_can_be_used_by_eligible_players(self):
        bot = ParamBot("p1", "Param1", seed=7, bluff_percent=1.0)

        decision = bot.decide(
            "block",
            {
                "eligible_blockers": ["p1"],
                "action": "foreign_aid",
                "allowed_roles": [Role.DUKE.value],
            },
        )

        self.assertEqual(decision, {"blocker_id": "p1"})

    def test_challenge_probability_matches_parameter(self):
        always_challenge = ParamBot("p1", "Param1", seed=7, challenge_percent=1.0)
        never_challenge = ParamBot("p2", "Param2", seed=7, challenge_percent=0.0)

        self.assertTrue(always_challenge.decide("challenge", {}))
        self.assertFalse(never_challenge.decide("challenge", {}))


if __name__ == "__main__":
    unittest.main()
