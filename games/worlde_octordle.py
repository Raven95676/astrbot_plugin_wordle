from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from .common import WordleBase  # type: ignore

GRID_SIZE = 8
WORD_LENGTH = 5
MAX_GUESSES = 13
CELL_SIZE = 50
PADDING = 10
FONT_SIZE = 30
GRID_WIDTH = CELL_SIZE * WORD_LENGTH + PADDING * (WORD_LENGTH + 1)
GRID_HEIGHT = CELL_SIZE * MAX_GUESSES + PADDING * (MAX_GUESSES + 1)
WINDOW_WIDTH = GRID_WIDTH * 4 + PADDING * 5
WINDOW_HEIGHT = GRID_HEIGHT * 2 + PADDING * 4 + 250

CELL_COLORS = {
    2: (106, 170, 100),
    1: (201, 180, 88),
    0: (120, 124, 126),
    -1: (211, 214, 218),
}
BACKGROUND_COLOR = (255, 255, 255)
KEYBOARD_COLORS = {
    2: CELL_COLORS[2],
    1: CELL_COLORS[1],
    0: (211, 214, 218),
}


class WordleOctordle(WordleBase):
    def __init__(self, answers: list[str], valid_words: list[str]):
        self._answers = [answer.upper() for answer in answers]
        self._valid_words = valid_words
        self._length = len(answers[0])
        self._max_attempts = MAX_GUESSES
        self._guesses: list[str] = []
        self._feedbacks: list[list[list[int]]] = []
        self._keyboard_status = {chr(i + ord("A")): [-1] * GRID_SIZE for i in range(26)}
        self._font = ImageFont.truetype("arial.ttf", FONT_SIZE)

    async def gen_image(self) -> bytes:
        img = Image.new("RGB", (WINDOW_WIDTH, WINDOW_HEIGHT), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)

        total_grid_width = GRID_WIDTH * 4 + PADDING * 3
        total_grid_height = GRID_HEIGHT * 2 + PADDING
        grid_start_x = (WINDOW_WIDTH - total_grid_width) // 2
        grid_start_y = (WINDOW_HEIGHT - total_grid_height - 100) // 2

        solved_grids = {}
        for grid_idx in range(GRID_SIZE):
            for guess_idx, _ in enumerate(self._guesses):
                if all(
                    self._feedbacks[guess_idx][grid_idx][i] == 2
                    for i in range(WORD_LENGTH)
                ):
                    solved_grids[grid_idx] = guess_idx
                    break

        for grid_idx in range(GRID_SIZE):
            grid_x = grid_start_x + (grid_idx % 4) * (GRID_WIDTH + PADDING)
            grid_y = grid_start_y + (grid_idx // 4) * (GRID_HEIGHT + PADDING)
            draw.rectangle(
                [grid_x, grid_y, grid_x + GRID_WIDTH, grid_y + GRID_HEIGHT],
                fill=BACKGROUND_COLOR,
                outline=(0, 0, 0),
                width=2,
            )
            for row in range(MAX_GUESSES):
                for col in range(WORD_LENGTH):
                    x = grid_x + PADDING + col * (CELL_SIZE + PADDING)
                    y = grid_y + PADDING + row * (CELL_SIZE + PADDING)
                    color = CELL_COLORS[-1]

                    if row < len(self._guesses) and (
                        grid_idx not in solved_grids or row <= solved_grids[grid_idx]
                    ):
                        guess = self._guesses[row]
                        feedback_value = self._feedbacks[row][grid_idx][col]
                        color = CELL_COLORS[feedback_value]
                        draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], fill=color)
                        draw.text(
                            (x + CELL_SIZE // 3, y + CELL_SIZE // 6),
                            guess[col],
                            fill=(255, 255, 255),
                            font=self._font,
                        )
                    else:
                        draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], fill=color)

        keyboard_rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        keyboard_y = grid_start_y + total_grid_height + PADDING * 2
        for row_idx, keyboard_row in enumerate(keyboard_rows):
            row_width = len(keyboard_row) * (CELL_SIZE + PADDING // 2)
            start_x = (WINDOW_WIDTH - row_width) // 2
            for col_idx, letter in enumerate(keyboard_row):
                x = start_x + col_idx * (CELL_SIZE + PADDING // 2)
                y = keyboard_y + row_idx * (CELL_SIZE + PADDING // 2)

                draw.rectangle(
                    [x, y, x + CELL_SIZE, y + CELL_SIZE], fill=KEYBOARD_COLORS[0]
                )

                cell_width = CELL_SIZE // 2
                cell_height = CELL_SIZE // 2
                for grid_idx in range(GRID_SIZE):
                    grid_x = x + (grid_idx % 4) * (cell_width // 2)
                    grid_y = y + (grid_idx // 4) * cell_height
                    status = self._keyboard_status[letter][grid_idx]
                    if status > 0:
                        draw.rectangle(
                            [
                                grid_x,
                                grid_y,
                                grid_x + cell_width // 2,
                                grid_y + cell_height,
                            ],
                            fill=KEYBOARD_COLORS[status],
                        )

                draw.text(
                    (x + CELL_SIZE // 3, y + CELL_SIZE // 6),
                    letter,
                    fill=(0, 0, 0),
                    font=self._font,
                )

        with BytesIO() as output:
            img.save(output, format="PNG")
            return output.getvalue()

    async def guess(self, word: str) -> bytes:
        word = word.upper()
        self._guesses.append(word)

        grid_feedbacks = []
        for answer in self._answers:
            feedback = [0] * self._length
            answer_char_counts: dict[str, int] = {}

            for i in range(self._length):
                if word[i] == answer[i]:
                    feedback[i] = 2
                else:
                    answer_char_counts[answer[i]] = (
                        answer_char_counts.get(answer[i], 0) + 1
                    )

            for i in range(self._length):
                if feedback[i] != 2:
                    char = word[i]
                    if char in answer_char_counts and answer_char_counts[char] > 0:
                        feedback[i] = 1
                        answer_char_counts[char] -= 1

            grid_feedbacks.append(feedback)
        self._feedbacks.append(grid_feedbacks)

        for letter in word:
            for grid_idx, _ in enumerate(self._answers):
                for i, char in enumerate(word):
                    if char == letter:
                        feedback_value = self._feedbacks[-1][grid_idx][i]
                        current_status = self._keyboard_status[letter][grid_idx]
                        if feedback_value > current_status:
                            self._keyboard_status[letter][grid_idx] = feedback_value

        result = await self.gen_image()
        return result

    @property
    def answer(self) -> str:
        return "/".join(self._answers)

    @property
    def valid_words(self) -> list[str]:
        return self._valid_words

    @property
    def length(self) -> int:
        return self._length

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    @property
    def guesses(self) -> list[str]:
        return self._guesses

    @property
    def is_game_over(self):
        if not self._guesses:
            return False
        return len(self._guesses) >= self._max_attempts or self.is_won

    @property
    def is_won(self):
        if not self._guesses:
            return False
        for grid_idx, _ in enumerate(self._answers):
            found = False
            for guess_idx, _ in enumerate(self._guesses):
                if all(
                    self._feedbacks[guess_idx][grid_idx][i] == 2
                    for i in range(self._length)
                ):
                    found = True
                    break
            if not found:
                return False
        return True
