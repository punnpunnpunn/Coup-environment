# Coup

A Python environment for playing Coup with human players and agents.

## Rules

### Setup and goal

The Court contains 15 character cards: three each of Duke, Assassin, Captain,
Ambassador, and Contessa. Each player starts with two face-down influence cards
and two coins. The game ends when only one player has influence remaining.

Players take turns clockwise. On a turn, choose exactly one action. A player
starting their turn with 10 or more coins must Coup. When losing influence, a
player reveals one of their face-down cards; revealed cards stay visible and no
longer provide influence. A player with no influence is eliminated.

### Actions

| Action | Effect | Challenge or block |
| --- | --- | --- |
| Income | Take 1 coin. | Cannot be blocked or challenged. |
| Foreign Aid | Take 2 coins. | Any other player may claim Duke to block it. |
| Coup | Pay 7 coins; target loses 1 influence. | Always succeeds; cannot be blocked or challenged. |
| Tax | Claim Duke and take 3 coins. | The Duke claim can be challenged. |
| Assassinate | Claim Assassin, pay 3 coins, and target loses 1 influence. | The Assassin claim can be challenged; target may claim Contessa to block. The fee remains spent if blocked. |
| Steal | Claim Captain and take up to 2 coins from a target. | The Captain claim can be challenged; target may claim Captain or Ambassador to block. |
| Exchange | Claim Ambassador, draw 2 Court cards, then return unwanted cards and shuffle the Court. | The Ambassador claim can be challenged. Revealed influence cannot be exchanged. |

Character actions and blocks are claims: players may tell the truth or bluff.
After a claim, each other living player may challenge in turn order. If the
claimant cannot prove the role with a face-down card, they lose influence and
the action or block fails. If the claimant proves it, they return that card to
the Court, shuffle, and draw a replacement; the challenger loses influence.
The action or block then proceeds.

### Implementation notes

- This implementation supports 2-6 players so the Court has enough cards for
  exchanges.
- Coins are treated as unlimited; there is no finite Treasury.
- Eliminated players' coins are not tracked in a Treasury.

## Run a game

From the repository root:

```bash
python main.py
```

The sample `main.py` roster contains the built-in Passive, Random, Always Duke,
and Honest Random agents. Replace or add entries in its `players` list to
configure a match. Human players can be added with `Player("id", "Name")`;
they will receive console prompts on their turns and when they need to respond.

Run all tests with:

```bash
python -m unittest discover -s tests
```

## Create an agent

An agent is a `Player` subclass. Implement `choose_action(game)` to submit one
complete turn through `Game.perform_action`. Return the resulting state if the
caller needs it. The game automatically calls an agent's `decide(kind,
context)` method when that agent is asked to challenge, block, reveal influence,
or exchange cards. If a responder is a regular `Player`, the game prompts in
the console instead.

An agent can override `observe(kind, context)` to track public game events. The
`Believer` agent uses those events to track role claims, challenge contradictions,
and clear a player's claim history after a successful exchange.

For example, this agent takes Income until forced to Coup, targeting a random
living opponent:

```python
import random

from src.game import Game
from src.player import Player


class IncomeCoupAgent(Player):
    def __init__(self, player_id: str, name: str, seed: int | None = None):
        super().__init__(player_id, name)
        self.rng = random.Random(seed)

    def choose_action(self, game: Game) -> dict:
        if game.current.id != self.id:
            raise ValueError("It is not this agent's turn.")

        if self.coins >= 10:
            opponents = [player for player in game.alive_players if player.id != self.id]
            action = "coup"
            target_id = self.rng.choice(opponents).id
        else:
            action = "income"
            target_id = None

        return game.perform_action(self.id, action, target_id=target_id)

    def decide(self, kind: str, context: dict[str, object]) -> object:
        if kind == "challenge":
            return False
        if kind == "block":
            return None
        if kind == "reveal_influence":
            return context["cards"][0]["index"]
        if kind == "exchange":
            return list(range(context["keep_count"]))
        raise ValueError(f"Unknown decision type: {kind}")
```

Save the class under `agents/`, then import it in `main.py` and add an instance
to `players`:

```python
from agents.income_coup import IncomeCoupAgent

players = [
    IncomeCoupAgent("agent-1", "Income/Coup", seed=1),
    Player("human-1", "Human player"),
]
```

### `choose_action` parameters

Use one of these action names: `income`, `foreign_aid`, `coup`, `tax`,
`assassinate`, `exchange`, or `steal`. The role aliases `duke`, `assassin`,
`ambassador`, and `captain` are also accepted. Coup, assassination, and steal
require a `target_id`.

### `decide` response types

- `challenge`: return `True` or `False`.
- `block`: return `None` to pass, or a mapping with `blocker_id`. Steal blocks
  also require `role` to be `"ambassador"` or `"captain"`; assassination uses
  `"contessa"`. Foreign Aid blocks use Duke automatically.
- `reveal_influence`: return one of the supplied zero-based card indices.
- `exchange`: return the required number of distinct zero-based candidate-card
  indices.

Decision contexts include `decision_player_id` for the player being asked,
along with action-specific information such as `allowed_roles`, `eligible_blockers`,
`cards`, and `keep_count`.