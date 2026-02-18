import unittest
from src.snake import Snake

class TestSnake(unittest.TestCase):
    def setUp(self):
        self.snake = Snake(initial_position=[(5, 5)], initial_direction='RIGHT', board_size=(10, 10))

    def test_initial_position(self):
        self.assertEqual(self.snake.body, [(5, 5)])

    def test_move_right(self):
        self.snake.move()
        self.assertEqual(self.snake.body[0], (6, 5))

    def test_move_up(self):
        self.snake.change_direction('UP')
        self.snake.move()
        self.assertEqual(self.snake.body[0], (5, 4))

    def test_grow(self):
        self.snake.grow()
        self.assertEqual(len(self.snake.body), 2)

    def test_self_collision(self):
        self.snake.body = [(5, 5), (5, 6), (5, 5)]
        self.assertTrue(self.snake.check_self_collision())

    def test_wall_collision(self):
        self.snake.body = [(10, 5)]
        self.assertTrue(self.snake.check_wall_collision())

if __name__ == '__main__':
    unittest.main()
