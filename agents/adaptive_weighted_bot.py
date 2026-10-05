from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable

from src.cards import Role
from src.game import Game
from src.player import Player


ACTIONS = (
    "income",
    "foreign_aid",
    "coup",
    "tax",
    "assassinate",
    "exchange",
    "steal",
)

FEATURES = (
    "bias",
    "own_coins",
    "own_coins_high",
    "own_influence",
    "opponent_coins",
    "opponent_influence",
    "coin_advantage",
    "influence_advantage",
    "living_opponents",
    "opponent_one_influence",
    "self_one_influence",
    "can_coup",
    "can_assassinate",
    "turn_progress",
    "game_length",
)


def _sigmoid(x: float) -> float:
    """Numerically stable logistic sigmoid."""
    if x >= 0:
        z = math.exp(-min(x, 60.0))
        return 1.0 / (1.0 + z)

    z = math.exp(max(x, -60.0))
    return z / (1.0 + z)


def _safe_exp(x: float) -> float:
    """
    Exponential used for action weights.

    Clipping prevents a badly mutated genome from producing infinity.
    """
    return math.exp(max(-20.0, min(20.0, x)))


def genome_to_python(genome: AdaptiveGenome) -> str:
    """
    Convert a genome into valid Python source code.

    The returned string can be copied directly into simulate.py.
    """
    return (
        "AdaptiveGenome(\n"
        f"    action_weights={repr(genome.action_weights)},\n"
        f"    bluff_weights={repr(genome.bluff_weights)},\n"
        f"    challenge_weights={repr(genome.challenge_weights)},\n"
        f"    block_weights={repr(genome.block_weights)},\n"
        f"    target_weights={repr(genome.target_weights)},\n"
        ")"
    )


@dataclass
class AdaptiveGenome:
    """
    Genome for AdaptiveWeightedBot.

    action_weights[action][feature]
        Controls the score of an action as a function of game state.

    bluff_weights / challenge_weights / block_weights
        Control contextual probabilities.

    target_weights
        Controls which opponent gets targeted by hostile actions.
    """

    action_weights: dict[str, dict[str, float]]
    bluff_weights: dict[str, float]
    challenge_weights: dict[str, float]
    block_weights: dict[str, float]
    target_weights: dict[str, float]

    @classmethod
    def random(
        cls,
        rng: random.Random,
        action_scale: float = 0.5,
        response_scale: float = 0.75,
    ) -> "AdaptiveGenome":
        return cls(
            action_weights={
                action: {
                    feature: rng.gauss(0.0, action_scale)
                    for feature in FEATURES
                }
                for action in ACTIONS
            },
            bluff_weights={
                feature: rng.gauss(0.0, response_scale)
                for feature in FEATURES
            },
            challenge_weights={
                feature: rng.gauss(0.0, response_scale)
                for feature in FEATURES
            },
            block_weights={
                feature: rng.gauss(0.0, response_scale)
                for feature in FEATURES
            },
            target_weights={
                "bias": rng.gauss(0.0, response_scale),
                "opponent_coins": rng.gauss(0.0, response_scale),
                "opponent_influence": rng.gauss(0.0, response_scale),
                "coin_advantage": rng.gauss(0.0, response_scale),
                "influence_advantage": rng.gauss(0.0, response_scale),
                "one_influence": rng.gauss(0.0, response_scale),
            },
        )

    @classmethod
    def from_dict(cls, data: dict) -> "AdaptiveGenome":
        return cls(
            action_weights={
                action: dict(weights)
                for action, weights in data["action_weights"].items()
            },
            bluff_weights=dict(data["bluff_weights"]),
            challenge_weights=dict(data["challenge_weights"]),
            block_weights=dict(data["block_weights"]),
            target_weights=dict(data["target_weights"]),
        )

    def to_dict(self) -> dict:
        return {
            "action_weights": {
                action: dict(weights)
                for action, weights in self.action_weights.items()
            },
            "bluff_weights": dict(self.bluff_weights),
            "challenge_weights": dict(self.challenge_weights),
            "block_weights": dict(self.block_weights),
            "target_weights": dict(self.target_weights),
        }

    def clone(self) -> "AdaptiveGenome":
        return AdaptiveGenome.from_dict(self.to_dict())


