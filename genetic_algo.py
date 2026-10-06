import random
from dataclasses import dataclass

from agents.weighted_param_bot import WeightedParamBot
from agents.weighted_param_bot_v2 import WeightedParamBotV2
from agents.passive_agent import create_passive_agent
from agents.always_duke import create_always_duke
from src.game import Game
from src.player import Player


ACTION_NAMES = (
    "income",
    "foreign_aid",
    "coup",
    "tax",
    "assassinate",
    "exchange",
    "steal",
)


@dataclass
class StrategyWeights:
    """
    The parameters that define a WeightedParamBot's action preferences.
    """

    income: float
    foreign_aid: float
    coup: float
    tax: float
    assassinate: float
    exchange: float
    steal: float

    def as_dict(self) -> dict[str, float]:
        return {
            "income": self.income,
            "foreign_aid": self.foreign_aid,
            "coup": self.coup,
            "tax": self.tax,
            "assassinate": self.assassinate,
            "exchange": self.exchange,
            "steal": self.steal,
        }

    def copy(self) -> "StrategyWeights":
        return StrategyWeights(
            income=self.income,
            foreign_aid=self.foreign_aid,
            coup=self.coup,
            tax=self.tax,
            assassinate=self.assassinate,
            exchange=self.exchange,
            steal=self.steal,
        )


@dataclass
class EvaluationResult:
    """
    Results from testing one candidate strategy.
    """

    weights: StrategyWeights
    wins: int
    games: int

    @property
    def win_rate(self) -> float:
        if self.games == 0:
            return 0.0
        return self.wins / self.games


