from unittest.mock import patch

from src.cards import Card, Role
from src.game import Game
from src.player import Player
from tests.game_test_case import GameTestCase


class GameStateTests(GameTestCase):
    def test_game_over_rejects_further_actions(self):
        for card in self.players[1].cards + self.players[2].cards:
            card.revealed = True

        with self.assertRaisesRegex(ValueError, "already over"):
            self.game.perform_action("p1", "income", self.no_challenges)

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

        self.assertEqual(state["players"][0]["cards"], ["duke", "captain"])
        self.assertEqual(state["players"][1]["cards"], ["hidden", "hidden"])

    def test_action_log_records_events_in_order_and_is_in_state(self):
        state = self.game.perform_action(
            "p1", "income", decision_provider=self.no_challenges
        )

        self.assertEqual(
            self.game.log,
            [
                "Player 1 takes Income.",
                "Player 1 gains 1 coin (now 3).",
                "It is now Player 2's turn.",
            ],
        )
        self.assertEqual(state["log"], self.game.log)

    def test_log_records_block_challenge_and_resolution(self):
        self.players[2].cards = [Card(Role.ASSASSIN), Card(Role.CAPTAIN)]

        def decisions(kind, context):
            if kind == "block":
                return {"blocker_id": "p3"}
            if kind == "challenge":
                return context["challenger_id"] == "p1"
            return self.no_challenges(kind, context)

        self.game.perform_action("p1", "foreign_aid", decision_provider=decisions)
        log_text = "\n".join(self.game.log)

        self.assertIn("claims duke to block foreign aid", log_text)
        self.assertIn("challenges Player 3's duke claim", log_text)
        self.assertIn("block is disproven; the action continues", log_text)
        self.assertIn("Player 1 gains 2 coins", log_text)

    def test_failed_action_rolls_back_its_log_entries(self):
        def invalid_challenge(kind, context):
            if kind == "challenge":
                return "no"
            return self.no_challenges(kind, context)

        with self.assertRaisesRegex(ValueError, "must be booleans"):
            self.game.perform_action("p1", "tax", decision_provider=invalid_challenge)

        self.assertEqual(self.game.log, [])

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