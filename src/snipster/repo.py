from abc import ABC, abstractmethod
from typing import Sequence
from .models import Snippet

#(add, list, get, delete)


class SnippetRepository(ABC):
    @abstractmethod
    def add(self, snippet : Snippet) -> None:
        pass

    @abstractmethod
    def list(self) -> Sequence[Snippet]:
        pass

    @abstractmethod
    def get(self, snippet_id : int) -> Snippet | None:
        pass

    @abstractmethod
    def delete(self, snippet_id : int) -> None:
        pass