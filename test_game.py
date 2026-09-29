import unittest
from unittest.mock import patch

from cards import Card, Role
from game import Game
from player import Player


class GameRulesTests(unittest.TestCase):
    def setUp(self):
        self.players = [
            Player("p1", "Player 1"),
            Player("p2", "Player 2"),
            Player("p3", "Player 3"),
        ]
        self.game = Game(self.players)

    @staticmethod
    def no_challenges(kind, context):
        if kind == "challenge":
            return False
        if kind == "block":
            return None
        if kind == "reveal_influence":
            return context["cards"][0]["index"]
        if kind == "exchange":
            return list(range(context["keep_count"]))
        raise AssertionError(f"Unexpected decision: {kind}")

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
                    self.game.perform_action(
                        "p1", action, "p2", self.no_challenges
                    )
        self.assertEqual(self.game.current.id, "p1")

    def test_game_over_rejects_further_actions(self):
        for card in self.players[1].cards + self.players[2].cards:
            card.revealed = True

        with self.assertRaisesRegex(ValueError, "already over"):
            self.game.perform_action("p1", "income", self.no_challenges)

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

    def test_exchange_requires_two_court_cards_and_rolls_back(self):
        self.game.deck = [self.game.deck.pop()]
        deck_before = list(self.game.deck)

        with self.assertRaisesRegex(ValueError, "Not enough cards"):
            self.game.perform_action(
                "p1", "exchange", decision_provider=self.no_challenges
            )

        self.assertEqual(self.game.deck, deck_before)
        self.assertEqual(self.game.current.id, "p1")

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

    def test_agent_tax_uses_claim_window_and_advances(self):
        queried = []

        def decisions(kind, context):
            if kind == "challenge":
                queried.append(context["challenger_id"])
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "tax", decision_provider=decisions)

        self.assertEqual(self.players[0].coins, 5)
        self.assertEqual(queried, ["p2", "p3"])
        self.assertEqual(self.game.current.id, "p2")

    def test_action_result_includes_actor_private_cards(self):
        self.players[0].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]

        state = self.game.perform_action(
            "p1", "income", decision_provider=self.no_challenges
        )

        self.assertEqual(
            state["players"][0]["cards"], ["duke", "captain"]
        )
        self.assertEqual(state["players"][1]["cards"], ["hidden", "hidden"])

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

    def test_console_player_completes_a_turn_through_game_api(self):
        with patch("builtins.input", return_value="1"):
            self.players[0].choose_action(self.game)

        self.assertEqual(self.players[0].coins, 3)
        self.assertEqual(self.game.current.id, "p2")

    def test_game_over_state_names_winner_and_current_player(self):
        players = [Player("p1", "Player 1"), Player("p2", "Player 2")]
        game = Game(players)
        players[0].cards = [Card(Role.ASSASSIN), Card(Role.CAPTAIN)]
        players[0].cards[0].revealed = True

        def decisions(kind, context):
            if kind == "challenge":
                return context["challenger_id"] == "p2"
            return self.no_challenges(kind, context)

        state = game.perform_action("p1", "tax", decision_provider=decisions)

        self.assertEqual(state["winner"], "p2")
        self.assertEqual(state["current_player"], "p2")
        self.assertIs(game.winner, players[1])

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

    def test_income_and_unblocked_foreign_aid(self):
        self.game.perform_action("p1", "income", decision_provider=self.no_challenges)
        self.assertEqual(self.players[0].coins, 3)
        self.game.perform_action(
            "p2", "foreign_aid", decision_provider=self.no_challenges
        )
        self.assertEqual(self.players[1].coins, 4)

    def test_honest_duke_blocks_foreign_aid(self):
        self.players[2].cards = [Card(Role.DUKE), Card(Role.ASSASSIN)]

        def decisions(kind, context):
            if kind == "block":
                return {"blocker_id": "p3"}
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "foreign_aid", decision_provider=decisions)

        self.assertEqual(self.players[0].coins, 2)
        self.assertEqual(self.players[2].influence, 2)

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

    def test_coup_costs_seven_and_skips_eliminated_target(self):
        self.players[0].coins = 7
        self.players[1].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]

        state = self.game.perform_action(
            "p1", "coup", "p2", decision_provider=self.no_challenges
        )

        self.assertEqual(self.players[0].coins, 0)
        self.assertEqual(self.players[1].influence, 1)
        self.assertEqual(self.game.current.id, "p2")
        self.assertEqual(state["current_player"], "p2")

    def test_coup_eliminating_last_opponent_ends_game(self):
        self.players[0].coins = 7
        self.players[1].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
        self.players[1].cards[0].revealed = True
        self.players[2].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]
        for card in self.players[2].cards:
            card.revealed = True

        self.game.perform_action(
            "p1", "coup", "p2", decision_provider=self.no_challenges
        )

        self.assertFalse(self.players[1].alive)
        self.assertEqual(self.game.current.id, "p1")
        self.assertIs(self.game.winner, self.players[0])

    def test_targeted_action_rejects_invalid_targets_without_effect(self):
        for action, coins, target in (
            ("coup", 7, "p1"),
            ("assassinate", 3, "p1"),
            ("steal", 2, "missing"),
        ):
            with self.subTest(action=action, target=target):
                self.players[0].coins = coins
                with self.assertRaises(ValueError):
                    self.game.perform_action(
                        "p1", action, target, self.no_challenges
                    )
                self.assertEqual(self.players[0].coins, coins)
                self.assertEqual(self.game.current.id, "p1")

    def test_coup_and_assassination_costs_are_validated(self):
        with self.assertRaisesRegex(ValueError, "Coup costs"):
            self.game.perform_action(
                "p1", "coup", "p2", self.no_challenges
            )
        with self.assertRaisesRegex(ValueError, "Assassination costs"):
            self.game.perform_action(
                "p1", "assassinate", "p2", self.no_challenges
            )
        self.assertEqual(self.players[0].coins, 2)
        self.assertEqual(self.game.current.id, "p1")

    def test_assassination_cost_and_influence(self):
        self.players[0].coins = 3
        self.players[1].cards = [Card(Role.DUKE), Card(Role.CAPTAIN)]

        self.game.perform_action(
            "p1", "assassin", "p2", self.no_challenges
        )

        self.assertEqual(self.players[0].coins, 0)
        self.assertEqual(self.players[1].influence, 1)

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

    def test_invalid_exchange_choice_preserves_cards_deck_and_turn(self):
        original_cards = list(self.players[0].cards)
        original_deck = list(self.game.deck)

        def invalid_exchange(kind, context):
            if kind == "exchange":
                return [0, 0]
            return self.no_challenges(kind, context)

        with self.assertRaisesRegex(ValueError, "distinct valid"):
            self.game.perform_action("p1", "exchange", decision_provider=invalid_exchange)

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

        with patch("game.random.shuffle", side_effect=lambda _deck: None):
            self.game.perform_action("p1", "tax", decision_provider=decisions)

        self.assertIn(proven_card, self.players[0].cards)
        self.assertFalse(proven_card.revealed)
        self.assertEqual(self.players[1].influence, 0)
        self.assertEqual(self.players[0].coins, 5)


if __name__ == "__main__":
    unittest.main()