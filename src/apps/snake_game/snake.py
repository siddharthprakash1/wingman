class Snake:
    def __init__(self, initial_position=[(0, 0)], initial_direction='RIGHT', board_size=(20, 15)):
        self.body = initial_position  # List of tuples representing the snake's body
        self.direction = initial_direction  # Current direction of the snake
        self.board_width, self.board_height = board_size

    def has_eaten_food(self, food_position):
        """Check if the snake's head is at the same position as the food."""
        return self.body[0] == food_position

    def move(self):
        """Move the snake in the current direction."""
        head_x, head_y = self.body[0]

        if self.direction == 'UP':
            new_head = (head_x, head_y - 1)
        elif self.direction == 'DOWN':
            new_head = (head_x, head_y + 1)
        elif self.direction == 'LEFT':
            new_head = (head_x - 1, head_y)
        elif self.direction == 'RIGHT':
            new_head = (head_x + 1, head_y)
        else:
            raise ValueError(f"Invalid direction: {self.direction}")

        # Insert new head and remove the tail
        self.body = [new_head] + self.body[:-1]

    def grow(self):
        """Increase the length of the snake by adding a new segment at the tail."""
        tail_x, tail_y = self.body[-1]
        if len(self.body) > 1:
            second_last_x, second_last_y = self.body[-2]
            # Determine the direction of growth based on the last two segments
            if tail_x == second_last_x:
                if tail_y > second_last_y:
                    new_tail = (tail_x, tail_y + 1)
                else:
                    new_tail = (tail_x, tail_y - 1)
            else:
                if tail_x > second_last_x:
                    new_tail = (tail_x + 1, tail_y)
                else:
                    new_tail = (tail_x - 1, tail_y)
        else:
            # If the snake has only one segment, grow in the opposite direction of movement
            if self.direction == 'UP':
                new_tail = (tail_x, tail_y + 1)
            elif self.direction == 'DOWN':
                new_tail = (tail_x, tail_y - 1)
            elif self.direction == 'LEFT':
                new_tail = (tail_x + 1, tail_y)
            elif self.direction == 'RIGHT':
                new_tail = (tail_x - 1, tail_y)

        self.body.append(new_tail)

    def change_direction(self, new_direction):
        """Change the direction of the snake, ensuring it doesn't reverse."""
        opposite_directions = {('UP', 'DOWN'), ('DOWN', 'UP'), ('LEFT', 'RIGHT'), ('RIGHT', 'LEFT')}
        if (self.direction, new_direction) not in opposite_directions:
            self.direction = new_direction
        else:
            raise ValueError(f"Cannot reverse direction from {self.direction} to {new_direction}")

    def check_self_collision(self):
        """Check if the snake has collided with itself."""
        head = self.body[0]
        return head in self.body[1:]

    def check_wall_collision(self):
        """Check if the snake has collided with the wall."""
        head_x, head_y = self.body[0]
        return not (0 <= head_x < self.board_width and 0 <= head_y < self.board_height)