class AdaptiveWeightedBot(Player):
    """
    A contextual/generalized version of WeightedParamBot.

    Unlike WeightedParamBot, whose action probabilities are fixed, this
    bot calculates action scores from the current game state.

    The genetic algorithm evolves the genome rather than source code.

    A useful way to think about the bot is:

        action_score =
            bias
            + own_coins * weight
            + opponent_influence * weight
            + ...

        action_probability = softmax(action_scores)

    Bluffing/challenge/blocking use logistic functions.
    """

    def __init__(
        self,
        player_id: str,
        name: str | None = None,
        genome: AdaptiveGenome | None = None,
        seed: int | None = None,
        print_turns: bool = False,
    ):
        super().__init__(
            player_id,
            name or player_id,
            print_turns=print_turns,
        )

        self.genome = genome or AdaptiveGenome.random(
            random.Random(seed)
        )

        self.rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------

    def _features(self, game: Game) -> dict[str, float]:
        opponents = [
            player
            for player in game.alive_players
            if player.id != self.id
        ]

        if opponents:
            average_opponent_coins = (
                sum(player.coins for player in opponents)
                / len(opponents)
            )

            average_opponent_influence = (
                sum(player.influence for player in opponents)
                / len(opponents)
            )

            strongest_opponent_coins = max(
                player.coins for player in opponents
            )

            weakest_opponent_influence = min(
                player.influence for player in opponents
            )
        else:
            average_opponent_coins = 0.0
            average_opponent_influence = 0.0
            strongest_opponent_coins = 0.0
            weakest_opponent_influence = 0.0

        # The game log is intentionally used only as a coarse measure of
        # progression. It does not leak hidden information.
        game_length = min(len(game.log) / 100.0, 1.0)

        return {
            "bias": 1.0,

            "own_coins": min(self.coins / 10.0, 1.5),

            "own_coins_high": (
                1.0 if self.coins >= 7 else 0.0
            ),

            "own_influence": self.influence / 2.0,

            "opponent_coins": min(
                average_opponent_coins / 10.0,
                1.5,
            ),

            "opponent_influence": (
                average_opponent_influence / 2.0
            ),

            "coin_advantage": max(
                -1.0,
                min(
                    1.0,
                    (self.coins - average_opponent_coins) / 10.0,
                ),
            ),

            "influence_advantage": max(
                -1.0,
                min(
                    1.0,
                    (
                        self.influence
                        - average_opponent_influence
                    )
                    / 2.0,
                ),
            ),

            "living_opponents": min(
                len(opponents) / 5.0,
                1.0,
            ),

            "opponent_one_influence": (
                1.0
                if weakest_opponent_influence <= 1
                else 0.0
            ),

            "self_one_influence": (
                1.0 if self.influence <= 1 else 0.0
            ),

            "can_coup": (
                1.0 if self.coins >= 7 else 0.0
            ),

            "can_assassinate": (
                1.0 if self.coins >= 3 else 0.0
            ),

            "turn_progress": (
                game.current_player / max(len(game.players), 1)
            ),

            "game_length": game_length,
        }

    @staticmethod
    def _dot(
        weights: dict[str, float],
        features: dict[str, float],
    ) -> float:
        return sum(
            weights.get(feature, 0.0) * value
            for feature, value in features.items()
        )

    # ------------------------------------------------------------------
    # Action selection
    # ------------------------------------------------------------------

    def _get_action_sets(
        self,
    ) -> tuple[list[str], list[str]]:
        """
        Return:

            honest_actions
            bluff_actions

        This preserves the behavior of WeightedParamBotV2 while allowing
        the probability of choosing either set to depend on state.
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

    def _action_weight(
        self,
        action: str,
        features: dict[str, float],
    ) -> float:
        return _safe_exp(
            self._dot(
                self.genome.action_weights[action],
                features,
            )
        )

    def _weighted_choice(
        self,
        actions: Iterable[str],
        features: dict[str, float],
    ) -> str:
        actions = list(actions)

        if not actions:
            raise ValueError("Cannot choose from an empty action list.")

        weights = [
            self._action_weight(action, features)
            for action in actions
        ]

        return self.rng.choices(
            actions,
            weights=weights,
            k=1,
        )[0]

    def _probability(
        self,
        weights: dict[str, float],
        features: dict[str, float],
    ) -> float:
        return _sigmoid(self._dot(weights, features))

    def choose_action(self, game: Game) -> dict:
        if game.current.id != self.id:
            raise ValueError("It is not this agent's turn.")

        # The engine requires a Coup at 10+ coins. Do not let the genome
        # violate a game rule.
        if self.coins >= 10:
            action = "coup"
        else:
            features = self._features(game)

            honest_actions, bluff_actions = self._get_action_sets()

            bluff_probability = self._probability(
                self.genome.bluff_weights,
                features,
            )

            should_bluff = (
                bool(bluff_actions)
                and self.rng.random() < bluff_probability
            )

            if should_bluff:
                action = self._weighted_choice(
                    bluff_actions,
                    features,
                )
            else:
                action = self._weighted_choice(
                    honest_actions,
                    features,
                )

        target_id = None

        if action in (
            "coup",
            "assassinate",
            "steal",
        ):
            target_id = self._choose_target(game)

        return game.perform_action(
            self.id,
            action,
            target_id=target_id,
        )

    # ------------------------------------------------------------------
    # Target selection
    # ------------------------------------------------------------------

    def _choose_target(self, game: Game) -> str:
        opponents = [
            player
            for player in game.alive_players
            if player.id != self.id
        ]

        if not opponents:
            raise ValueError("No valid opponents are available.")

        scored = []

        for opponent in opponents:
            features = {
                "bias": 1.0,

                "opponent_coins": min(
                    opponent.coins / 10.0,
                    1.5,
                ),

                "opponent_influence": (
                    opponent.influence / 2.0
                ),

                "coin_advantage": max(
                    -1.0,
                    min(
                        1.0,
                        (
                            opponent.coins
                            - self.coins
                        )
                        / 10.0,
                    ),
                ),

                "influence_advantage": max(
                    -1.0,
                    min(
                        1.0,
                        (
                            opponent.influence
                            - self.influence
                        )
                        / 2.0,
                    ),
                ),

                "one_influence": (
                    1.0 if opponent.influence == 1 else 0.0
                ),
            }

            score = self._dot(
                self.genome.target_weights,
                features,
            )

            scored.append((opponent, score))

        # Softmax target selection.
        max_score = max(score for _, score in scored)

        weights = [
            math.exp(
                max(-20.0, min(20.0, score - max_score))
            )
            for _, score in scored
        ]

        return self.rng.choices(
            [opponent.id for opponent, _ in scored],
            weights=weights,
            k=1,
        )[0]

    # ------------------------------------------------------------------
    # Responses
    # ------------------------------------------------------------------

    def decide(
        self,
        kind: str,
        context: dict[str, object],
    ) -> object:

        # The Game does not pass the Game object into decide(), so use
        # state available on the Player itself for response decisions.
        #
        # The response feature vector is deliberately kept compatible
        # with the main feature representation.

        if kind == "challenge":
            features = self._response_features(context)

            probability = self._probability(
                self.genome.challenge_weights,
                features,
            )

            return self.rng.random() < probability

        if kind == "block":
            if self.id not in context["eligible_blockers"]:
                return None

            features = self._response_features(context)

            probability = self._probability(
                self.genome.block_weights,
                features,
            )

            if self.rng.random() >= probability:
                return None

            action = context["action"]

            if action == "foreign_aid":
                return {
                    "blocker_id": self.id,
                }

            allowed_roles = list(
                context["allowed_roles"]
            )

            owned_roles = {
                card.role.value
                for card in self.cards
                if not card.revealed
            }

            truthful = [
                role
                for role in allowed_roles
                if role in owned_roles
            ]

            if truthful:
                role = self.rng.choice(truthful)
            else:
                role = self.rng.choice(allowed_roles)

            return {
                "blocker_id": self.id,
                "role": role,
            }

        if kind == "reveal_influence":
            cards = context["cards"]

            # Prefer revealing already-known-to-be-less-useful cards
            # only through randomization here. The genome can evolve
            # response probabilities without needing hidden information.
            return self.rng.choice(cards)["index"]

        if kind == "exchange":
            return self.rng.sample(
                range(len(context["cards"])),
                context["keep_count"],
            )

        raise ValueError(f"Unknown decision type: {kind}")

    def _response_features(
        self,
        context: dict[str, object],
    ) -> dict[str, float]:
        """
        Build a state vector from the information supplied by Game.decide.

        This intentionally never invents hidden information.
        """

        features = {
            feature: 0.0
            for feature in FEATURES
        }

        features["bias"] = 1.0
        features["own_coins"] = min(
            self.coins / 10.0,
            1.5,
        )
        features["own_influence"] = self.influence / 2.0
        features["can_coup"] = (
            1.0 if self.coins >= 7 else 0.0
        )
        features["can_assassinate"] = (
            1.0 if self.coins >= 3 else 0.0
        )
        features["self_one_influence"] = (
            1.0 if self.influence <= 1 else 0.0
        )

        action = context.get("action")

        if action == "foreign_aid":
            features["opponent_coins"] = 0.2

        if action in (
            "assassinate",
            "steal",
        ):
            features["opponent_influence"] = 0.5

        return features