import random

from src.cards import Role
from src.game import Game
from src.player import Player


class ParamBot(Player):
	"""Choose actions based on random probability"""

	def __init__(
		self,
		player_id: str,
		name: str | None = None,
		seed: int | None = None,
		bluff_percent: float = 0,
		challenge_percent: float = 0,
	):
		super().__init__(player_id, name or player_id)
		self.rng = random.Random(seed)
		self.bluff_percent = bluff_percent
		self.challenge_percent = challenge_percent

	def choose_action(self, game: Game) -> dict:
		if game.current.id != self.id:
			raise ValueError("It is not this agent's turn.")

		roles = {card.role for card in self.cards if not card.revealed}
		if self.coins >= 10:
			action = "coup"
		else:
			lies = ["tax", "exchange", "steal"]
			honest_actions = ["income", "foreign_aid"]
			if Role.DUKE in roles:
				honest_actions.append("tax")
				lies.remove("tax")
			if Role.ASSASSIN in roles and self.coins >= 3:
				honest_actions.append("assassinate")
			elif self.coins >= 3:
				lies.append("assassinate")
			if Role.AMBASSADOR in roles:
				honest_actions.append("exchange")
				lies.remove("exchange")
			if Role.CAPTAIN in roles:
				honest_actions.append("steal")
				lies.remove("steal")
			if self.coins >= 7:
				honest_actions.append("coup")
				
			if self.rng.random() < self.bluff_percent:
				action =self.rng.choice(lies)
			else:
				action = self.rng.choice(honest_actions)

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
			if self.rng.random() < self.challenge_percent:
				return True
			else:
				return False

		if kind == "block":
			roles = {card.role.value for card in self.cards if not card.revealed}
			if self.id not in context["eligible_blockers"]:
				return None
			
			if self.rng.random() > self.bluff_percent:
				return None

			if context["action"] == "foreign_aid":
				return {"blocker_id": self.id}

			claimable_roles = [
				role for role in context["allowed_roles"] if role in roles
			]
			if not claimable_roles:
				return self.rng.choice(context["allowed_roles"])

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
