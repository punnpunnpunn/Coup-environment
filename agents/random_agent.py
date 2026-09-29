import random

from src.game import Game
from src.player import Player


class RandomAgent(Player):
	"""An agent that chooses actions and responses uniformly at random."""

	def __init__(
		self,
		player_id: str,
		name: str | None = None,
		seed: int | None = None,
	):
		super().__init__(player_id, name or player_id)
		self.rng = random.Random(seed)

	def choose_action(self, game: Game) -> dict:
		if game.current.id != self.id:
			raise ValueError("It is not this agent's turn.")

		player = game.current
		if player.coins >= 10:
			action = "coup"
		else:
			actions = ["income", "foreign_aid", "tax", "exchange", "steal"]
			if player.coins >= 3:
				actions.append("assassinate")
			if player.coins >= 7:
				actions.append("coup")
			action = self.rng.choice(actions)

		target_id = None
		if action in ("coup", "assassinate", "steal"):
			opponents = [
				opponent
				for opponent in game.alive_players
				if opponent.id != self.id
			]
			target_id = self.rng.choice(opponents).id

		return game.perform_action(
			self.id,
			action,
			target_id=target_id,
			decision_provider=self.decide,
		)

	def decide(self, kind: str, context: dict[str, object]) -> object:
		if kind == "challenge":
			return self.rng.choice((True, False))

		if kind == "block":
			if not self.rng.choice((True, False)):
				return None

			blocker_id = self.rng.choice(context["eligible_blockers"])
			if context["action"] == "foreign_aid":
				return {"blocker_id": blocker_id}

			role = self.rng.choice(context["allowed_roles"])
			return {"blocker_id": blocker_id, "role": role}

		if kind == "reveal_influence":
			return self.rng.choice(context["cards"])["index"]

		if kind == "exchange":
			return self.rng.sample(
				range(len(context["cards"])), context["keep_count"]
			)

		raise ValueError(f"Unknown decision type: {kind}")
