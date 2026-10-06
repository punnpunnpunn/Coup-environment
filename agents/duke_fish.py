import random

from src.cards import Role
from src.game import Game
from src.player import Player


class DukeFish(Player):
	"""Claims duke if has duke. Otherwise claims ambassador and fishes for duke and contessa. Blocks if able to"""

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

		elif any(
			card.role == Role.DUKE and not card.revealed for card in self.cards
		):
			target_id = None
			action = "duke"

		else:
			target_id = None
			revealed_dukes = sum(
				card.role == Role.DUKE and card.revealed
				for player in game.players
				for card in player.cards
			)
			action = "foreign_aid" if revealed_dukes >= 3 else "ambassador"

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

			roles = {card.role.value for card in self.cards if not card.revealed}
			if context["action"] == "foreign_aid":
				if Role.DUKE.value not in roles:
					return None
				return {"blocker_id": self.id}

			claimable_roles = [
				role for role in context["allowed_roles"] if role in roles
			]
			if not claimable_roles:
				return None

			block = {"blocker_id": self.id}
			block["role"] = self.rng.choice(claimable_roles)
			return block

		if kind == "reveal_influence":
			cards = context["cards"]
			non_dukes = [card for card in cards if card["role"] != Role.DUKE.value]
			return (non_dukes or cards)[0]["index"]

		if kind == "exchange":
			cards = context["cards"]
			keep_count = context["keep_count"]
			role_indices = {
				role: [card["index"] for card in cards if card["role"] == role.value]
				for role in Role
			}
			dukes = role_indices[Role.DUKE]
			contessas = role_indices[Role.CONTESSA]
			ambassadors = role_indices[Role.AMBASSADOR]

			preferred = []
			if keep_count >= 2 and dukes and contessas:
				preferred = [dukes[0], contessas[0]]
			elif keep_count >= 2 and dukes and ambassadors:
				preferred = [dukes[0], ambassadors[0]]
			elif keep_count >= 2 and not dukes and contessas and ambassadors:
				preferred = [contessas[0], ambassadors[0]]
			elif dukes:
				preferred = [dukes[0]]
			elif contessas or ambassadors:
				preferred = [ambassadors[0]] if ambassadors else [contessas[0]]

			remaining = [
				card["index"]
				for card in cards
				if card["index"] not in preferred
			]
			return preferred + self.rng.sample(
				remaining, keep_count - len(preferred)
			)

		raise ValueError(f"Unknown decision type: {kind}")
