from agents.adaptive_weighted_bot import AdaptiveWeightedBot
from genetic_adaptive_algo import AdaptiveGeneticTrainer

from agents.passive_agent import PassiveAgent
from agents.always_duke import AlwaysDuke
from agents.honest_random import HonestRandom
from agents.duke_fish import DukeFish
from agents.belief_honest_random import BeliefHonestRandom


def opponent_factory(game_number, rng):
    """
    Construct a fresh set of opponents for every game.

    Replace the contents of this function with the Bot type
    you want to develop an anti-strategy against.
    """

    return [
        BeliefHonestRandom(
            "opponent1",
            "Opponent 1",
            print_turns=False,
        ),

        BeliefHonestRandom(
            "opponent2",
            "Opponent 2",
            print_turns=False,
        ),

        BeliefHonestRandom(
            "opponent3",
            "Opponent 3",
            print_turns=False,
        ),
    ]


def main():
    trainer = AdaptiveGeneticTrainer(
        opponent_factory=opponent_factory,

        population_size=10,

        # Increase this for more reliable fitness estimates.
        games_per_candidate=1000,

        generations=100,

        elite_count=3,
        tournament_size=4,

        mutation_rate=0.06,
        mutation_sigma=0.30,

        crossover_rate=0.85,

        seed=12345,

        print_progress=True,
        print_interval=5,
    )

    best = trainer.train()

    print()
    print(
        f"Training complete: "
        f"{best.wins}/{best.games} wins "
        f"({best.win_rate:.2%})"
    )


if __name__ == "__main__":
    main()