from unittest.mock import patch

from src.cards import Card, Role
from tests.game_test_case import GameTestCase


class GameChallengeTests(GameTestCase):
    def test_honest_duke_challenged_proves_claim_then_tax_resolves(self):
        self.players[0].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
        self.players[1].cards[1].revealed = True

        def decisions(kind, context):
            if kind == "challenge":
                return context["challenger_id"] == "p2"
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "duke", decision_provider=decisions)

        self.assertEqual(self.players[0].coins, 5)
        self.assertEqual(self.players[0].influence, 2)
        self.assertEqual(self.players[1].influence, 0)
        self.assertEqual(len(self.game.deck), 9)

    def test_challenge_window_stops_at_first_challenger(self):
        queried = []

        def decisions(kind, context):
            if kind == "challenge":
                queried.append(context["challenger_id"])
                return context["challenger_id"] == "p3"
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "tax", decision_provider=decisions)
        self.assertEqual(queried, ["p2", "p3"])

    def test_false_duke_block_unchallenged_still_blocks(self):
        self.players[2].cards = [Card(Role.ASSASSIN), Card(Role.CAPTAIN)]

        def decisions(kind, context):
            if kind == "block":
                return {"blocker_id": "p3"}
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "foreign_aid", decision_provider=decisions)

        self.assertEqual(self.players[0].coins, 2)
        self.assertEqual(self.players[2].influence, 2)

    def test_false_contessa_block_unchallenged_still_blocks(self):
        self.players[0].coins = 3
        self.players[1].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]

        def decisions(kind, context):
            if kind == "block":
                return {"blocker_id": "p2", "role": "contessa"}
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "assassinate", "p2", decisions)

        self.assertEqual(self.players[0].coins, 0)
        self.assertEqual(self.players[1].influence, 2)

    def test_honest_duke_blocks_foreign_aid(self):
        self.players[2].cards = [Card(Role.DUKE), Card(Role.ASSASSIN)]

        def decisions(kind, context):
            if kind == "block":
                return {"blocker_id": "p3"}
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "foreign_aid", decision_provider=decisions)

        self.assertEqual(self.players[0].coins, 2)
        self.assertEqual(self.players[2].influence, 2)

    def test_invalid_challenge_response_rolls_back(self):
        coins_before = self.players[0].coins

        def invalid_challenge(kind, context):
            if kind == "challenge":
                return "no"
            return self.no_challenges(kind, context)

        with self.assertRaisesRegex(ValueError, "must be booleans"):
            self.game.perform_action("p1", "tax", decision_provider=invalid_challenge)

        self.assertEqual(self.players[0].coins, coins_before)
        self.assertEqual(self.game.current.id, "p1")

    def test_false_duke_block_is_challenged_and_aid_resolves(self):
        self.players[2].cards = [Card(Role.ASSASSIN), Card(Role.CAPTAIN)]

        def decisions(kind, context):
            if kind == "block":
                return {"blocker_id": "p3"}
            if kind == "challenge":
                return (
                    context["claimant_id"] == "p3"
                    and context["challenger_id"] == "p1"
                )
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "foreign aid", decision_provider=decisions)

        self.assertEqual(self.players[0].coins, 4)
        self.assertEqual(self.players[2].influence, 1)

    def test_bluffing_duke_challenged_cancels_tax(self):
        self.players[0].cards = [Card(Role.ASSASSIN), Card(Role.CAPTAIN)]

        def decisions(kind, context):
            if kind == "challenge":
                return context["challenger_id"] == "p2"
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "tax", decision_provider=decisions)

        self.assertEqual(self.players[0].coins, 2)
        self.assertEqual(self.players[0].influence, 1)
        self.assertEqual(self.game.current.id, "p2")

    def test_false_assassin_claim_challenged_refunds_fee(self):
        self.players[0].coins = 3
        self.players[0].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]

        def decisions(kind, context):
            if kind == "challenge":
                return context["challenger_id"] == "p2"
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "assassinate", "p2", decisions)

        self.assertEqual(self.players[0].coins, 3)
        self.assertEqual(self.players[0].influence, 1)
        self.assertEqual(self.players[1].influence, 2)

    def test_honest_contessa_block_spends_assassination_fee(self):
        self.players[0].coins = 3
        self.players[1].cards = [Card(Role.CONTESSA), Card(Role.DUKE)]

        def decisions(kind, context):
            if kind == "block":
                return {"blocker_id": "p2", "role": "contessa"}
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "assassinate", "p2", decisions)

        self.assertEqual(self.players[0].coins, 0)
        self.assertEqual(self.players[1].influence, 2)

    def test_challenged_false_contessa_block_allows_assassination(self):
        self.players[0].coins = 3
        self.players[1].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]

        def decisions(kind, context):
            if kind == "block":
                return {"blocker_id": "p2", "role": "contessa"}
            if kind == "challenge":
                return (
                    context["claimant_id"] == "p2"
                    and context["challenger_id"] == "p1"
                )
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "assassinate", "p2", decisions)

        self.assertEqual(self.players[0].coins, 0)
        self.assertEqual(self.players[1].influence, 0)

    def test_honest_captain_block_prevents_steal(self):
        self.players[1].cards = [Card(Role.CAPTAIN), Card(Role.DUKE)]

        def decisions(kind, context):
            if kind == "block":
                return {"blocker_id": "p2", "role": "captain"}
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "steal", "p2", decisions)

        self.assertEqual(self.players[0].coins, 2)
        self.assertEqual(self.players[1].coins, 2)

    def test_honest_ambassador_block_prevents_steal(self):
        self.players[1].cards = [Card(Role.AMBASSADOR), Card(Role.DUKE)]

        def decisions(kind, context):
            if kind == "block":
                return {"blocker_id": "p2", "role": "ambassador"}
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "steal", "p2", decisions)

        self.assertEqual(self.players[0].coins, 2)
        self.assertEqual(self.players[1].coins, 2)

    def test_challenged_bluffing_captain_claim_prevents_steal(self):
        self.players[0].cards = [Card(Role.DUKE), Card(Role.ASSASSIN)]

        def decisions(kind, context):
            if kind == "challenge":
                return context["claimant_id"] == "p1"
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "steal", "p2", decisions)

        self.assertEqual(self.players[0].coins, 2)
        self.assertEqual(self.players[0].influence, 1)
        self.assertEqual(self.players[1].coins, 2)

    def test_steal_does_not_take_coins_from_blocker_eliminated_by_challenge(self):
        self.players[1].coins = 5
        self.players[1].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
        self.players[1].cards[0].revealed = True

        def decisions(kind, context):
            if kind == "block":
                return {"blocker_id": "p2", "role": "ambassador"}
            if kind == "challenge":
                return (
                    context["claimant_id"] == "p2"
                    and context["challenger_id"] == "p1"
                )
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "steal", "p2", decisions)

        self.assertFalse(self.players[1].alive)
        self.assertEqual(self.players[0].coins, 2)
        self.assertEqual(self.players[1].coins, 5)
        self.assertEqual(self.game.current.id, "p3")

    def test_challenged_false_steal_block_allows_steal_if_target_survives(self):
        self.players[1].coins = 5
        self.players[1].cards = [Card(Role.DUKE), Card(Role.CONTESSA)]

        def decisions(kind, context):
            if kind == "block":
                return {"blocker_id": "p2", "role": "ambassador"}
            if kind == "challenge":
                return (
                    context["claimant_id"] == "p2"
                    and context["challenger_id"] == "p1"
                )
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "steal", "p2", decisions)

        self.assertEqual(self.players[1].influence, 1)
        self.assertEqual(self.players[0].coins, 4)
        self.assertEqual(self.players[1].coins, 3)

    def test_assassin_does_not_offer_block_to_target_eliminated_by_challenge(self):
        self.players[0].coins = 3
        self.players[0].cards = [Card(Role.ASSASSIN), Card(Role.DUKE)]
        self.players[1].cards = [Card(Role.CONTESSA), Card(Role.CAPTAIN)]
        self.players[1].cards[0].revealed = True
        for card in self.players[2].cards:
            card.revealed = True

        def decisions(kind, context):
            if kind == "challenge":
                return context["challenger_id"] == "p2"
            if kind == "block":
                raise AssertionError("eliminated target was asked to block")
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "assassinate", "p2", decisions)

        self.assertFalse(self.players[1].alive)
        self.assertEqual(self.players[0].coins, 0)
        self.assertIs(self.game.winner, self.players[0])

    def test_steal_does_not_offer_block_to_target_eliminated_by_challenge(self):
        self.players[0].cards = [Card(Role.CAPTAIN), Card(Role.DUKE)]
        self.players[1].cards = [Card(Role.AMBASSADOR), Card(Role.CONTESSA)]
        self.players[1].cards[0].revealed = True
        self.players[1].coins = 5
        for card in self.players[2].cards:
            card.revealed = True

        def decisions(kind, context):
            if kind == "challenge":
                return context["challenger_id"] == "p2"
            if kind == "block":
                raise AssertionError("eliminated target was asked to block")
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "steal", "p2", decisions)

        self.assertFalse(self.players[1].alive)
        self.assertEqual(self.players[0].coins, 2)
        self.assertEqual(self.players[1].coins, 5)
        self.assertIs(self.game.winner, self.players[0])

    def test_challenge_returns_card_before_drawing_replacement(self):
        proven_card = Card(Role.DUKE)
        self.players[0].cards = [proven_card, Card(Role.CONTESSA)]
        self.players[1].cards = [Card(Role.ASSASSIN), Card(Role.CAPTAIN)]
        self.players[1].cards[1].revealed = True
        self.game.deck = [Card(Role.AMBASSADOR)]

        def decisions(kind, context):
            if kind == "challenge":
                return context["challenger_id"] == "p2"
            return self.no_challenges(kind, context)

        with patch("src.game.random.shuffle", side_effect=lambda _deck: None):
            self.game.perform_action("p1", "tax", decision_provider=decisions)

        self.assertIn(proven_card, self.players[0].cards)
        self.assertFalse(proven_card.revealed)
        self.assertEqual(self.players[1].influence, 0)
        self.assertEqual(self.players[0].coins, 5)

    def test_failed_challenge_decision_rolls_back_card_exchange(self):
        proven_card = Card(Role.DUKE)
        self.players[0].cards = [proven_card, Card(Role.CONTESSA)]
        deck_before = list(self.game.deck)
        player_cards_before = [list(player.cards) for player in self.players]

        def invalid_decisions(kind, context):
            if kind == "challenge":
                return context["challenger_id"] == "p2"
            if kind == "reveal_influence":
                return []
            return self.no_challenges(kind, context)

        with self.assertRaises(ValueError):
            self.game.perform_action("p1", "tax", decision_provider=invalid_decisions)

        self.assertEqual(self.game.deck, deck_before)
        self.assertEqual(
            [player.cards for player in self.players], player_cards_before
        )
        self.assertFalse(proven_card.revealed)
        self.assertEqual(self.players[0].coins, 2)
        self.assertEqual(self.game.current.id, "p1")

    def test_invalid_block_response_does_not_change_state(self):
        deck_before = list(self.game.deck)

        def invalid_block(kind, context):
            if kind == "block":
                return {"blocker_id": "p3", "role": "contessa"}
            return self.no_challenges(kind, context)

        with self.assertRaisesRegex(ValueError, "cannot block this action"):
            self.game.perform_action(
                "p1", "steal", "p2", decision_provider=invalid_block
            )

        self.assertEqual([player.coins for player in self.players], [2, 2, 2])
        self.assertEqual(self.game.deck, deck_before)
        self.assertEqual(self.game.current.id, "p1")