import random

from agents.belief import BeliefTracker
from src.cards import Role
from src.game import Game
from src.player import Player


class BeliefHonestRandom(Player):
	"""Honest Random with Beliefs"""

	def __init__(
		self,
		player_id: str,
		name: str | None = None,
		seed: int | None = None,
		print_turns: bool = True
	):
		super().__init__(player_id, name or player_id, print_turns=print_turns)
		self.rng = random.Random(seed)
		self.belief_tracker = BeliefTracker(player_id)

	def observe(self, kind: str, context: dict[str, object]) -> None:
		self.belief_tracker.observe(kind, context)
		if kind == "initial_hand" or (
			kind == "exchange" and context.get("player_id") == self.id
		) or (kind == "reveal" and context.get("player_id") == self.id) or (
			kind == "claim" and context.get("claimant_id") == self.id
		):
			self.belief_tracker.sync_own_cards(
				[card.role for card in self.cards]
			)

	def choose_action(self, game: Game) -> dict:
		if game.current.id != self.id:
			raise ValueError("It is not this agent's turn.")

		roles = {card.role for card in self.cards if not card.revealed}
		if self.coins >= 10:
			action = "coup"
		else:
			actions = ["income", "foreign_aid"]
			if Role.DUKE in roles:
				actions.append("tax")
			if Role.ASSASSIN in roles and self.coins >= 3:
				actions.append("assassinate")
			if Role.AMBASSADOR in roles:
				actions.append("exchange")
			if Role.CAPTAIN in roles:
				actions.append("steal")
			if self.coins >= 7:
				actions.append("coup")
			action = self.rng.choice(actions)

		target_id = None
		if action in ("coup", "assassinate", "steal"):
			opponents = [
				player for player in game.alive_players if player.id != self.id
			]
			target_id = self.rng.choice(opponents).id

		return game.perform_action(
			self.id,
			action,
			target_id=target_id,
		)

	def decide(self, kind: str, context: dict[str, object]) -> object:
		if kind == "challenge":
			return self.belief_tracker.contradicts(
					context["claimant_id"], context["role"]
				)

		if kind == "block":
			roles = {card.role.value for card in self.cards if not card.revealed}
			if self.id not in context["eligible_blockers"]:
				return None

			if context["action"] == "foreign_aid":
				if Role.DUKE.value not in roles:
					return None
				return {"blocker_id": self.id}

			claimable_roles = [
				role for role in context["allowed_roles"] if role in roles
			]
			if not claimable_roles:
				return None

			return {
				"blocker_id": self.id,
				"role": self.rng.choice(claimable_roles),
			}

		if kind == "reveal_influence":
			return self.rng.choice(context["cards"])["index"]

		if kind == "exchange":
			return self.rng.sample(
				range(len(context["cards"])), context["keep_count"]
			)

		raise ValueError(f"Unknown decision type: {kind}")
