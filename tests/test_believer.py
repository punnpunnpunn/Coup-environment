import unittest
from unittest.mock import patch

from agents.believer import Believer
from src.cards import Card, Role
from src.game import Game
from src.player import Player


class BelieverTests(unittest.TestCase):
	def setUp(self):
		self.agent = Believer("p1", seed=1)

	def challenge_context(self, claimant_id: str, role: Role) -> dict[str, object]:
		return {"claimant_id": claimant_id, "role": role.value}

	def test_challenges_a_third_distinct_role_claim(self):
		self.agent.add_belief("p2", Role.DUKE)
		self.agent.add_belief("p2", Role.CAPTAIN)

		self.assertTrue(
			self.agent.decide(
				"challenge",
				self.challenge_context("p2", Role.ASSASSIN),
			)
		)
		self.assertEqual(
			self.agent.beliefs["p2"],
			[Role.DUKE, Role.CAPTAIN],
		)

	def test_randomly_challenges_claims_without_a_contradiction(self):
		with patch.object(self.agent.rng, "choice", return_value=True) as choice:
			self.assertTrue(
				self.agent.decide(
					"challenge",
					self.challenge_context("p2", Role.DUKE),
				)
			)

		choice.assert_called_once_with((True, False))

	def test_challenges_when_all_three_copies_are_already_accounted_for(self):
		self.agent.cards = [Card(Role.DUKE), Card(Role.ASSASSIN)]
		self.agent.add_belief("p2", Role.DUKE)
		self.agent.add_belief("p3", Role.DUKE)

		self.assertTrue(
			self.agent.decide(
				"challenge",
				self.challenge_context("p4", Role.DUKE),
			)
		)

	def test_own_claims_are_not_counted_twice_with_own_cards(self):
		self.agent.cards = [Card(Role.DUKE), Card(Role.ASSASSIN)]
		self.agent.add_belief(self.agent.id, Role.DUKE)
		self.agent.add_belief("p2", Role.DUKE)

		self.assertFalse(self.agent._contradicts_beliefs("p3", Role.DUKE))

	def test_repeated_claims_do_not_add_extra_belief_copies(self):
		self.agent.observe(
			"claim",
			{"claimant_id": "p2", "role": Role.DUKE.value},
		)
		self.agent.observe(
			"claim",
			{"claimant_id": "p2", "role": Role.DUKE.value},
		)

		self.assertEqual(self.agent.beliefs["p2"], [Role.DUKE])
		self.assertEqual(
			self.agent.claim_order["p2"], [Role.DUKE, Role.DUKE]
		)

	def test_disproven_claim_is_removed_from_beliefs(self):
		self.agent.add_belief("p2", Role.DUKE)

		self.agent.observe(
			"claim",
			{
				"claimant_id": "p2",
				"role": Role.DUKE.value,
				"disproven": True,
			},
		)

		self.assertEqual(self.agent.beliefs["p2"], [])

	def test_successful_exchange_clears_that_players_beliefs(self):
		self.agent.add_belief("p2", Role.DUKE)
		self.agent.add_belief("p2", Role.CAPTAIN)
		self.agent.add_belief("p3", Role.ASSASSIN)

		self.agent.observe("exchange", {"player_id": "p2"})

		self.assertEqual(self.agent.beliefs["p2"], [])
		self.assertEqual(self.agent.beliefs["p3"], [Role.ASSASSIN])

	def test_successful_exchange_preserves_revealed_beliefs(self):
		self.agent.add_belief("p2", Role.CAPTAIN)
		self.agent.observe(
			"reveal",
			{"player_id": "p2", "role": Role.DUKE.value},
		)
		self.agent.observe(
			"claim",
			{"claimant_id": "p2", "role": Role.ASSASSIN.value},
		)

		self.agent.observe("exchange", {"player_id": "p2"})

		self.assertEqual(self.agent.beliefs["p2"], [Role.DUKE])

	def test_reveal_keeps_known_card_and_removes_newest_unrevealed_belief(self):
		for role in (Role.DUKE, Role.CAPTAIN):
			self.agent.observe(
				"claim",
				{"claimant_id": "p2", "role": role.value},
			)
		self.agent.observe(
			"claim",
			{"claimant_id": "p2", "role": Role.ASSASSIN.value},
		)

		self.agent.observe(
			"reveal",
			{"player_id": "p2", "role": Role.CONTESSA.value},
		)

		self.assertEqual(
			self.agent.beliefs["p2"],
			[Role.DUKE, Role.CONTESSA],
		)
		self.assertEqual(
			self.agent.known_beliefs["p2"], [Role.CONTESSA]
		)

	def test_game_initializes_beliefs_with_agents_own_cards(self):
		agent = Believer("p1", seed=1)
		Game([agent, Player("p2", "Opponent")])

		self.assertEqual(
			set(agent.beliefs[agent.id]),
			{card.role for card in agent.cards},
		)
		self.assertEqual(
			agent.known_beliefs[agent.id],
			[card.role for card in agent.cards],
		)

	def test_initial_hand_keeps_duplicate_known_copies(self):
		self.agent.observe(
			"initial_hand",
			{
				"player_id": self.agent.id,
				"roles": [Role.DUKE.value, Role.DUKE.value],
			},
		)

		self.assertEqual(
			self.agent.beliefs[self.agent.id], [Role.DUKE, Role.DUKE]
		)

	def test_game_notifies_believers_after_a_successful_exchange(self):
		exchanger = Player("p1", "Exchanger")
		agent = Believer("p2", seed=1)
		game = Game([exchanger, agent])
		agent.add_belief(exchanger.id, Role.DUKE)
		game.current_player = 0
		exchanger.cards = [Card(Role.AMBASSADOR), Card(Role.CAPTAIN)]

		def decide(kind: str, context: dict[str, object]) -> object:
			if kind == "challenge":
				return False
			if kind == "exchange":
				return [0, 1]
			raise AssertionError(f"Unexpected decision: {kind}")

		with patch("random.shuffle"):
			game.perform_action(exchanger.id, "exchange", decision_provider=decide)

		self.assertEqual(agent.beliefs[exchanger.id], [])

	def test_game_claims_build_beliefs_and_trigger_a_contradiction(self):
		class Claimant(Player):
			def decide(self, kind: str, context: dict[str, object]) -> object:
				if kind == "challenge":
					return False
				if kind == "reveal_influence":
					return context["cards"][0]["index"]
				raise AssertionError(f"Unexpected decision: {kind}")

		agent = Believer("p1", seed=1)
		claimant = Claimant("p2", "Claimant")
		game = Game([agent, claimant])

		def choose_without_random_challenges(options):
			if options == (True, False):
				return False
			return options[0]

		with patch.object(
			agent.rng, "choice", side_effect=choose_without_random_challenges
		):
			for action in ("tax", "steal"):
				game.current_player = 1
				claimant.coins = 4
				game.perform_action(
					claimant.id,
					action,
					target_id=agent.id if action == "steal" else None,
				)

			self.assertEqual(
				agent.beliefs[claimant.id],
				[Role.DUKE, Role.CAPTAIN],
			)

			game.current_player = 1
			claimant.coins = 4
			game.perform_action(
				claimant.id,
				"assassinate",
				target_id=agent.id,
			)

		self.assertTrue(
			any(
				"challenges Claimant's assassin claim" in event
				for event in game.log
			)
		)


if __name__ == "__main__":
	unittest.main()
