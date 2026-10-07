import random

from agents.belief import BeliefTracker
from src.cards import Role
from src.game import Game
from src.player import Player


class AggressiveBelief(Player):
	"""Choose the most aggressive honest action opponents are unlikely to stop."""

	def __init__(
		self,
		player_id: str,
		name: str | None = None,
		seed: int | None = None,
	):
		super().__init__(player_id, name or player_id)
		self.rng = random.Random(seed)
		self.belief_tracker = BeliefTracker(player_id)
		self._game: Game | None = None

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
		self._game = game

		roles = {card.role for card in self.cards if not card.revealed}
		opponents = [
			player for player in game.alive_players if player.id != self.id
		]

		if self.coins >= 7:
			target = max(opponents, key=lambda player: player.influence)
			return game.perform_action(self.id, "coup", target_id=target.id)

		if Role.ASSASSIN in roles and self.coins >= 3:
			targets = [
				player
				for player in opponents
				if self._cannot_block(
					player, {Role.CONTESSA}, game
				)
			]
			if targets:
				target = min(targets, key=lambda player: player.influence)
				return game.perform_action(
					self.id, "assassinate", target_id=target.id
				)

		if Role.DUKE in roles:
			return game.perform_action(self.id, "tax")

		if Role.CAPTAIN in roles:
			targets = [
				player
				for player in opponents
				if self._cannot_block(
					player, {Role.AMBASSADOR, Role.CAPTAIN}, game
				)
			]
			if targets:
				target = max(targets, key=lambda player: player.coins)
				return game.perform_action(self.id, "steal", target_id=target.id)

		if Role.AMBASSADOR in roles:
			return game.perform_action(self.id, "exchange")

		if all(
			self._cannot_block(player, {Role.DUKE}, game)
			for player in opponents
		):
			return game.perform_action(self.id, "foreign_aid")

		return game.perform_action(self.id, "income")

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
			cards = context["cards"]
			role_order = self._ranked_card_indices(cards)
			return role_order[-1]

		if kind == "exchange":
			cards = context["cards"]
			keep_count = context["keep_count"]
			ranked_indices = self._ranked_card_indices(cards)
			kept: list[int] = []
			kept_roles: set[Role] = set()
			for index in ranked_indices:
				role = Role(cards[index]["role"])
				if role not in kept_roles:
					kept.append(index)
					kept_roles.add(role)
					if len(kept) == keep_count:
						return kept

			kept.extend(
				index for index in ranked_indices if index not in kept
			)
			return kept[:keep_count]

		raise ValueError(f"Unknown decision type: {kind}")

	def _ranked_card_indices(
		self, cards: list[dict[str, object]]
	) -> list[int]:
		priorities = {
			Role.DUKE: 0,
			Role.ASSASSIN: 1,
			Role.CAPTAIN: 2,
			Role.CONTESSA: 3,
			Role.AMBASSADOR: 4,
		}
		return sorted(
			(range(len(cards))),
			key=lambda index: (
				self._role_priority(Role(cards[index]["role"]), priorities),
				index,
			),
		)

	def _role_priority(
		self, role: Role, priorities: dict[Role, int]
	) -> int:
		if role in (Role.ASSASSIN, Role.CAPTAIN) and not self._can_use_role(
			role
		):
			return len(priorities) + priorities[role]
		return priorities[role]

	def _can_use_role(self, role: Role) -> bool:
		if role not in (Role.ASSASSIN, Role.CAPTAIN):
			return True
		if role == Role.ASSASSIN and self.coins < 3:
			return False
		if self._game is None:
			return False

		blocking_roles = (
			{Role.CONTESSA}
			if role == Role.ASSASSIN
			else {Role.AMBASSADOR, Role.CAPTAIN}
		)
		return any(
			player.id != self.id
			and player.alive
			and self._cannot_block(player, blocking_roles, self._game)
			for player in self._game.alive_players
		)

	def _cannot_block(
		self, target: Player, blocking_roles: set[Role], game: Game
	) -> bool:
		active_beliefs = list(
			self.belief_tracker.beliefs.get(target.id, [])
		)
		for card in target.cards:
			if card.revealed and card.role in active_beliefs:
				active_beliefs.remove(card.role)

		if (
			len(active_beliefs) >= target.influence
			and not blocking_roles.intersection(active_beliefs)
		):
			return True

		if blocking_roles.intersection(active_beliefs):
			return False

		return all(
			sum(
				self.belief_tracker.beliefs.get(player.id, []).count(role)
				for player in game.players
				if player.id != target.id
			)
			>= 3
			for role in blocking_roles
		)