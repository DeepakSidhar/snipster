from datetime import UTC, datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class Language(str, Enum):
    # These are the allowed language the short code is stored in the DB
    python = "py"
    javascript = "js"
    rust = "rs"


class SnippetBase(SQLModel):
    # Shared fields: Anything you want both SnippetBase
    # and Snippet goes here. AVOIDS repeating.
    title: str
    code: str
    description: str | None = None
    language: Language
    tags: str | None = None
    favorite: bool = False


class Snippet(SnippetBase, table=True):
    # The actual database with shared fields from SnippetBase
    # and adds database-specific fields.

    id: int | None = Field(default=None, primary_key=True)
    # id starts as None when the object is created.
    # The database assigns the id after session.commit()
    # and session.refresh().

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    # created_at is automatically set when a new Snippet object is created.

    updated_at: datetime | None = None

    # updated_at can stay empty at first.
    # You can update it later whenever the record changes.
    def __str__(self) -> str:
        return f"{self.title} ({self.language.value})"

    # Property makes this an attribute returns an empyt list
    # if data is none or blank Otherwise creates a new list that
    # can handle comma seperated values, removing white space
    @property
    def tag_list(self) -> list[str]:
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

    # https://www.geeksforgeeks.org/python/classmethod-in-python/
    # class method(cls) can construct a snippet kwarg grabs the agruments provided
    # expecting a list along the lines of line 16
    # get the title and checkinng the len is not less the  3
    # if it is we give an error or return sinppet instance.
    @classmethod
    def create_snippet(cls, **kwarg):
        title = kwarg.get("title")
        if title is None or len(title) < 3:
            raise ValueError("Title must be at least 3 characters long")
        return cls(**kwarg)
