from game import Game

game = Game()

while not game.is_over:
    current_player = game.players[game.current_player]
    print(current_player)
    action = input(f"Player {game.current_player + 1}, choose your action: ")
    current_player.choose_action(action)
    game.current_player = (game.current_player + 1) % len(game.players)