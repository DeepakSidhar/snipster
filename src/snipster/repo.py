from abc import ABC, abstractmethod
from typing import Sequence
from .models import Snippet
from .exceptions import SnippetNotFoundError
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

class InMemorySnippetRepo(SnippetRepository):
#Constructr
    def __init__(self) -> None:
        self._data: dict[int, Snippet] = {} # empty dict


    def add(self, snippet: Snippet) -> None:
        next_id = max(self._data.keys(), default=0) + 1
        snippet.id = next_id
        self._data[next_id] = snippet

    def list(self) -> Sequence[Snippet]:
        return list(self._data.values())

    def get(self, snippet_id: int) -> Snippet | None:
        return self._data.get(snippet_id)



    def delete(self, snippet_id: int) -> None:
        snippet = self._data.pop(snippet_id, None)
        if snippet is None:
            raise SnippetNotFoundError(f'Snippet id {snippet_id} not found')
