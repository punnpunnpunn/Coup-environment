from src.game import Game
from src.player import Player


class PassiveAgent(Player):
	"""Take Income every turn and otherwise avoid confrontation."""

	def __init__(self, player_id: str, name: str | None = None, print_turns=True):
		super().__init__(player_id, name or player_id, print_turns=print_turns)

	def choose_action(self, game: Game) -> dict:
		if game.current.id != self.id:
			raise ValueError("It is not this agent's turn.")

		if self.coins >= 10:
			opponents = [
				player for player in game.alive_players if player.id != self.id
			]
			target_id = opponents[0].id
			action = "coup"
		else:
			target_id = None
			action = "income"

		return game.perform_action(
			self.id,
			action,
			target_id=target_id,
		)

	def decide(self, kind: str, context: dict[str, object]) -> object:
		if kind == "challenge":
			return False

		if kind == "block":
			return None

		if kind == "reveal_influence":
			return context["cards"][0]["index"]

		raise ValueError(f"Unknown decision type: {kind}")

def create_passive_agent(player_id: str, 
                         name: str, 
						 seed: int) -> PassiveAgent:
	"""Creates an instance of PassiveAgent with given player_id 
	and name and with print_turns set to False. Intended for use
	in the AntiStrategyOptimizer."""
	return PassiveAgent(player_id, name, print_turns=False)