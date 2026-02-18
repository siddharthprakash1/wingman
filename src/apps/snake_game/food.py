import random

class Food:
    def __init__(self, board_width, board_height, snake_body):
        self.board_width = board_width
        self.board_height = board_height
        self.snake_body = snake_body
        self.position = self.generate_food_position()

    def generate_food_position(self):
        while True:
            x = random.randint(0, self.board_width - 1)
            y = random.randint(0, self.board_height - 1)
            if (x, y) not in self.snake_body:
                return (x, y)

    def place_new_food(self, snake_body):
        self.snake_body = snake_body
        self.position = self.generate_food_position()
