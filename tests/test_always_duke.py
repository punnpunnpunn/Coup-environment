import random
import unittest
from unittest.mock import patch

from agents.always_duke import AlwaysDuke
from src.cards import Card, Role
from src.game import Game
from src.player import Player


class AlwaysDukeTests(unittest.TestCase):
    def make_game_with_blocking_agent(self, action):
        actor = Player("p1", "Actor")
        agent = AlwaysDuke("p2", "Always Duke", seed=3)
        game = Game([actor, agent])
        if action == "assassinate":
            actor.coins = 3
        agent.cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
        return game, actor, agent

    def test_coups_player_with_most_coins(self):
        agent = AlwaysDuke("p1", "Always Duke", seed=5)
        opponents = [Player("p2", "Two"), Player("p3", "Three"), Player("p4", "Four")]
        game = Game([agent, *opponents])
        agent.coins = 7
        opponents[0].coins = 6
        opponents[1].coins = 9
        opponents[2].coins = 8

        with patch("builtins.input", return_value="1"):
            agent.choose_action(game)

        self.assertEqual(opponents[1].influence, 1)
        self.assertEqual(opponents[0].influence, 2)
        self.assertEqual(opponents[2].influence, 2)

    def test_randomly_selects_among_opponents_tied_for_most_coins(self):
        seed = 11
        agent = AlwaysDuke("p1", "Always Duke", seed=seed)
        opponents = [Player(f"p{i}", f"Player {i}") for i in range(2, 5)]
        game = Game([agent, *opponents])
        agent.coins = 7
        opponents[0].coins = 10
        opponents[1].coins = 10
        opponents[2].coins = 4
        expected_target = random.Random(seed).choice(opponents[:2])

        with patch("builtins.input", return_value="1"):
            agent.choose_action(game)

        self.assertEqual(expected_target.influence, 1)
        self.assertEqual(opponents[2].influence, 2)
        other_tied_opponent = opponents[1] if expected_target is opponents[0] else opponents[0]
        self.assertEqual(other_tied_opponent.influence, 2)

    def test_blocks_foreign_aid_with_duke(self):
        game, actor, _agent = self.make_game_with_blocking_agent("foreign_aid")

        with patch("builtins.input", return_value="n"):
            game.perform_action(actor.id, "foreign_aid")

        self.assertEqual(actor.coins, 2)
        self.assertTrue(any("block succeeds" in event for event in game.log))

    def test_blocks_assassination_with_contessa_claim(self):
        game, actor, agent = self.make_game_with_blocking_agent("assassinate")

        with patch("builtins.input", return_value="n"):
            game.perform_action(actor.id, "assassinate", agent.id)

        self.assertEqual(actor.coins, 0)
        self.assertEqual(agent.influence, 2)
        self.assertTrue(any("claims contessa to block assassinate" in event for event in game.log))

    def test_blocks_steal_with_allowed_role(self):
        game, actor, agent = self.make_game_with_blocking_agent("steal")

        with patch("builtins.input", return_value="n"):
            game.perform_action(actor.id, "steal", agent.id)

        self.assertEqual(actor.coins, 2)
        self.assertEqual(agent.coins, 2)
        self.assertTrue(
            any(
                "claims captain to block steal" in event
                or "claims ambassador to block steal" in event
                for event in game.log
            )
        )

    def test_does_not_block_when_not_eligible(self):
        agent = AlwaysDuke("p1", "Always Duke", seed=3)

        self.assertIsNone(
            agent.decide(
                "block",
                {
                    "action": "foreign_aid",
                    "eligible_blockers": ["p2"],
                    "allowed_roles": ["duke"],
                },
            )
        )

    def test_reveals_non_duke_when_available(self):
        agent = AlwaysDuke("p1", "Always Duke", seed=3)
        available_cards = [
            {"index": 0, "role": "duke"},
            {"index": 1, "role": "captain"},
        ]

        self.assertEqual(
            agent.decide("reveal_influence", {"cards": available_cards}),
            1,
        )

    def test_reveals_duke_only_when_no_alternative_exists(self):
        agent = AlwaysDuke("p1", "Always Duke", seed=3)

        self.assertEqual(
            agent.decide(
                "reveal_influence",
                {"cards": [{"index": 2, "role": "duke"}]},
            ),
            2,
        )


if __name__ == "__main__":
	unittest.main()