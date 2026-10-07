import unittest
from unittest.mock import patch

from agents.aggressive_belief import AggressiveBelief
from agents.belief_honest_random import BeliefHonestRandom
from src.cards import Card, Role
from src.game import Game
from src.player import Player


class AggressiveBeliefTests(unittest.TestCase):
	def setUp(self):
		self.agent = AggressiveBelief("p1", seed=1)
		self.opponent = Player("p2", "Opponent")
		self.game = Game([self.agent, self.opponent])

	def test_is_independent_of_belief_honest_random(self):
		self.assertIs(AggressiveBelief.__base__, Player)
		self.assertFalse(issubclass(AggressiveBelief, BeliefHonestRandom))

	def choose_action(self):
		with patch.object(self.game, "perform_action", return_value={}) as perform:
			self.agent.choose_action(self.game)
		return perform.call_args

	def test_coups_before_other_actions_when_affordable(self):
		self.agent.coins = 7
		self.agent.cards = [Card(Role.DUKE), Card(Role.ASSASSIN)]

		call = self.choose_action()

		self.assertEqual(call.args[1], "coup")
		self.assertEqual(call.kwargs["target_id"], self.opponent.id)

	def test_assassin_targets_player_with_two_believed_nonblocking_cards(self):
		self.agent.coins = 3
		self.agent.cards = [Card(Role.ASSASSIN), Card(Role.CONTESSA)]
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.CONTESSA)
		other = Player("p3", "Other")
		other.cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
		self.game.players.append(other)
		self.agent.belief_tracker.add_belief(other.id, Role.DUKE)
		self.agent.belief_tracker.add_belief(other.id, Role.CAPTAIN)

		call = self.choose_action()

		self.assertEqual(call.args[1], "assassinate")
		self.assertEqual(call.kwargs["target_id"], other.id)

	def test_does_not_assassinate_a_player_with_an_unknown_hand(self):
		self.agent.coins = 3
		self.agent.cards = [Card(Role.ASSASSIN), Card(Role.DUKE)]

		call = self.choose_action()

		self.assertEqual(call.args[1], "tax")
		self.assertIsNone(call.kwargs.get("target_id"))

	def test_assassin_uses_role_exhaustion_to_rule_out_contessa(self):
		self.agent.coins = 3
		self.agent.cards = [Card(Role.ASSASSIN), Card(Role.CONTESSA)]
		self.agent.belief_tracker.sync_own_cards(
			[card.role for card in self.agent.cards]
		)
		first = Player("p3", "First")
		second = Player("p4", "Second")
		first.cards = [Card(Role.CONTESSA), Card(Role.DUKE)]
		second.cards = [Card(Role.CONTESSA), Card(Role.CAPTAIN)]
		self.game.players.extend([first, second])
		self.agent.belief_tracker.add_belief(first.id, Role.CONTESSA)
		self.agent.belief_tracker.add_belief(second.id, Role.CONTESSA)

		call = self.choose_action()

		self.assertEqual(call.args[1], "assassinate")
		self.assertEqual(call.kwargs["target_id"], self.opponent.id)

	def test_uses_tax_when_all_assassination_targets_are_believed_to_block(self):
		self.agent.coins = 3
		self.agent.cards = [Card(Role.ASSASSIN), Card(Role.DUKE)]
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.CONTESSA)

		call = self.choose_action()

		self.assertEqual(call.args[1], "tax")
		self.assertIsNone(call.kwargs.get("target_id"))

	def test_skips_steal_when_target_is_believed_to_have_a_blocker(self):
		self.agent.cards = [Card(Role.CAPTAIN), Card(Role.AMBASSADOR)]
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.CAPTAIN)

		call = self.choose_action()

		self.assertEqual(call.args[1], "exchange")

	def test_steals_when_target_has_two_believed_nonblocking_cards(self):
		self.agent.cards = [Card(Role.CAPTAIN), Card(Role.CONTESSA)]
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.DUKE)
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.ASSASSIN)

		call = self.choose_action()

		self.assertEqual(call.args[1], "steal")
		self.assertEqual(call.kwargs["target_id"], self.opponent.id)

	def test_revealed_role_does_not_count_as_a_possible_blocker(self):
		self.agent.cards = [Card(Role.CAPTAIN), Card(Role.CONTESSA)]
		revealed_captain = Card(Role.CAPTAIN)
		revealed_captain.revealed = True
		self.opponent.cards = [revealed_captain, Card(Role.DUKE)]
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.CAPTAIN)
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.DUKE)
		self.agent.belief_tracker.observe(
			"reveal",
			{"player_id": self.opponent.id, "role": Role.CAPTAIN.value},
		)

		call = self.choose_action()

		self.assertEqual(call.args[1], "steal")
		self.assertEqual(call.kwargs["target_id"], self.opponent.id)

	def test_skips_foreign_aid_if_any_opponent_is_believed_to_have_duke(self):
		self.agent.cards = [Card(Role.ASSASSIN), Card(Role.CONTESSA)]
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.DUKE)

		call = self.choose_action()

		self.assertEqual(call.args[1], "income")

	def test_foreign_aid_precedes_income_when_no_one_is_believed_to_block(self):
		self.agent.cards = [Card(Role.ASSASSIN), Card(Role.CONTESSA)]
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.ASSASSIN)
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.CAPTAIN)

		call = self.choose_action()

		self.assertEqual(call.args[1], "foreign_aid")

	def test_does_not_use_roles_that_are_revealed(self):
		revealed_duke = Card(Role.DUKE)
		revealed_duke.revealed = True
		self.agent.cards = [revealed_duke, Card(Role.ASSASSIN)]

		call = self.choose_action()

		self.assertEqual(call.args[1], "income")

	def test_turn_advances_when_assassination_is_uncertain(self):
		self.agent.coins = 3
		self.agent.cards = [Card(Role.ASSASSIN), Card(Role.DUKE)]

		with patch("builtins.input", return_value="n"):
			self.agent.choose_action(self.game)

		self.assertEqual(self.agent.coins, 6)
		self.assertEqual(self.game.current.id, self.opponent.id)

	def test_exchange_keeps_distinct_roles_in_aggressive_order(self):
		self.agent.coins = 3
		self.agent.cards = [Card(Role.DUKE), Card(Role.CONTESSA)]
		self.opponent.cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.DUKE)
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.CAPTAIN)
		self.agent._game = self.game

		kept = self.agent.decide(
			"exchange",
			{
				"cards": [
					{"index": 0, "role": Role.ASSASSIN.value},
					{"index": 1, "role": Role.CAPTAIN.value},
					{"index": 2, "role": Role.DUKE.value},
					{"index": 3, "role": Role.CONTESSA.value},
				],
				"keep_count": 2,
			},
		)

		self.assertEqual(kept, [2, 0])

	def test_exchange_does_not_keep_duplicate_roles_when_distinct_roles_exist(self):
		self.agent.cards = [Card(Role.DUKE), Card(Role.CONTESSA)]

		kept = self.agent.decide(
			"exchange",
			{
				"cards": [
					{"index": 0, "role": Role.DUKE.value},
					{"index": 1, "role": Role.DUKE.value},
					{"index": 2, "role": Role.CONTESSA.value},
					{"index": 3, "role": Role.AMBASSADOR.value},
				],
				"keep_count": 2,
			},
		)

		self.assertEqual(kept, [0, 2])

	def test_exchange_defers_assassin_when_no_target_is_known_unblockable(self):
		self.agent.coins = 3
		self.agent.cards = [Card(Role.DUKE), Card(Role.CONTESSA)]
		self.agent._game = self.game

		kept = self.agent.decide(
			"exchange",
			{
				"cards": [
					{"index": 0, "role": Role.ASSASSIN.value},
					{"index": 1, "role": Role.DUKE.value},
					{"index": 2, "role": Role.CONTESSA.value},
				],
				"keep_count": 2,
			},
		)

		self.assertEqual(kept, [1, 2])

	def test_reveal_influence_preserves_the_highest_ranked_usable_role(self):
		self.agent.coins = 3
		self.agent.cards = [Card(Role.DUKE), Card(Role.CONTESSA)]
		self.opponent.cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.DUKE)
		self.agent.belief_tracker.add_belief(self.opponent.id, Role.CAPTAIN)
		self.agent._game = self.game

		revealed_index = self.agent.decide(
			"reveal_influence",
			{
				"cards": [
					{"index": 0, "role": Role.DUKE.value},
					{"index": 1, "role": Role.ASSASSIN.value},
				],
			},
		)

		self.assertEqual(revealed_index, 1)

	def test_reveal_influence_discards_an_unusable_assassin_before_contessa(self):
		self.agent._game = self.game

		revealed_index = self.agent.decide(
			"reveal_influence",
			{
				"cards": [
					{"index": 0, "role": Role.ASSASSIN.value},
					{"index": 1, "role": Role.CONTESSA.value},
				],
			},
		)

		self.assertEqual(revealed_index, 0)


if __name__ == "__main__":
	unittest.main()
