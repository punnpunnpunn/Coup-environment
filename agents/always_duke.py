import random

from src.cards import Role
from src.game import Game
from src.player import Player


class AlwaysDuke(Player):
	"""Claims duke every turn and otherwise blocks everything"""

	def __init__(self, player_id: str, name: str | None = None, seed: int | None = None):
		super().__init__(player_id, name or player_id)
		self.rng = random.Random(seed)

	def choose_action(self, game: Game) -> dict:
		if game.current.id != self.id:
			raise ValueError("It is not this agent's turn.")

		if self.coins >= 7:
			opponents = [
				player for player in game.alive_players if player.id != self.id
			]
			highest_coin_total = max(player.coins for player in opponents)
			top_coin_opponents = [
				player for player in opponents if player.coins == highest_coin_total
			]
			target_id = self.rng.choice(top_coin_opponents).id
			action = "coup"
		else:
			target_id = None
			action = "duke"

		return game.perform_action(
			self.id,
			action,
			target_id=target_id,
		)

	def decide(self, kind: str, context: dict[str, object]) -> object:
		if kind == "challenge":
			return False

		if kind == "block":
			if self.id not in context["eligible_blockers"]:
				return None

			block = {"blocker_id": self.id}
			if context["action"] == "foreign_aid":
				return block

			if context["action"] == "assassinate":
				block["role"] = "contessa"
			else:
				block["role"] = self.rng.choice(context["allowed_roles"])
			return block

		if kind == "reveal_influence":
			cards = context["cards"]
			non_dukes = [card for card in cards if card["role"] != Role.DUKE.value]
			return (non_dukes or cards)[0]["index"]

		raise ValueError(f"Unknown decision type: {kind}")
