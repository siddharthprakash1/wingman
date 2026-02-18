import unittest
from src.food import Food

class TestFood(unittest.TestCase):
    def setUp(self):
        self.food = Food(board_width=10, board_height=10, snake_body=[(5, 5), (5, 6)])

    def test_generate_food_position(self):
        x, y = self.food.position
        self.assertTrue(0 <= x < 10)
        self.assertTrue(0 <= y < 10)
        self.assertNotIn((x, y), self.food.snake_body)

    def test_place_new_food(self):
        old_position = self.food.position
        self.food.place_new_food([(1, 1), (2, 2)])
        new_position = self.food.position
        self.assertNotEqual(old_position, new_position)
        self.assertNotIn(new_position, [(1, 1), (2, 2)])

if __name__ == '__main__':
    unittest.main()
