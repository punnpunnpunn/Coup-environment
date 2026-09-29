Coup Environment
================

Agents submit one complete turn through `Game.perform_action`. The method
validates the action, resolves challenges and blocks, applies costs and effects,
advances to the next living player, and returns the public game state.

```python
from agents.random_agent import RandomAgent
from src.game import Game
from src.player import Player

players = [Player(f"p{i}", f"Player {i}") for i in range(4)]
game = Game(players)
agents = {
    player.id: RandomAgent(player.id, seed=index)
    for index, player in enumerate(players)
}

while game.winner is None:
    state = agents[game.current.id].play_turn(game)

print(f"Winner: {game.winner.name}")
```

`RandomAgent` randomly selects any currently legal action and target, then
randomly decides whether to challenge or block and which cards to reveal or
keep. Pass a seed to make an agent's decisions reproducible.

Action names are `income`, `foreign_aid`, `coup`, `tax`, `assassinate`,
`exchange`, and `steal`. Targeted actions take `target_id`. `duke`, `assassin`,
`ambassador`, and `captain` are accepted aliases.
Games support 2-6 players so the Court retains the cards needed for exchanges.

The decision callback receives a decision kind and context:

- `challenge`: return `True` or `False`.
- `block`: return `None`, or a mapping with `blocker_id`. For assassination,
	include `role: "contessa"`; for a steal, include `role: "ambassador"` or
	`role: "captain"`. Foreign Aid uses Duke automatically.
- `reveal_influence`: return one of the supplied zero-based card indices.
- `exchange`: return the required number of distinct zero-based card indices.

Run the rule tests with `python -m unittest discover -s tests`.
