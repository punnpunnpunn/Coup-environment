from src.cards import Card, Role
from src.game import Game
from src.player import Player
from tests.game_test_case import GameTestCase


class GameActionTests(GameTestCase):
    def test_must_coup_at_ten_and_action_advances_turn(self):
        self.players[0].coins = 10

        with self.assertRaisesRegex(ValueError, "must coup"):
            self.game.perform_action(
                "p1", "income", decision_provider=self.no_challenges
            )

        state = self.game.perform_action(
            "p1", "coup", "p2", decision_provider=self.no_challenges
        )
        self.assertEqual(self.players[0].coins, 3)
        self.assertEqual(self.game.current.id, "p2")
        self.assertEqual(state["current_player"], "p2")

    def test_must_coup_rule_applies_above_ten_too(self):
        self.players[0].coins = 12

        with self.assertRaisesRegex(ValueError, "must coup"):
            self.game.perform_action(
                "p1", "foreign_aid", decision_provider=self.no_challenges
            )
        self.assertEqual(self.players[0].coins, 12)

    def test_income_can_reach_ten_and_forces_coup_next_turn(self):
        self.players[0].coins = 9
        self.game.perform_action("p1", "income", decision_provider=self.no_challenges)
        self.assertEqual(self.players[0].coins, 10)
        self.players[1].coins = 10
        with self.assertRaisesRegex(ValueError, "must coup"):
            self.game.perform_action(
                "p2", "income", decision_provider=self.no_challenges
            )

    def test_invalid_player_action_and_missing_target_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown action"):
            self.game.perform_action("p1", "pass", decision_provider=self.no_challenges)
        with self.assertRaisesRegex(ValueError, "not this player's turn"):
            self.game.perform_action("p2", "income", decision_provider=self.no_challenges)
        with self.assertRaisesRegex(ValueError, "requires a target"):
            self.game.perform_action("p1", "coup", decision_provider=self.no_challenges)
        self.assertEqual(self.game.current.id, "p1")
        self.assertEqual(self.players[0].coins, 2)

    def test_eliminated_target_cannot_be_targeted(self):
        self.players[1].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
        for card in self.players[1].cards:
            card.revealed = True

        for action, coins in (("coup", 7), ("assassinate", 3), ("steal", 2)):
            with self.subTest(action=action):
                self.players[0].coins = coins
                with self.assertRaisesRegex(ValueError, "Target is eliminated"):
                    self.game.perform_action("p1", action, "p2", self.no_challenges)
        self.assertEqual(self.game.current.id, "p1")

    def test_setup_deals_two_cards_and_two_coins(self):
        self.assertEqual([player.coins for player in self.players], [2, 2, 2])
        self.assertEqual([player.influence for player in self.players], [2, 2, 2])
        self.assertEqual(len(self.game.deck), 9)
        role_counts = {role: 0 for role in Role}
        for card in self.game.deck + [
            card for player in self.players for card in player.cards
        ]:
            role_counts[card.role] += 1
        self.assertEqual(set(role_counts.values()), {3})

    def test_setup_requires_room_for_an_exchange(self):
        six_players = [Player(f"p{i}", f"Player {i}") for i in range(6)]
        game = Game(six_players)
        self.assertEqual(len(game.deck), 3)

        seven_players = [Player(f"p{i}", f"Player {i}") for i in range(7)]
        with self.assertRaisesRegex(ValueError, "2-6 players"):
            Game(seven_players)

    def test_setup_rejects_too_few_players_and_duplicate_ids(self):
        with self.assertRaisesRegex(ValueError, "2-6 players"):
            Game([Player("only", "Only player")])
        with self.assertRaisesRegex(ValueError, "IDs must be unique"):
            Game([Player("same", "First"), Player("same", "Second")])

    def test_income_and_unblocked_foreign_aid(self):
        self.game.perform_action("p1", "income", decision_provider=self.no_challenges)
        self.assertEqual(self.players[0].coins, 3)
        self.game.perform_action(
            "p2", "foreign_aid", decision_provider=self.no_challenges
        )
        self.assertEqual(self.players[1].coins, 4)

    def test_coup_costs_seven_and_skips_eliminated_target(self):
        self.players[0].coins = 7
        self.players[1].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]

        state = self.game.perform_action(
            "p1", "coup", "p2", decision_provider=self.no_challenges
        )

        self.assertEqual(self.players[0].coins, 0)
        self.assertEqual(self.players[1].influence, 1)
        self.assertEqual(state["current_player"], "p2")

    def test_targeted_action_rejects_invalid_targets_without_effect(self):
        for action, coins, target in (
            ("coup", 7, "p1"),
            ("assassinate", 3, "p1"),
            ("steal", 2, "missing"),
        ):
            with self.subTest(action=action, target=target):
                self.players[0].coins = coins
                with self.assertRaises(ValueError):
                    self.game.perform_action("p1", action, target, self.no_challenges)
                self.assertEqual(self.players[0].coins, coins)
                self.assertEqual(self.game.current.id, "p1")

    def test_coup_and_assassination_costs_are_validated(self):
        with self.assertRaisesRegex(ValueError, "Coup costs"):
            self.game.perform_action("p1", "coup", "p2", self.no_challenges)
        with self.assertRaisesRegex(ValueError, "Assassination costs"):
            self.game.perform_action("p1", "assassinate", "p2", self.no_challenges)
        self.assertEqual(self.players[0].coins, 2)
        self.assertEqual(self.game.current.id, "p1")

    def test_assassination_cost_and_influence(self):
        self.players[0].coins = 3
        self.players[1].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]

        self.game.perform_action("p1", "assassin", "p2", self.no_challenges)

        self.assertEqual(self.players[0].coins, 0)
        self.assertEqual(self.players[1].influence, 1)

    def test_steal_takes_at_most_two_coins(self):
        self.players[1].coins = 1
        self.game.perform_action("p1", "steal", "p2", self.no_challenges)
        self.assertEqual(self.players[0].coins, 3)
        self.assertEqual(self.players[1].coins, 0)

        self.game.perform_action("p2", "income", decision_provider=self.no_challenges)
        self.players[0].coins = 0
        self.players[2].coins = 0
        self.game.perform_action("p3", "steal", "p1", self.no_challenges)
        self.assertEqual(self.players[2].coins, 0)

    def test_exchange_requires_two_court_cards_and_rolls_back(self):
        self.game.deck = [self.game.deck.pop()]
        deck_before = list(self.game.deck)

        with self.assertRaisesRegex(ValueError, "Not enough cards"):
            self.game.perform_action(
                "p1", "exchange", decision_provider=self.no_challenges
            )

        self.assertEqual(self.game.deck, deck_before)
        self.assertEqual(self.game.current.id, "p1")

    def test_invalid_exchange_choice_preserves_cards_deck_and_turn(self):
        original_cards = list(self.players[0].cards)
        original_deck = list(self.game.deck)

        def invalid_exchange(kind, context):
            if kind == "exchange":
                return [0, 0]
            return self.no_challenges(kind, context)

        with self.assertRaisesRegex(ValueError, "distinct valid"):
            self.game.perform_action(
                "p1", "exchange", decision_provider=invalid_exchange
            )

        self.assertEqual(self.players[0].cards, original_cards)
        self.assertEqual(self.game.deck, original_deck)
        self.assertEqual(self.game.current.id, "p1")

    def test_invalid_influence_choice_does_not_charge_coup(self):
        self.players[0].coins = 7
        original_cards = list(self.players[1].cards)

        def invalid_reveal(kind, context):
            if kind == "reveal_influence":
                return []
            return self.no_challenges(kind, context)

        with self.assertRaises(ValueError):
            self.game.perform_action("p1", "coup", "p2", invalid_reveal)

        self.assertEqual(self.players[0].coins, 7)
        self.assertEqual(self.players[1].cards, original_cards)
        self.assertEqual(self.game.current.id, "p1")

    def test_exchange_preserves_but_cannot_choose_revealed_card(self):
        revealed = Card(Role.DUKE)
        revealed.revealed = True
        active = Card(Role.CAPTAIN)
        self.players[0].cards = [revealed, active]
        self.game.deck = [Card(Role.ASSASSIN), Card(Role.AMBASSADOR)]
        seen_candidates = []

        def decisions(kind, context):
            if kind == "exchange":
                seen_candidates.extend(card["role"] for card in context["cards"])
                return [0]
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "exchange", decision_provider=decisions)

        self.assertEqual(
            set(seen_candidates), {"captain", "assassin", "ambassador"}
        )
        self.assertIn(revealed, self.players[0].cards)
        self.assertTrue(revealed.revealed)
        self.assertEqual(self.players[0].influence, 1)