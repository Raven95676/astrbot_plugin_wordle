from io import BytesIO

from PIL import Image as ImageW
from PIL import ImageDraw, ImageFont
from .common import WordleBase  # type: ignore


class WordleClassic(WordleBase):
    def __init__(self, answer: str, valid_words: list[str]):
        self._answer = answer.upper()
        self._valid_words = valid_words
        self._length = len(answer)
        self._max_attempts = self._length + 1
        self._guesses: list[str] = []
        self._feedbacks: list[list[int]] = []
        self._font = ImageFont.load_default()

    async def gen_image(self) -> bytes:
        CELL_COLORS = {
            2: (106, 170, 100),
            1: (201, 180, 88),
            0: (120, 124, 126),
            -1: (211, 214, 218),
        }
        BACKGROUND_COLOR = (255, 255, 255)
        TEXT_COLOR = (255, 255, 255)

        CELL_SIZE = 60
        CELL_MARGIN = 5
        GRID_MARGIN = 5

        cell_stride = CELL_SIZE + CELL_MARGIN
        width = GRID_MARGIN * 2 + cell_stride * self._length - CELL_MARGIN
        height = GRID_MARGIN * 2 + cell_stride * self._max_attempts - CELL_MARGIN

        image = ImageW.new("RGB", (width, height), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(image)

        for row in range(self._max_attempts):
            y = GRID_MARGIN + row * cell_stride

            for col in range(self._length):
                x = GRID_MARGIN + col * cell_stride

                if row < len(self._guesses) and col < len(self._guesses[row]):
                    letter = self._guesses[row][col].upper()
                    feedback_value = self._feedbacks[row][col]
                    cell_color = CELL_COLORS[feedback_value]
                else:
                    letter = ""
                    cell_color = CELL_COLORS[-1]

                draw.rectangle(
                    [x, y, x + CELL_SIZE, y + CELL_SIZE], fill=cell_color, outline=None
                )

                if letter:
                    text_bbox = draw.textbbox((0, 0), letter, font=self._font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]

                    letter_x = x + (CELL_SIZE - text_width) // 2
                    letter_y = y + (CELL_SIZE - text_height) // 2

                    draw.text(
                        (letter_x, letter_y), letter, fill=TEXT_COLOR, font=self._font
                    )

        with BytesIO() as output:
            image.save(output, format="PNG")
            return output.getvalue()

    async def guess(self, word: str) -> bytes:
        word = word.upper()
        self._guesses.append(word)

        feedback = [0] * self._length
        answer_char_counts: dict[str, int] = {}

        for i in range(self._length):
            if word[i] == self._answer[i]:
                feedback[i] = 2
            else:
                answer_char_counts[self._answer[i]] = (
                    answer_char_counts.get(self._answer[i], 0) + 1
                )

        for i in range(self._length):
            if feedback[i] != 2:
                char = word[i]
                if char in answer_char_counts and answer_char_counts[char] > 0:
                    feedback[i] = 1
                    answer_char_counts[char] -= 1

        self._feedbacks.append(feedback)
        result = await self.gen_image()

        return result

    @property
    def answer(self) -> str:
        return self._answer

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
        return self._guesses and self._guesses[-1].upper() == self._answer
