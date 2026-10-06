import random

from src.cards import Role
from src.game import Game
from src.player import Player


class WeightedParamBotV2(Player):
    """
    A parameterized version of ParamBot.

    The bot first rolls to determine whether it will bluff. It then
    chooses an action from the appropriate set using weighted random
    selection.

    Each action's weight controls how likely that action is to be chosen
    relative to the other currently available actions.

    For example, if the available actions have weights:

        income=1
        foreign_aid=2
        tax=3

    then their probabilities are:

        income      = 1 / 6
        foreign_aid = 2 / 6
        tax         = 3 / 6
    """

    def __init__(
        self,
        player_id: str,
        name: str | None = None,
        seed: int | None = None,
        bluff_percent: float = 0,
        challenge_percent: float = 0,
        income_weight: float = 1,
        foreign_aid_weight: float = 1,
        coup_weight: float = 1,
        tax_weight: float = 1,
        assassinate_weight: float = 1,
        exchange_weight: float = 1,
        steal_weight: float = 1,
        print_turns=True,
    ):
        super().__init__(player_id, name or player_id, print_turns=print_turns)

        self.rng = random.Random(seed)

        self.bluff_percent = bluff_percent
        self.challenge_percent = challenge_percent

        self.action_weights = {
            "income": income_weight,
            "foreign_aid": foreign_aid_weight,
            "coup": coup_weight,
            "tax": tax_weight,
            "assassinate": assassinate_weight,
            "exchange": exchange_weight,
            "steal": steal_weight,
        }

        self._validate_weights()

    def _validate_weights(self):
        """Make sure all action weights are valid."""
        for action, weight in self.action_weights.items():
            if weight < 0:
                raise ValueError(
                    f"Weight for {action} cannot be negative."
                )

    def _weighted_choice(self, actions: list[str]) -> str:
        """
        Choose one action from `actions` using the configured weights.

        The probability of choosing an action is:

            action_weight / sum(all_available_action_weights)
        """
        if not actions:
            raise ValueError("Cannot choose from an empty action list.")

        available_weights = [
            self.action_weights[action]
            for action in actions
        ]

        total_weight = sum(available_weights)

        if total_weight <= 0:
            raise ValueError(
                "The total weight of the available actions must be greater than 0."
            )

        return self.rng.choices(
            actions,
            weights=available_weights,
            k=1,
        )[0]

    def _get_action_sets(self) -> tuple[list[str], list[str]]:
        """
        Determine which actions are honest and which actions require bluffing.

        Returns:
            (honest_actions, bluff_actions)
        """
        roles = {
            card.role
            for card in self.cards
            if not card.revealed
        }

        honest_actions = [
            "income",
            "foreign_aid",
        ]

        bluff_actions = [
            "tax",
            "exchange",
            "steal",
        ]

        if Role.DUKE in roles:
            honest_actions.append("tax")
            bluff_actions.remove("tax")

        if self.coins >= 3:
            if Role.ASSASSIN in roles:
                honest_actions.append("assassinate")
            else:
                bluff_actions.append("assassinate")

        if Role.AMBASSADOR in roles:
            honest_actions.append("exchange")
            bluff_actions.remove("exchange")

        if Role.CAPTAIN in roles:
            honest_actions.append("steal")
            bluff_actions.remove("steal")

        if self.coins >= 7:
            honest_actions.append("coup")

        return honest_actions, bluff_actions

    def choose_action(self, game: Game) -> dict:
        if game.current.id != self.id:
            raise ValueError("It is not this agent's turn.")

        if self.coins >= 10:
            action = "coup"
        else:
            honest_actions, bluff_actions = self._get_action_sets()

            all_actions = honest_actions + bluff_actions

            should_bluff = (
                self.rng.random() < self.bluff_percent
            )

            # --------------------------------
            # This is the big change from WeightedParamBotV1, instead of
            # forcing the bot to lie when it rolls above bluff_percent,
            # we simply allow it to pick from all the possible actions.
            # Later versions could encode different weights for the honest
            # actions versus the ones for bluffing.
            # --------------------------------

            if should_bluff:
                action = self._weighted_choice(all_actions)
            else:
                action = self._weighted_choice(honest_actions)

        target_id = None

        if action in ("coup", "assassinate", "steal"):
            opponents = [
                player
                for player in game.alive_players
                if player.id != self.id
            ]

            if not opponents:
                raise ValueError(
                    "No valid opponents are available to target."
                )

            target_id = self.rng.choice(opponents).id

        return game.perform_action(
            self.id,
            action,
            target_id=target_id,
        )

    def decide(
        self,
        kind: str,
        context: dict[str, object],
    ) -> object:
        if kind == "challenge":
            return self.rng.random() < self.challenge_percent

        if kind == "block":
            roles = {
                card.role.value
                for card in self.cards
                if not card.revealed
            }

            if self.id not in context["eligible_blockers"]:
                return None

            if self.rng.random() > self.bluff_percent:
                return None

            if context["action"] == "foreign_aid":
                return {
                    "blocker_id": self.id,
                }

            claimable_roles = [
                role
                for role in context["allowed_roles"]
                if role in roles
            ]

            # If bluffing and we don't actually have an appropriate role,
            # choose one of the legal roles to claim.
            if not claimable_roles:
                return {
                    "blocker_id": self.id,
                    "role": self.rng.choice(
                        context["allowed_roles"]
                    ),
                }

            return {
                "blocker_id": self.id,
                "role": self.rng.choice(claimable_roles),
            }

        if kind == "reveal_influence":
            return self.rng.choice(context["cards"])["index"]

        if kind == "exchange":
            return self.rng.sample(
                range(len(context["cards"])),
                context["keep_count"],
            )

        raise ValueError(f"Unknown decision type: {kind}")
