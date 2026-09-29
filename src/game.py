import random
from collections.abc import Callable
from dataclasses import dataclass, field

from src.cards import ALL_ROLES, Card, Role
from src.player import Player


DecisionProvider = Callable[[str, dict[str, object]], object]


@dataclass
class Game:
    players: list[Player]
    deck: list[Card] = field(default_factory=list)
    current_player: int = 0
    log: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not 2 <= len(self.players) <= 6:
            raise ValueError("Coup requires 2-6 players so the Court can support exchanges.")
        if len({player.id for player in self.players}) != len(self.players):
            raise ValueError("Player IDs must be unique.")

        self._create_deck()
        self._deal_cards()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _create_deck(self):
        self.deck = [
            Card(role)
            for role in ALL_ROLES
            for _ in range(3)
        ]
        random.shuffle(self.deck)

    def _deal_cards(self):
        for player in self.players:
            player.coins = 2
            player.cards = [
                self.deck.pop(),
                self.deck.pop(),
            ]

    # ------------------------------------------------------------------
    # Game state
    # ------------------------------------------------------------------

    @property
    def current(self) -> Player:
        return self.players[self.current_player]

    @property
    def alive_players(self) -> list[Player]:
        return [p for p in self.players if p.alive]

    @property
    def winner(self) -> Player | None:
        alive = self.alive_players
        return alive[0] if len(alive) == 1 else None

    def state_for(self, player_id: str | None = None) -> dict:
        """
        Return a serializable view of the game.

        If player_id is provided, that player's cards are visible
        while everybody else's cards remain hidden.
        """
        state = {
            "current_player": self.current.id,
            "winner": self.winner.id if self.winner is not None else None,
            "log": list(self.log),
            "players": [],
        }

        for player in self.players:
            player_state = {
                "id": player.id,
                "name": player.name,
                "coins": player.coins,
                "influence": player.influence,
                "cards": [],
            }

            for card in player.cards:
                visible = (
                    player.id == player_id
                    or card.revealed
                )

                player_state["cards"].append(
                    card.role.value if visible else "hidden"
                )

            state["players"].append(player_state)

        return state

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def perform_action(
        self,
        player_id: str,
        action: str,
        target_id: str | None = None,
        decision_provider: DecisionProvider | None = None,
    ) -> dict:
        deck_before = list(self.deck)
        current_before = self.current_player
        log_length_before = len(self.log)
        players_before = [
            (player, player.coins, list(player.cards)) for player in self.players
        ]
        card_states = {card: card.revealed for card in self.deck}
        for _player, _coins, cards in players_before:
            card_states.update({card: card.revealed for card in cards})

        try:
            return self._resolve_action(
                player_id, action, target_id, decision_provider
            )
        except Exception:
            self.current_player = current_before
            self.deck[:] = deck_before
            del self.log[log_length_before:]
            for player, coins, cards in players_before:
                player.coins = coins
                player.cards[:] = cards
            for card, revealed in card_states.items():
                card.revealed = revealed
            raise

    def _resolve_action(
        self,
        player_id: str,
        action: str,
        target_id: str | None = None,
        decision_provider: DecisionProvider | None = None,
    ) -> dict:
        """Resolve one complete turn through a structured decision callback.

        The callback receives (kind, context) and returns a bool for
        ``challenge``, None or a block dict for ``block``, a card index for
        ``reveal_influence``, and kept-card indices for ``exchange``. Card
        indices are zero-based.
        """
        actor = self._require_current_player(player_id)
        if self.winner is not None:
            raise ValueError("The game is already over.")

        action = action.strip().lower().replace(" ", "_")
        action = {
            "duke": "tax",
            "assassin": "assassinate",
            "ambassador": "exchange",
            "captain": "steal",
        }.get(action, action)
        valid_actions = {
            "income", "foreign_aid", "coup", "tax", "assassinate", "exchange", "steal"
        }
        if action not in valid_actions:
            raise ValueError(f"Unknown action: {action}")
        if actor.coins >= 10 and action != "coup":
            raise ValueError("Player must coup when they have 10+ coins.")

        target = None
        if action in ("coup", "assassinate", "steal"):
            if target_id is None:
                raise ValueError("This action requires a target.")
            target = self._get_player(target_id)
            if not target.alive:
                raise ValueError("Target is eliminated.")
            if target.id == actor.id:
                raise ValueError("Cannot target yourself.")

        if action == "coup" and actor.coins < 7:
            raise ValueError("Coup costs 7 coins.")
        if action == "assassinate" and actor.coins < 3:
            raise ValueError("Assassination costs 3 coins.")

        descriptions = {
            "income": "takes Income",
            "foreign_aid": "claims Foreign Aid",
            "coup": "launches a Coup",
            "tax": "claims Duke for Tax",
            "assassinate": "claims Assassin",
            "exchange": "claims Ambassador to Exchange",
            "steal": "claims Captain to Steal",
        }
        if target is not None:
            descriptions[action] += f" against {target.name}"
        self._record_event(f"{actor.name} {descriptions[action]}.")

        if action == "income":
            actor.coins += 1
            self._record_event(f"{actor.name} gains 1 coin (now {actor.coins}).")
        elif action == "foreign_aid":
            if not self._check_block(actor, action, target, decision_provider):
                actor.coins += 2
                self._record_event(f"{actor.name} gains 2 coins (now {actor.coins}).")
        elif action == "coup":
            actor.coins -= 7
            self._record_event(f"{actor.name} pays 7 coins (now {actor.coins}).")
            self._lose_influence(target, decision_provider)
        elif action == "tax":
            if self._check_challenge(actor, Role.DUKE, decision_provider):
                self._record_event("The Tax claim is disproven; no coins are taken.")
            else:
                actor.coins += 3
                self._record_event(f"{actor.name} gains 3 Tax coins (now {actor.coins}).")
        elif action == "assassinate":
            if not self._check_challenge(actor, Role.ASSASSIN, decision_provider):
                blocked = target.alive and self._check_block(
                    actor, action, target, decision_provider
                )
                actor.coins -= 3
                self._record_event(
                    f"{actor.name} pays 3 coins for the assassination (now {actor.coins})."
                )
                if not blocked and target.alive:
                    self._lose_influence(target, decision_provider)
            else:
                self._record_event("The assassination claim fails; no fee is paid.")
        elif action == "exchange":
            if self._check_challenge(actor, Role.AMBASSADOR, decision_provider):
                self._record_event("The Exchange claim is disproven; no cards are exchanged.")
            else:
                self._exchange(actor, decision_provider)
                self._record_event(f"{actor.name} exchanges cards with the Court.")
        elif action == "steal":
            if self._check_challenge(actor, Role.CAPTAIN, decision_provider):
                self._record_event("The Steal claim is disproven; no coins are transferred.")
            else:
                if (
                    target.alive
                    and not self._check_block(actor, action, target, decision_provider)
                    and target.alive
                ):
                    stolen = min(2, target.coins)
                    target.coins -= stolen
                    actor.coins += stolen
                    self._record_event(
                        f"{actor.name} steals {stolen} coin(s) from {target.name}."
                    )
                elif not target.alive:
                    self._record_event(
                        f"{target.name} was eliminated during the challenge; the steal does not resolve."
                    )

        self._end_turn()
        return self.state_for(player_id)

    def _check_challenge(
        self,
        claimant: Player,
        role: Role,
        decision_provider: DecisionProvider | None,
    ) -> bool:
        for step in range(1, len(self.players) + 1):
            challenger = self.players[(self.current_player + step) % len(self.players)]
            if not challenger.alive or challenger.id == claimant.id:
                continue
            should_challenge = self._decide(
                decision_provider,
                "challenge",
                {
                    "challenger_id": challenger.id,
                    "challenger_name": challenger.name,
                    "claimant_id": claimant.id,
                    "role": role.value,
                    "decision_player_id": challenger.id,
                },
            )
            if not isinstance(should_challenge, bool):
                raise ValueError("Challenge decisions must be booleans.")
            if should_challenge:
                self._record_event(
                    f"{challenger.name} challenges {claimant.name}'s {role.value} claim."
                )
                return self._challenge(challenger, claimant, role, decision_provider)
            self._record_event(
                f"{challenger.name} does not challenge {claimant.name}'s {role.value} claim."
            )
        return False

    def _challenge(
        self,
        challenger: Player,
        claimant: Player,
        role: Role,
        decision_provider: DecisionProvider | None,
    ) -> bool:
        revealed_card = next(
            (
                card
                for card in claimant.cards
                if card.role == role and not card.revealed
            ),
            None,
        )
        if revealed_card is None:
            self._record_event(
                f"{claimant.name} cannot prove the {role.value} claim."
            )
            self._lose_influence(claimant, decision_provider)
            return True

        self._record_event(
            f"{claimant.name} proves the {role.value} claim and returns that card to the Court."
        )
        claimant.cards.remove(revealed_card)
        revealed_card.revealed = False
        self.deck.append(revealed_card)
        random.shuffle(self.deck)
        replacement = self.deck.pop()
        claimant.cards.append(replacement)
        self._record_event(f"{claimant.name} draws a hidden replacement card.")
        self._lose_influence(challenger, decision_provider)
        return False

    def _check_block(
        self,
        actor: Player,
        action: str,
        target: Player | None,
        decision_provider: DecisionProvider | None,
    ) -> bool:
        if action == "foreign_aid":
            eligible = [
                player for player in self.alive_players if player.id != actor.id
            ]
            roles = [Role.DUKE.value]
        elif action == "assassinate":
            eligible = [target]
            roles = [Role.CONTESSA.value]
        elif action == "steal":
            eligible = [target]
            roles = [Role.AMBASSADOR.value, Role.CAPTAIN.value]
        else:
            raise ValueError(f"Action cannot be blocked: {action}")

        selection_context = {
            "actor_id": actor.id,
            "action": action,
            "target_id": target.id if target else None,
            "eligible_blockers": [player.id for player in eligible],
            "allowed_roles": roles,
        }
        blocker = None
        if action == "foreign_aid" and decision_provider is None:
            for candidate in eligible:
                selection_context["decision_player_id"] = candidate.id
                selection_context["eligible_blockers"] = [candidate.id]
                selection = self._decide(None, "block", selection_context)
                if selection is not None:
                    blocker = candidate
                    break
            else:
                self._record_event("No one blocks foreign aid.")
                return False
        else:
            if action != "foreign_aid":
                selection_context["decision_player_id"] = target.id
            selection = self._decide(
                decision_provider,
                "block",
                selection_context,
            )
        if selection is None:
            self._record_event(f"No one blocks {action.replace('_', ' ')}.")
            return False
        if not isinstance(selection, dict):
            raise ValueError("A block decision must be None or a block mapping.")

        blocker_id = selection.get("blocker_id")
        if blocker is None:
            blocker = self._get_player(blocker_id) if isinstance(blocker_id, str) else None
        if blocker is None or blocker not in eligible or not blocker.alive:
            raise ValueError("That player cannot block this action.")
        if action == "foreign_aid" and blocker_id != blocker.id:
            raise ValueError("A player can only submit their own block.")

        if action == "foreign_aid":
            block_role = Role.DUKE
        else:
            try:
                block_role = Role(selection.get("role"))
            except ValueError as error:
                raise ValueError("Invalid blocking role.") from error
            if block_role.value not in roles:
                raise ValueError("That role cannot block this action.")

        self._record_event(
            f"{blocker.name} claims {block_role.value} to block {action.replace('_', ' ')}."
        )
        blocked = not self._check_challenge(blocker, block_role, decision_provider)
        if blocked:
            self._record_event(f"{blocker.name}'s block succeeds.")
        else:
            self._record_event(f"{blocker.name}'s block is disproven; the action continues.")
        return blocked

    def _lose_influence(
        self,
        player: Player,
        decision_provider: DecisionProvider | None,
    ):
        if player.influence <= 1:
            card = player.lose_influence()
            self._record_event(
                f"{player.name} loses influence, revealing {card.role.value}."
            )
            return card

        active_cards = [
            (index, card)
            for index, card in enumerate(player.cards)
            if not card.revealed
        ]
        card_index = self._decide(
            decision_provider,
            "reveal_influence",
            {
                "player_id": player.id,
                "cards": [
                    {"index": index, "role": card.role.value}
                    for index, card in active_cards
                ],
            },
        )
        valid_indices = {index for index, _card in active_cards}
        if (
            isinstance(card_index, bool)
            or not isinstance(card_index, int)
            or card_index not in valid_indices
        ):
            raise ValueError("Invalid influence card index.")
        card = player.reveal_card(card_index)
        self._record_event(
            f"{player.name} loses influence, revealing {card.role.value}."
        )
        return card

    def _exchange(
        self,
        player: Player,
        decision_provider: DecisionProvider | None,
    ):
        if len(self.deck) < 2:
            raise ValueError("Not enough cards in the Court to exchange.")

        revealed_cards = [card for card in player.cards if card.revealed]
        cards = [card for card in player.cards if not card.revealed]
        drawn = [self.deck.pop(), self.deck.pop()]
        cards.extend(drawn)
        keep_count = len(player.cards) - len(revealed_cards)
        choices = self._decide(
            decision_provider,
            "exchange",
            {
                "player_id": player.id,
                "cards": [
                    {"index": index, "role": card.role.value}
                    for index, card in enumerate(cards)
                ],
                "keep_count": keep_count,
            },
        )
        valid = (
            isinstance(choices, (list, tuple))
            and len(choices) == keep_count
            and all(
                isinstance(index, int)
                and not isinstance(index, bool)
                and 0 <= index < len(cards)
                for index in choices
            )
            and len(set(choices)) == len(choices)
        )
        if not valid:
            self.deck.extend(reversed(drawn))
            raise ValueError("Exchange must select distinct valid card indices.")

        kept_indices = set(choices)
        player.cards = revealed_cards + [cards[index] for index in choices]
        self.deck.extend(
            card for index, card in enumerate(cards) if index not in kept_indices
        )
        random.shuffle(self.deck)

    def _record_event(self, message: str):
        self.log.append(message)

    def _decide(
        self,
        decision_provider: DecisionProvider | None,
        kind: str,
        context: dict[str, object],
    ) -> object:
        if decision_provider is not None:
            return decision_provider(kind, context)

        player_id = context.get("decision_player_id", context.get("player_id"))
        if isinstance(player_id, str):
            player = self._get_player(player_id)
            player_decision = getattr(player, "decide", None)
            if callable(player_decision):
                return player_decision(kind, context)
        return self._console_decision(kind, context)

    def _console_decision(self, kind: str, context: dict[str, object]) -> object:
        if kind == "challenge":
            answer = input(
                f"{context['challenger_name']}, challenge? [y/n]: "
            ).strip().lower()
            while answer not in ("y", "n"):
                answer = input("Invalid choice. Challenge? [y/n]: ").strip().lower()
            return answer == "y"

        if kind == "block":
            answer = input("Block? [y/n]: ").strip().lower()
            while answer not in ("y", "n"):
                answer = input("Invalid choice. Block? [y/n]: ").strip().lower()
            if answer == "n":
                return None

            action = context["action"]
            if action == "foreign_aid":
                eligible = context["eligible_blockers"]
                blocker_id = input(f"Blocker ID {eligible}: ").strip()
                while blocker_id not in eligible:
                    blocker_id = input(f"Choose an eligible blocker {eligible}: ").strip()
                return {"blocker_id": blocker_id}

            if action == "assassinate":
                return {
                    "blocker_id": context["target_id"],
                    "role": Role.CONTESSA.value,
                }

            role_choice = input("Block with [1] ambassador or [2] captain: ").strip()
            while role_choice not in ("1", "2"):
                role_choice = input("Choose [1] ambassador or [2] captain: ").strip()
            role = Role.AMBASSADOR if role_choice == "1" else Role.CAPTAIN
            return {"blocker_id": context["target_id"], "role": role.value}

        if kind == "reveal_influence":
            cards = context["cards"]
            for option, card in enumerate(cards, start=1):
                print(f"  [{option}] {card['role']}")
            choice = input(f"Choose a card to reveal [1-{len(cards)}]: ").strip()
            while not choice.isdigit() or not 1 <= int(choice) <= len(cards):
                choice = input(f"Invalid choice. Choose [1-{len(cards)}]: ").strip()
            return cards[int(choice) - 1]["index"]

        if kind == "exchange":
            cards = context["cards"]
            keep_count = context["keep_count"]
            for option, card in enumerate(cards, start=1):
                print(f"  [{option}] {card['role']}")
            choices = []
            for choice_number in range(keep_count):
                choice = input(
                    f"Choose card {choice_number + 1} to keep [1-{len(cards)}]: "
                ).strip()
                while (
                    not choice.isdigit()
                    or not 1 <= int(choice) <= len(cards)
                    or int(choice) - 1 in choices
                ):
                    choice = input("Choose a distinct listed card: ").strip()
                choices.append(int(choice) - 1)
            return choices

        raise ValueError(f"Unknown decision type: {kind}")
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_player(self, player_id: str) -> Player:
        for player in self.players:
            if player.id == player_id:
                return player

        raise ValueError(f"Unknown player: {player_id}")

    def _require_current_player(self, player_id: str) -> Player:
        if self.current.id != player_id:
            raise ValueError("It is not this player's turn.")

        if not self.current.alive:
            raise ValueError("Player is eliminated.")

        return self.current

    def _end_turn(self):
        winner = self.winner
        if winner is not None:
            self.current_player = self.players.index(winner)
            self._record_event(f"{winner.name} wins the game.")
            return

        start = self.current_player

        while True:
            self.current_player = (
                self.current_player + 1
            ) % len(self.players)

            if self.players[self.current_player].alive:
                self._record_event(f"It is now {self.current.name}'s turn.")
                break

            if self.current_player == start:
                break
