import unittest
from unittest.mock import patch

from agents.honest_random import HonestRandom
from agents.random_agent import RandomAgent
from src.cards import Card, Role
from src.game import Game
from src.player import Player


class HonestRandomTests(unittest.TestCase):
	def test_is_independent_of_random_agent(self):
		self.assertIs(HonestRandom.__base__, Player)
		self.assertFalse(issubclass(HonestRandom, RandomAgent))

	def test_action_choices_only_include_roles_it_holds(self):
		agent = HonestRandom("p1", seed=1)
		game = Game([agent, Player("p2", "Opponent")])
		agent.cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
		seen_actions = []

		def choose_first(options):
			seen_actions.append(tuple(options))
			return options[0]

		with patch.object(agent.rng, "choice", side_effect=choose_first):
			agent.choose_action(game)

		self.assertEqual(
			seen_actions[0], ("income", "foreign_aid", "tax", "steal")
		)

	def test_revealed_roles_do_not_enable_actions_or_blocks(self):
		agent = HonestRandom("p1", seed=1)
		duke = Card(Role.DUKE)
		duke.revealed = True
		agent.cards = [duke, Card(Role.CAPTAIN)]

		self.assertIsNone(
			agent.decide(
				"block",
				{
					"action": "foreign_aid",
					"eligible_blockers": ["p1"],
					"allowed_roles": ["duke"],
				},
			)
		)

	def test_steal_block_uses_only_a_held_allowed_role(self):
		agent = HonestRandom("p1", seed=1)
		agent.cards = [Card(Role.CAPTAIN), Card(Role.DUKE)]

		with patch.object(agent.rng, "choice", return_value="captain"):
			block = agent.decide(
				"block",
				{
					"action": "steal",
					"eligible_blockers": ["p1"],
					"allowed_roles": ["ambassador", "captain"],
				},
			)

		self.assertEqual(block, {"blocker_id": "p1", "role": "captain"})

	def test_honest_agent_blocks_foreign_aid_during_game(self):
		actor = Player("p1", "Actor")
		agent = HonestRandom("p2", seed=1)
		game = Game([actor, agent])
		agent.cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]

		with patch("builtins.input", return_value="n"):
			game.perform_action(actor.id, "foreign_aid")

		self.assertEqual(actor.coins, 2)
		self.assertTrue(any("block succeeds" in event for event in game.log))

	def test_agent_completes_turn_and_forces_coup_at_ten(self):
		agent = HonestRandom("p1", seed=5)
		opponent = HonestRandom("p2", seed=6)
		game = Game([agent, opponent])
		agent.coins = 10
		influence_before = opponent.influence

		state = agent.choose_action(game)

		self.assertEqual(agent.coins, 3)
		self.assertEqual(opponent.influence, influence_before - 1)
		self.assertEqual(state["current_player"], "p2")


if __name__ == "__main__":
	unittest.main()