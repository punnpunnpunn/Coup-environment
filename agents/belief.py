from src.cards import Role


class BeliefTracker:
	"""Track each player's known cards and unrevealed role claims."""

	def __init__(self, player_id: str):
		self.player_id = player_id
		self.beliefs: dict[str, list[Role]] = {}
		self.known_beliefs: dict[str, list[Role]] = {}
		self.claim_order: dict[str, list[Role]] = {}

	def observe(self, kind: str, context: dict[str, object]) -> None:
		if kind == "new_game":
			self.beliefs.clear()
			self.known_beliefs.clear()
			self.claim_order.clear()
			return

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

			if claimant_id == self.player_id:
				return
			if context.get("disproven", False) or context.get("proven", False):
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
			return

		raise ValueError(f"Unknown observation type: {kind}")

	def sync_own_cards(self, roles: list[Role]) -> None:
		"""Replace own-card beliefs after dealing or exchanging."""
		self.beliefs[self.player_id] = []
		self.known_beliefs[self.player_id] = []
		self.claim_order[self.player_id] = []
		for role in roles:
			self._add_known_belief(self.player_id, role)

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

	def _add_known_belief(self, player_id: str, role: Role) -> None:
		known = self.known_beliefs.setdefault(player_id, [])
		known.append(role)
		beliefs = self.beliefs.setdefault(player_id, [])
		if beliefs.count(role) < known.count(role):
			beliefs.append(role)

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

	def contradicts(self, claimant_id: str, role: Role | str) -> bool:
		role = role if isinstance(role, Role) else Role(role)
		prior_roles = set(self.beliefs.get(claimant_id, []))
		if role not in prior_roles and len(prior_roles) >= 2:
			return True

		known_copies = 0
		for player_id, claimed_roles in self.beliefs.items():
			known_copies += self.known_beliefs.get(player_id, []).count(role)
			if (
				player_id != self.player_id
				and role in claimed_roles
				and role not in self.known_beliefs.get(player_id, [])
			):
				known_copies += 1
		return known_copies >= 3
