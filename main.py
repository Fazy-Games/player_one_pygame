from game import Game


def clamp_integer(value, lower_bound, upper_bound):
    return lower_bound if value < lower_bound else upper_bound if value > upper_bound else value


def main():
    the_game = Game()
    the_game.game_loop()


if __name__ == '__main__':
    main()
