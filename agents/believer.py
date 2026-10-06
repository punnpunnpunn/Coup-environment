import random

from src.cards import Role
from src.game import Game
from src.player import Player


class Believer(Player):
	"""Tracks role claims and challenges claims that conflict with its beliefs."""

	def __init__(
		self,
		player_id: str,
		name: str | None = None,
		seed: int | None = None,
	):
		super().__init__(player_id, name or player_id)
		self.rng = random.Random(seed)
		self.beliefs: dict[str, list[Role]] = {}
		self.known_beliefs: dict[str, list[Role]] = {}
		self.claim_order: dict[str, list[Role]] = {}

	def add_belief(self, player_id: str, card: Role | str) -> None:
		role = card if isinstance(card, Role) else Role(card)
		if player_id not in self.beliefs:
			self.beliefs[player_id] = []
		if role not in self.beliefs[player_id]:
			self.beliefs[player_id].append(role)

	def remove_belief(self, player_id: str, card: Role | str) -> None:
		if player_id not in self.beliefs:
			raise ValueError("No existing beliefs for this Player ID")
		role = card if isinstance(card, Role) else Role(card)
		if role not in self.beliefs[player_id]:
			raise ValueError("Card not in this player's belief")
		self.beliefs[player_id].remove(role)

	def observe(self, kind: str, context: dict[str, object]) -> None:
		if kind == "initial_hand":
			player_id = context["player_id"]
			roles = context["roles"]
			if not isinstance(player_id, str) or not isinstance(roles, list):
				raise ValueError("Initial hand observation is invalid.")
			self.beliefs[player_id] = []
			self.known_beliefs[player_id] = []
			self.claim_order[player_id] = []
			for role in roles:
				self._add_known_belief(player_id, Role(role))
			return

		if kind == "claim":
			claimant_id = context["claimant_id"]
			role = Role(context["role"])
			if not isinstance(claimant_id, str):
				raise ValueError("Claimant ID must be a string.")

			if claimant_id == self.id:
				self._sync_own_beliefs()
			elif context.get("disproven", False) or context.get("proven", False):
				self._remove_unrevealed_belief(claimant_id, role)
			else:
				self.add_belief(claimant_id, role)
				self.claim_order.setdefault(claimant_id, []).append(role)
			return

		if kind == "reveal":
			player_id = context["player_id"]
			if not isinstance(player_id, str):
				raise ValueError("Player ID must be a string.")
			role = Role(context["role"])
			if player_id == self.id:
				self._sync_own_beliefs()
			else:
				self._add_known_belief(player_id, role)
				while len(self.beliefs[player_id]) > 2:
					if not self._remove_newest_unrevealed_belief(
						player_id, except_role=role
					):
						break
			return

		if kind == "exchange":
			player_id = context["player_id"]
			if not isinstance(player_id, str):
				raise ValueError("Player ID must be a string.")
			self.beliefs[player_id] = [
				role
				for role in self.beliefs.get(player_id, [])
				if role in self.known_beliefs.get(player_id, [])
			]
			self.claim_order[player_id] = []
			if player_id == self.id:
				self._sync_own_beliefs()
			return

		raise ValueError(f"Unknown observation type: {kind}")

	def _add_known_belief(self, player_id: str, role: Role) -> None:
		known = self.known_beliefs.setdefault(player_id, [])
		known.append(role)
		beliefs = self.beliefs.setdefault(player_id, [])
		if beliefs.count(role) < known.count(role):
			beliefs.append(role)

	def _sync_own_beliefs(self) -> None:
		self.beliefs[self.id] = []
		self.known_beliefs[self.id] = []
		self.claim_order[self.id] = []
		for card in self.cards:
			self._add_known_belief(self.id, card.role)

	def _remove_unrevealed_belief(self, player_id: str, role: Role) -> None:
		if role in self.known_beliefs.get(player_id, []):
			return
		if role in self.beliefs.get(player_id, []):
			self.remove_belief(player_id, role)
		self.claim_order[player_id] = [
			claimed_role
			for claimed_role in self.claim_order.get(player_id, [])
			if claimed_role != role
		]

	def _remove_newest_unrevealed_belief(
		self, player_id: str, except_role: Role | None = None
	) -> bool:
		known = self.known_beliefs.get(player_id, [])
		claim_order = self.claim_order.get(player_id, [])
		for index in range(len(claim_order) - 1, -1, -1):
			role = claim_order[index]
			if role != except_role and role not in known:
				self.claim_order[player_id] = [
					claimed_role
					for claimed_role in claim_order
					if claimed_role != role
				]
				if role in self.beliefs.get(player_id, []):
					self.remove_belief(player_id, role)
				return True
		return False

	def _contradicts_beliefs(self, claimant_id: str, role: Role) -> bool:
		prior_roles = set(self.beliefs.get(claimant_id, []))
		if role not in prior_roles and len(prior_roles) >= 2:
			return True

		known_copies = sum(card.role == role for card in self.cards)
		for player_id, claimed_roles in self.beliefs.items():
			if player_id == self.id:
				continue
			known_copies += self.known_beliefs.get(player_id, []).count(role)
			if (
				role in claimed_roles
				and role not in self.known_beliefs.get(player_id, [])
			):
				known_copies += 1
		return known_copies >= 3

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
			claimant_id = context["claimant_id"]
			role = Role(context["role"])
			if not isinstance(claimant_id, str):
				raise ValueError("Claimant ID must be a string.")

			should_challenge = self._contradicts_beliefs(claimant_id, role)
			if should_challenge:
				return True
			return self.rng.choice((True, False))

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
