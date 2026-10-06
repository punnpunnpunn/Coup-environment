import unittest
from unittest.mock import patch

from agents.duke_fish import DukeFish
from src.cards import Card, Role
from src.game import Game
from src.player import Player


class DukeFishTests(unittest.TestCase):
	def setUp(self):
		self.agent = DukeFish("p1", seed=7)

	@staticmethod
	def offered(*roles):
		return [
			{"index": index, "role": role.value}
			for index, role in enumerate(roles)
		]

	def exchange(self, roles, keep_count=2):
		return self.agent.decide(
			"exchange",
			{"cards": self.offered(*roles), "keep_count": keep_count},
		)

	def test_uses_duke_action_when_unrevealed_duke_is_available(self):
		game = Game([self.agent, Player("p2", "Opponent")])
		self.agent.cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]

		with patch.object(game, "perform_action", return_value={}) as perform_action:
			self.agent.choose_action(game)

		self.assertEqual(perform_action.call_args.args[1], "duke")

	def test_exposed_duke_does_not_count_as_available(self):
		game = Game([self.agent, Player("p2", "Opponent")])
		duke = Card(Role.DUKE)
		duke.revealed = True
		self.agent.cards = [duke, Card(Role.CAPTAIN)]

		with patch.object(game, "perform_action", return_value={}) as perform_action:
			self.agent.choose_action(game)

		self.assertEqual(perform_action.call_args.args[1], "ambassador")

	def test_foreign_aids_instead_of_exchanging_when_three_dukes_are_revealed(self):
		opponents = [Player("p2", "Opponent 1"), Player("p3", "Opponent 2")]
		game = Game([self.agent, *opponents])
		self.agent.cards = [Card(Role.CAPTAIN), Card(Role.ASSASSIN)]
		revealed_dukes = [Card(Role.DUKE) for _ in range(3)]
		for card in revealed_dukes:
			card.revealed = True
		opponents[0].cards = [revealed_dukes[0], Card(Role.CAPTAIN)]
		opponents[1].cards = revealed_dukes[1:]

		with patch.object(game, "perform_action", return_value={}) as perform_action:
			self.agent.choose_action(game)

		self.assertEqual(perform_action.call_args.args[1], "foreign_aid")

	def test_keeps_exchanging_when_fewer_than_three_dukes_are_revealed(self):
		game = Game([self.agent, Player("p2", "Opponent")])
		self.agent.cards = [Card(Role.CAPTAIN), Card(Role.ASSASSIN)]
		revealed_dukes = [Card(Role.DUKE) for _ in range(2)]
		for card in revealed_dukes:
			card.revealed = True
		game.players[1].cards = [*revealed_dukes, Card(Role.CAPTAIN)]

		with patch.object(game, "perform_action", return_value={}) as perform_action:
			self.agent.choose_action(game)

		self.assertEqual(perform_action.call_args.args[1], "ambassador")

	def test_exchange_prefers_duke_and_contessa(self):
		self.assertEqual(
			self.exchange(
				[Role.ASSASSIN, Role.DUKE, Role.CONTESSA, Role.AMBASSADOR]
			),
			[1, 2],
		)

	def test_exchange_prefers_duke_and_ambassador_without_contessa(self):
		self.assertEqual(
			self.exchange([Role.ASSASSIN, Role.AMBASSADOR, Role.DUKE]),
			[2, 1],
		)

	def test_exchange_keeps_duke_and_a_random_card_without_contessa_or_ambassador(self):
		choices = self.exchange([Role.DUKE, Role.ASSASSIN, Role.CAPTAIN])

		self.assertEqual(choices[0], 0)
		self.assertEqual(len(set(choices)), 2)
		self.assertEqual(len(choices), 2)

	def test_exchange_keeps_contessa_and_ambassador_without_duke(self):
		self.assertEqual(
			self.exchange([Role.ASSASSIN, Role.AMBASSADOR, Role.CONTESSA]),
			[2, 1],
		)

	def test_exchange_keeps_only_contessa_or_ambassador_and_another_card(self):
		choices = self.exchange(
			[Role.ASSASSIN, Role.CONTESSA, Role.CAPTAIN]
		)

		self.assertEqual(choices[0], 1)
		self.assertEqual(len(set(choices)), 2)
		self.assertEqual(len(choices), 2)

	def test_exchange_keeps_one_duke_when_only_one_card_can_be_kept(self):
		self.assertEqual(
			self.exchange([Role.CONTESSA, Role.DUKE, Role.AMBASSADOR], 1),
			[1],
		)

	def test_exchange_fills_randomly_when_no_preferred_role_is_available(self):
		choices = self.exchange([Role.ASSASSIN, Role.CAPTAIN, Role.ASSASSIN])

		self.assertEqual(len(choices), 2)
		self.assertEqual(len(set(choices)), 2)

	def test_does_not_block_if_not_eligible(self):
		self.agent.cards = [Card(Role.DUKE)]

		self.assertIsNone(
			self.agent.decide(
				"block",
				{
					"action": "foreign_aid",
					"eligible_blockers": ["p2"],
					"allowed_roles": [Role.DUKE.value],
				},
			)
		)

	def test_only_blocks_with_unrevealed_allowed_influence(self):
		self.agent.cards = [Card(Role.ASSASSIN), Card(Role.CAPTAIN)]

		self.assertIsNone(
			self.agent.decide(
				"block",
				{
					"action": "foreign_aid",
					"eligible_blockers": ["p1"],
					"allowed_roles": [Role.DUKE.value],
				},
			)
		)
		self.assertIsNone(
			self.agent.decide(
				"block",
				{
					"action": "assassinate",
					"eligible_blockers": ["p1"],
					"allowed_roles": [Role.CONTESSA.value],
				},
			)
		)

		self.agent.cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
		self.agent.cards[0].revealed = True
		self.assertIsNone(
			self.agent.decide(
				"block",
				{
					"action": "foreign_aid",
					"eligible_blockers": ["p1"],
					"allowed_roles": [Role.DUKE.value],
				},
			)
		)

	def test_blocks_with_held_allowed_role(self):
		self.agent.cards = [Card(Role.CAPTAIN), Card(Role.DUKE)]

		self.assertEqual(
			self.agent.decide(
				"block",
				{
					"action": "foreign_aid",
					"eligible_blockers": ["p1"],
					"allowed_roles": [Role.DUKE.value],
				},
			),
			{"blocker_id": "p1"},
		)
		self.assertEqual(
			self.agent.decide(
				"block",
				{
					"action": "steal",
					"eligible_blockers": ["p1"],
					"allowed_roles": [Role.AMBASSADOR.value, Role.CAPTAIN.value],
				},
			),
			{"blocker_id": "p1", "role": Role.CAPTAIN.value},
		)


if __name__ == "__main__":
	unittest.main()