class AntiStrategyOptimizer:
    """
    Evolves a WeightedParamBot toward a strategy that performs well
    against a fixed target strategy.

    Each game consists of:

        1 candidate WeightedParamBot
        3 copies of the target WeightedParamBot

    A generation consists of the current best strategy plus a number
    of mutations of it.

    The highest-performing candidate becomes the parent for the
    following generation.
    """

    def __init__(
        self,
        target_bot_factory,
        starting_weights: StrategyWeights = StrategyWeights(
            income=1.0,
            foreign_aid=1.0,
            coup=1.0,
            tax=1.0,
            assassinate=1.0,
            exchange=1.0,
            steal=1.0,
        ),
        num_opponents: int = 2,
        bluff_percent: float = 0.0,
        challenge_percent: float = 0.0,
        population_size: int = 10,
        games_per_candidate: int = 1000,
        mutation_strength: float = 0.10,
        max_rounds: int = 50,
        target_win_rate: float = 0.50,
        seed: int | None = None,
    ):
        if population_size < 1:
            raise ValueError("population_size must be at least 1.")

        if games_per_candidate < 1:
            raise ValueError("games_per_candidate must be at least 1.")

        if mutation_strength < 0:
            raise ValueError("mutation_strength cannot be negative.")

        if max_rounds < 1:
            raise ValueError("max_rounds must be at least 1.")

        if not 0 <= target_win_rate <= 1:
            raise ValueError("target_win_rate must be between 0 and 1.")

        self.target_bot_factory = target_bot_factory
        self.starting_weights = starting_weights

        self.num_opponents = num_opponents

        self.bluff_percent = bluff_percent
        self.challenge_percent = challenge_percent

        self.population_size = population_size
        self.games_per_candidate = games_per_candidate
        self.mutation_strength = mutation_strength
        self.max_rounds = max_rounds
        self.target_win_rate = target_win_rate

        self.rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Strategy creation
    # ------------------------------------------------------------------

    def _create_candidate(
        self,
        weights: StrategyWeights,
        player_id: str,
        name: str,
        seed: int,
    ) -> Player:
        """
        Create a WeightedParamBot from a set of strategy weights.
        """

        return WeightedParamBotV2(
            player_id=player_id,
            name=name,
            seed=seed,
            print_turns=False,
            bluff_percent=self.bluff_percent,
            challenge_percent=self.challenge_percent,

            income_weight=weights.income,
            foreign_aid_weight=weights.foreign_aid,
            coup_weight=weights.coup,
            tax_weight=weights.tax,
            assassinate_weight=weights.assassinate,
            exchange_weight=weights.exchange,
            steal_weight=weights.steal,
        )

    def _create_mutation(
        self,
        parent: StrategyWeights,
    ) -> StrategyWeights:
        """
        Create a small mutation of a strategy.

        Each parameter is independently multiplied by a random factor
        centered around 1.0.

        For example, with mutation_strength = 0.10:

            5.0 -> somewhere approximately between 4.5 and 5.5

        This keeps the mutation proportional to the size of the
        parameter rather than using the same absolute change for
        every parameter.
        """

        child = parent.copy()

        for action in ACTION_NAMES:
            value = getattr(child, action)

            # A uniform mutation keeps the implementation simple and
            # makes mutation_strength easy to interpret.
            multiplier = self.rng.uniform(
                1.0 - self.mutation_strength,
                1.0 + self.mutation_strength,
            )

            new_value = value * multiplier

            # Never allow a negative weight.
            new_value = max(0.0, new_value)

            setattr(child, action, new_value)

        # It is possible, although unlikely, for every weight to become
        # zero if the parent itself contains only zeroes.
        if sum(child.as_dict().values()) == 0:
            random_action = self.rng.choice(ACTION_NAMES)
            setattr(child, random_action, 1.0)

        return child

    # ------------------------------------------------------------------
    # Game evaluation
    # ------------------------------------------------------------------

    def _evaluate_candidate(
        self,
        weights: StrategyWeights,
        games: int | None = None,
    ) -> EvaluationResult:
        """
        Test one candidate against three copies of the target strategy.
        """

        if games is None:
            games = self.games_per_candidate

        wins = 0

        for game_number in range(games):
            candidate_seed = self.rng.randrange(2**32)

            candidate = self._create_candidate(
                weights=weights,
                player_id="candidate",
                name="Candidate",
                seed=candidate_seed,
            )

            target_players = [
                self.target_bot_factory(
                    player_id=f"target-{i}",
                    name=f"Target {i}",
                    seed=self.rng.randrange(2**32),
                )
                for i in range(self.num_opponents)
            ]

            players = [
                candidate,
                *target_players,
            ]

            # Randomize turn order.
            self.rng.shuffle(players)

            game = Game(players, print_turns=False)

            while game.winner is None:
                game.current.choose_action(game)

            if game.winner.id == "candidate":
                wins += 1

        return EvaluationResult(
            weights=weights.copy(),
            wins=wins,
            games=games,
        )

    # ------------------------------------------------------------------
    # Population
    # ------------------------------------------------------------------

    def _create_initial_population(self) -> list[StrategyWeights]:
        """
        The first generation consists of:

            - the exact target strategy
            - several mutations of it
        """

        population = [
            self.starting_weights.copy()
        ]

        while len(population) < self.population_size:
            population.append(
                self._create_mutation(self.starting_weights)
            )

        return population

    def _create_next_population(
        self,
        winner: StrategyWeights,
    ) -> list[StrategyWeights]:
        """
        Create the next generation from the best strategy.

        The winning strategy is preserved unchanged, and all other
        members are mutations of it.
        """

        population = [
            winner.copy()
        ]

        while len(population) < self.population_size:
            population.append(
                self._create_mutation(winner)
            )

        return population

    # ------------------------------------------------------------------
    # Optimization
    # ------------------------------------------------------------------

    def optimize(self) -> EvaluationResult:
        """
        Run the evolutionary search.

        Returns the best strategy discovered.
        """

        population = self._create_initial_population()

        best_result: EvaluationResult | None = None

        for round_number in range(1, self.max_rounds + 1):
            print()
            print("=" * 60)
            print(f"Generation {round_number}")
            print("=" * 60)

            results = []

            for candidate_number, weights in enumerate(population):
                print(
                    f"Testing candidate "
                    f"{candidate_number + 1}/{len(population)}..."
                )

                result = self._evaluate_candidate(weights)

                results.append(result)

                print(
                    f"  Win rate: "
                    f"{result.wins}/{result.games} "
                    f"({result.win_rate:.2%})"
                )

                print(
                    f"  Weights: {result.weights.as_dict()}"
                )

            # Highest win rate wins the generation.
            winner = max(
                results,
                key=lambda result: result.win_rate,
            )

            print()
            print("Generation winner:")
            print(
                f"  Win rate: {winner.win_rate:.2%}"
            )
            print(
                f"  Weights: {winner.weights.as_dict()}"
            )

            if (
                best_result is None
                or winner.win_rate > best_result.win_rate
            ):
                best_result = winner

            # Stop once the desired anti-strategy performance
            # has been achieved.
            if winner.win_rate >= self.target_win_rate:
                print()
                print(
                    f"Target win rate of "
                    f"{self.target_win_rate:.2%} reached."
                )
                break

            # Use the generation winner as the parent for the
            # next generation.
            population = self._create_next_population(
                winner.weights
            )

        if best_result is None:
            raise RuntimeError("Optimizer produced no results.")

        print()
        print("=" * 60)
        print("Optimization complete")
        print("=" * 60)
        print(
            f"Best win rate: {best_result.win_rate:.2%}"
        )
        print(
            f"Best weights: {best_result.weights.as_dict()}"
        )

        return best_result


# ----------------------------------------------------------------------
# Example usage
# ----------------------------------------------------------------------

if __name__ == "__main__":
    target = StrategyWeights(
        income=1.0,
        foreign_aid=1.0,
        coup=1.0,
        tax=1.0,
        assassinate=1.0,
        exchange=1.0,
        steal=1.0,
    )

    start = StrategyWeights(
        income=0.299981009486409,
        foreign_aid=10.0,
        coup=0.5255674038567602, 
        tax=0.07395424978955586, 
        assassinate=0.8607068155503209, 
        exchange=0.42732524228008906, 
        steal=0.4778216512613571
    )

    optimizer = AntiStrategyOptimizer(
        target_bot_factory=create_always_duke,
        starting_weights=start,

        num_opponents = 2,
        
        # These remain fixed during optimization.
        bluff_percent=0.5,
        challenge_percent=0.5,

        # Number of strategies tested per generation.
        population_size=10,

        # Number of games played by each strategy.
        games_per_candidate=1000,

        # Maximum percentage change applied to each weight
        # when creating a mutation.
        mutation_strength=0.10,

        # Maximum number of generations.
        max_rounds=500,

        # Stop early once the anti-strategy wins this often.
        target_win_rate=1,

        seed=42,
    )

    result = optimizer.optimize()

    print()
    print("Final anti-strategy:")
    print(result.weights.as_dict())
