"""
Модуль библиотечного каталога.
Практика 2: Фикстуры, параметризация, маркеры.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class Book:
    """Книга в библиотечном каталоге."""

    title: str
    author: str
    isbn: str
    total_copies: int
    available_copies: int = -1

    def __post_init__(self):
        if self.available_copies == -1:
            self.available_copies = self.total_copies


@dataclass
class Member:
    """Читатель библиотеки."""

    name: str
    member_id: str
    borrowed_books: list[str] = field(default_factory=list)
    max_books: int = 5


@dataclass
class BorrowRecord:
    """Запись о выдаче книги."""

    member_id: str
    isbn: str
    borrow_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None

    @property
    def is_overdue(self) -> bool:
        """Проверяет, просрочена ли книга."""
        if self.return_date:
            return self.return_date > self.due_date
        return datetime.now() > self.due_date

    @property
    def fine(self) -> float:
        """Штраф: 10 руб. за каждый день просрочки."""
        if not self.is_overdue:
            return 0.0
        if self.return_date:
            overdue_days = (self.return_date - self.due_date).days
        else:
            overdue_days = (datetime.now() - self.due_date).days
        return max(0, overdue_days * 10.0)


class Library:
    """Библиотека: управление книгами, читателями и выдачей."""

    def __init__(self):
        self.books: dict[str, Book] = {}
        self.members: dict[str, Member] = {}
        self.records: list[BorrowRecord] = []

    # ── Управление книгами ────────────────────────────

    def add_book(self, book: Book):
        """Добавляет книгу в каталог. При повторном добавлении увеличивает число копий."""
        if book.isbn in self.books:
            self.books[book.isbn].total_copies += book.total_copies
            self.books[book.isbn].available_copies += book.total_copies
        else:
            self.books[book.isbn] = book

    def get_book(self, isbn: str) -> Optional[Book]:
        """Возвращает книгу по ISBN или None."""
        return self.books.get(isbn)

    def search_books(self, query: str) -> list[Book]:
        """Ищет книги по названию или автору (без учёта регистра)."""
        query_lower = query.lower()
        return [
            b
            for b in self.books.values()
            if query_lower in b.title.lower() or query_lower in b.author.lower()
        ]

    # ── Управление читателями ─────────────────────────

    def register_member(self, member: Member):
        """Регистрирует нового читателя."""
        if member.member_id in self.members:
            raise ValueError(f"Читатель {member.member_id} уже зарегистрирован")
        self.members[member.member_id] = member

    def get_member(self, member_id: str) -> Optional[Member]:
        """Возвращает читателя по ID или None."""
        return self.members.get(member_id)

    # ── Выдача и возврат ──────────────────────────────

    def borrow_book(
        self, member_id: str, isbn: str, borrow_days: int = 14
    ) -> BorrowRecord:
        """
        Выдаёт книгу читателю.

        Raises:
            ValueError: Если читатель/книга не найдены, нет копий,
                        превышен лимит или книга уже на руках.
        """
        member = self.members.get(member_id)
        if member is None:
            raise ValueError(f"Читатель {member_id} не найден")

        book = self.books.get(isbn)
        if book is None:
            raise ValueError(f"Книга {isbn} не найдена")

        if book.available_copies <= 0:
            raise ValueError(
                f"Нет доступных экземпляров книги '{book.title}'"
            )

        if len(member.borrowed_books) >= member.max_books:
            raise ValueError(
                f"Читатель {member.name} достиг лимита ({member.max_books} книг)"
            )

        if isbn in member.borrowed_books:
            raise ValueError("Читатель уже взял эту книгу")

        now = datetime.now()
        record = BorrowRecord(
            member_id=member_id,
            isbn=isbn,
            borrow_date=now,
            due_date=now + timedelta(days=borrow_days),
        )

        book.available_copies -= 1
        member.borrowed_books.append(isbn)
        self.records.append(record)
        return record

    def return_book(self, member_id: str, isbn: str) -> BorrowRecord:
        """
        Принимает возврат книги от читателя.

        Raises:
            ValueError: Если читатель не найден, не брал эту книгу или запись не найдена.
        """
        member = self.members.get(member_id)
        if member is None:
            raise ValueError(f"Читатель {member_id} не найден")

        if isbn not in member.borrowed_books:
            raise ValueError(f"Читатель не брал книгу {isbn}")

        book = self.books.get(isbn)
        if book is None:
            raise ValueError(f"Книга {isbn} не найдена в каталоге")

        record = None
        for r in reversed(self.records):
            if (
                r.member_id == member_id
                and r.isbn == isbn
                and r.return_date is None
            ):
                record = r
                break

        if record is None:
            raise ValueError("Запись о выдаче не найдена")

        record.return_date = datetime.now()
        book.available_copies += 1
        member.borrowed_books.remove(isbn)
        return record

    # ── Статистика ────────────────────────────────────

    def get_overdue_records(self) -> list[BorrowRecord]:
        """Возвращает все просроченные и невозвращённые записи."""
        return [r for r in self.records if r.is_overdue and r.return_date is None]

    def get_member_history(self, member_id: str) -> list[BorrowRecord]:
        """Возвращает историю выдач конкретного читателя."""
        return [r for r in self.records if r.member_id == member_id]

    def get_popular_books(self, top_n: int = 5) -> list[tuple[str, int]]:
        """Возвращает топ-N самых популярных книг (по количеству выдач)."""
        borrow_count: dict[str, int] = {}
        for r in self.records:
            borrow_count[r.isbn] = borrow_count.get(r.isbn, 0) + 1
        sorted_books = sorted(
            borrow_count.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_books[:top_n]
