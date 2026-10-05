from __future__ import annotations

import random
from dataclasses import dataclass

from src.game import Game

from agents.adaptive_weighted_bot import (
    AdaptiveGenome,
    AdaptiveWeightedBot,
    ACTIONS,
    FEATURES,
)


@dataclass
class Individual:
    genome: AdaptiveGenome
    fitness: float = 0.0
    wins: int = 0
    games: int = 0

    @property
    def win_rate(self) -> float:
        if self.games == 0:
            return 0.0
        return self.wins / self.games


class AdaptiveGeneticTrainer:
    """
    Genetic algorithm for training AdaptiveWeightedBot.

    The trainer evaluates one candidate against a fixed opponent roster,
    then evolves the population based on candidate win rate.
    """

    def __init__(
        self,
        opponent_factory,
        population_size: int = 20,
        games_per_candidate: int = 500,
        generations: int = 50,
        elite_count: int = 2,
        tournament_size: int = 3,
        mutation_rate: float = 0.08,
        mutation_sigma: float = 0.25,
        crossover_rate: float = 0.8,
        seed: int | None = None,
        print_progress: bool = True,
        print_interval: int = 5,
    ):
        self.opponent_factory = opponent_factory
        self.population_size = population_size
        self.games_per_candidate = games_per_candidate
        self.generations = generations
        self.elite_count = elite_count
        self.tournament_size = tournament_size
        self.mutation_rate = mutation_rate
        self.mutation_sigma = mutation_sigma
        self.crossover_rate = crossover_rate
        self.print_progress = print_progress
        self.print_interval = print_interval

        self.rng = random.Random(seed)

    def print_best_genome(
            self,
            individual: Individual,
            generation: int,
    ) -> None:
        print()
        print("="*20)
        print(
            f"best genome at generation {generation}"
        )
        print(
            f"win rate={individual.win_rate:.2%}"
        )

        print()
        print("BEST_GENOME = AdaptiveGenome(")

        print(
            f"    action_weights="
            f"{repr(individual.genome.action_weights)},"
        )

        print(
            f"    bluff_weights="
            f"{repr(individual.genome.bluff_weights)},"
        )

        print(
            f"    challenge_weights="
            f"{repr(individual.genome.challenge_weights)},"
        )

        print(
            f"    block_weights="
            f"{repr(individual.genome.block_weights)},"
        )

        print(
            f"    target_weights="
            f"{repr(individual.genome.target_weights)},"
        )

        print(")")

        print("="*20)
        print()


    # ------------------------------------------------------------------
    # Population
    # ------------------------------------------------------------------

    def initialize_population(self) -> list[Individual]:
        return [
            Individual(
                genome=AdaptiveGenome.random(self.rng)
            )
            for _ in range(self.population_size)
        ]

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        individual: Individual,
    ) -> None:
        """
        Evaluate one genome.

        opponent_factory must return a fresh list of Player instances
        for every game.
        """

        individual.wins = 0
        individual.games = 0

        for game_number in range(self.games_per_candidate):
            candidate = AdaptiveWeightedBot(
                player_id="candidate",
                name="Candidate",
                genome=individual.genome.clone(),
                seed=self.rng.randrange(2**32),
                print_turns=False,
            )

            opponents = self.opponent_factory(
                game_number,
                self.rng,
            )

            players = [
                candidate,
                *opponents,
            ]

            self.rng.shuffle(players)

            game = Game(players)

            # Play the game.
            while game.winner is None:
                game.current.choose_action(game)

            individual.games += 1

            if game.winner.id == "candidate":
                individual.wins += 1

        individual.fitness = individual.win_rate

    def evaluate_population(
        self,
        population: list[Individual],
    ) -> None:
        for individual in population:
            self.evaluate(individual)

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def tournament_select(
        self,
        population: list[Individual],
    ) -> Individual:
        participants = self.rng.sample(
            population,
            min(
                self.tournament_size,
                len(population),
            ),
        )

        return max(
            participants,
            key=lambda individual: individual.fitness,
        )

    # ------------------------------------------------------------------
    # Crossover
    # ------------------------------------------------------------------

    def crossover(
        self,
        first: AdaptiveGenome,
        second: AdaptiveGenome,
    ) -> AdaptiveGenome:

        child = first.clone()

        # Action parameters.
        for action in ACTIONS:
            for feature in FEATURES:
                if self.rng.random() < 0.5:
                    child.action_weights[action][feature] = (
                        second.action_weights[action][feature]
                    )

        # Response parameters.
        for name in (
            "bluff_weights",
            "challenge_weights",
            "block_weights",
        ):
            first_weights = getattr(first, name)
            second_weights = getattr(second, name)
            child_weights = getattr(child, name)

            for feature in FEATURES:
                if self.rng.random() < 0.5:
                    child_weights[feature] = (
                        second_weights[feature]
                    )

        # Target parameters.
        for feature in child.target_weights:
            if self.rng.random() < 0.5:
                child.target_weights[feature] = (
                    second.target_weights[feature]
                )

        return child

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def _mutate_mapping(
        self,
        mapping: dict[str, float],
        sigma: float,
    ) -> None:
        for key in mapping:
            if self.rng.random() < self.mutation_rate:
                mapping[key] += self.rng.gauss(
                    0.0,
                    sigma,
                )

    def mutate(
        self,
        genome: AdaptiveGenome,
        sigma: float | None = None,
    ) -> AdaptiveGenome:

        sigma = (
            self.mutation_sigma
            if sigma is None
            else sigma
        )

        for action in ACTIONS:
            self._mutate_mapping(
                genome.action_weights[action],
                sigma,
            )

        self._mutate_mapping(
            genome.bluff_weights,
            sigma,
        )

        self._mutate_mapping(
            genome.challenge_weights,
            sigma,
        )

        self._mutate_mapping(
            genome.block_weights,
            sigma,
        )

        self._mutate_mapping(
            genome.target_weights,
            sigma,
        )

        return genome

    # ------------------------------------------------------------------
    # Evolution
    # ------------------------------------------------------------------

    def next_generation(
        self,
        population: list[Individual],
        generation: int,
    ) -> list[Individual]:

        population.sort(
            key=lambda individual: individual.fitness,
            reverse=True,
        )

        next_population = [
            Individual(
                genome=individual.genome.clone()
            )
            for individual in population[
                :self.elite_count
            ]
        ]

        # Gradually reduce mutation size as the search progresses.
        progress = generation / max(
            self.generations - 1,
            1,
        )

        sigma = self.mutation_sigma * (
            1.0 - 0.6 * progress
        )

        while len(next_population) < self.population_size:
            parent_a = self.tournament_select(population)
            parent_b = self.tournament_select(population)

            if (
                self.rng.random()
                < self.crossover_rate
            ):
                genome = self.crossover(
                    parent_a.genome,
                    parent_b.genome,
                )
            else:
                genome = parent_a.genome.clone()

            genome = self.mutate(
                genome,
                sigma=sigma,
            )

            next_population.append(
                Individual(genome=genome)
            )

        return next_population

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(
        self,
        initial_population: list[Individual] | None = None,
    ) -> Individual:

        population = (
            initial_population
            if initial_population is not None
            else self.initialize_population()
        )

        best_ever: Individual | None = None

        for generation in range(self.generations):
            self.evaluate_population(population)

            population.sort(
                key=lambda individual: individual.fitness,
                reverse=True,
            )

            generation_best = population[0]

            if (
                best_ever is None
                or generation_best.fitness
                > best_ever.fitness
            ):
                best_ever = Individual(
                    genome=generation_best.genome.clone(),
                    fitness=generation_best.fitness,
                    wins=generation_best.wins,
                    games=generation_best.games,
                )

            if self.print_progress:
                average_fitness = sum(
                    individual.fitness
                    for individual in population
                ) / len(population)

                print(
                    f"Generation {generation + 1}/{self.generations}: "
                    f"best={generation_best.win_rate:.4f}, "
                    f"average={average_fitness:.4f}"
                )

            if (
                self.print_interval > 0
                and (
                    (generation + 1) % self.print_interval == 0
                    or generation == self.generations - 1
                )
            ):
                self.print_best_genome(
                    best_ever,
                    generation + 1
                )

            if generation == self.generations - 1:
                break

            population = self.next_generation(
                population,
                generation,
            )

        assert best_ever is not None

        return best_ever