import random
from dataclasses import dataclass, field

from cards import ALL_ROLES, Card, Role
from player import Player


@dataclass
class Game:
    players: list[Player]
    deck: list[Card] = field(default_factory=list)
    current_player: int = 0

    def __post_init__(self):
        if len(self.players) < 2:
            raise ValueError("Coup requires at least 2 players.")

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

    def income(self, player_id: str):
        player = self._require_current_player(player_id)

        if player.coins >= 10:
            raise ValueError("Player must coup when they have 10+ coins.")

        player.coins += 1
        self._end_turn()

    def foreign_aid(self, player_id: str):
        player = self._require_current_player(player_id)

        if player.coins >= 10:
            raise ValueError("Player must coup when they have 10+ coins.")

        player.coins += 2
        self._end_turn()

    def coup(self, player_id: str, target_id: str):
        player = self._require_current_player(player_id)
        target = self._get_player(target_id)

        if player.coins < 7:
            raise ValueError("Coup costs 7 coins.")

        if not target.alive:
            raise ValueError("Target is eliminated.")

        if target.id == player.id:
            raise ValueError("Cannot coup yourself.")

        player.coins -= 7

        target.lose_influence()

        self._end_turn()

    def tax(self, player_id: str):
        player = self._require_current_player(player_id)

        if player.coins >= 10:
            raise ValueError("Player must coup when they have 10+ coins.")

        player.coins += 3
        self._end_turn()

    def assassinate(self, player_id: str, target_id: str):
        player = self._require_current_player(player_id)
        target = self._get_player(target_id)

        if player.coins < 3:
            raise ValueError("Assassination costs 3 coins.")

        if not target.alive:
            raise ValueError("Target is eliminated.")

        if target.id == player.id:
            raise ValueError("Cannot assassinate yourself.")

        player.coins -= 3

        target.lose_influence()

        self._end_turn()

    def exchange(self, player_id: str):
        player = self._require_current_player(player_id)

        drawn = [self.deck.pop(), self.deck.pop()]
        print(f"{player.name} draws {drawn[0].role.value} and {drawn[1].role.value} for exchange.")
        cards = player.cards + drawn
        for i in range(len(cards)):
            print(f"  [{i + 1}] {cards[i].role.value}")
        choice = []
        for i in range(len(player.cards)):
            chosen = " "
            while not chosen.isdigit() or int(chosen) < 1 or int(chosen) > len(cards) or int(chosen) in choice:
                chosen = input(f"Choose card {i + 1} to keep [1-{len(player.cards) + 2}]: ").strip()
            choice.append(int(chosen))
            print(f"  Chosen: {cards[int(chosen) - 1].role.value}")
        player.cards = [cards[i - 1] for i in choice]
        print(f"{player.name} keeps {', '.join(card.role.value for card in player.cards)} and returns the rest to the deck.")
        self.deck.extend(cards[i - 1] for i in range(1, len(cards) + 1) if i not in choice)
        random.shuffle(self.deck)

        self._end_turn()

    def steal(self, player_id: str, target_id: str):
        player = self._require_current_player(player_id)
        target = self._get_player(target_id)

        if not target.alive:
            raise ValueError("Target is eliminated.")

        if target.id == player.id:
            raise ValueError("Cannot steal from yourself.")

        stolen = min(2, target.coins)
        target.coins -= stolen
        player.coins += stolen

        self._end_turn()

    def challenge(self, challenger_id: str, player_id: str, role: Role):
        challenger = self._get_player(challenger_id)
        player = self._get_player(player_id)

        if player.id == challenger.id:
            raise ValueError("Cannot challenge yourself.")
        if not challenger.alive:
            raise ValueError("Challenger is eliminated.")
        if role in [card.role for card in player.cards] and not any(card.revealed for card in player.cards if card.role == role):
            # Player has the role and can reveal it.
            revealed_card = next(card for card in player.cards if card.role == role)
            revealed_card.revealed = True
            print(f"{player.name} reveals {revealed_card.role.value}.")
            # Player draws a new card to replace the revealed one.
            new_card = self.deck.pop()
            player.cards.remove(revealed_card)
            player.cards.append(new_card)
            self.deck.append(revealed_card)
            random.shuffle(self.deck)
            print(f"{player.name} draws a new card to replace the revealed one.")
            print(player.name + "'s cards: " + ", ".join(
                card.role.value if not card.revealed else f"{card.role.value} (revealed)"
                for card in player.cards
            ))
            # Challenger loses influence.
            challenger.lose_influence()
        else:
            player.lose_influence()

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
        if self.winner is not None:
            return

        start = self.current_player

        while True:
            self.current_player = (
                self.current_player + 1
            ) % len(self.players)

            if self.players[self.current_player].alive:
                break

            if self.current_player == start:
                break
