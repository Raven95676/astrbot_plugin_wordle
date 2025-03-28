from abc import ABC, abstractmethod


class WordleBase(ABC):
    @abstractmethod
    async def gen_image(self) -> bytes:
        pass

    @abstractmethod
    async def guess(self, word: str) -> bytes:
        pass

    @property
    @abstractmethod
    def answer(self) -> str:
        pass

    @property
    @abstractmethod
    def valid_words(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def length(self) -> int:
        pass

    @property
    @abstractmethod
    def max_attempts(self) -> int:
        pass

    @property
    @abstractmethod
    def guesses(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def is_game_over(self):
        pass

    @property
    @abstractmethod
    def is_won(self):
        pass
