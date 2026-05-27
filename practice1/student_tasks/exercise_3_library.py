"""
СТАРТОВЫЙ ФАЙЛ — Занятие 2, Упражнения с фикстурами и параметризацией.

Задача:
    1. Определить нужные фикстуры в этом файле
    2. Написать тесты с использованием фикстур
    3. Применить параметризацию для поиска
    4. Разметить тесты маркерами smoke/boundary/negative

Эталон: tests/unit/test_library_books.py, test_library_borrow.py

Как запустить:
    pytest student_tasks/exercise_3_library.py -v
    pytest student_tasks/exercise_3_library.py -m smoke -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from library import Book, Member, Library


# ══════════════════════════════════════════════════════════════
#  ФИКСТУРЫ
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def book_python():
    """Книга 'Python для профессионалов' — 3 экземпляра."""
    return Book(
        title="Python для профессионалов",
        author="Лучано Рамальо",
        isbn="978-1-001",
        total_copies=3,
    )


@pytest.fixture
def book_algorithms():
    """Книга 'Алгоритмы и структуры данных' — 2 экземпляра."""
    return Book(
        title="Алгоритмы и структуры данных",
        author="Томас Кормен",
        isbn="978-1-002",
        total_copies=2,
    )


@pytest.fixture
def member_anna():
    """Читатель Анна — ID M001."""
    return Member(name="Анна Иванова", member_id="M001")


@pytest.fixture
def empty_library():
    """Пустая библиотека."""
    return Library()


@pytest.fixture
def library_with_books(empty_library, book_python, book_algorithms):
    """Библиотека с двумя книгами (композиция фикстур)."""
    empty_library.add_book(book_python)
    empty_library.add_book(book_algorithms)
    return empty_library


@pytest.fixture
def library_full(library_with_books, member_anna):
    """Библиотека с книгами и зарегистрированным читателем."""
    library_with_books.register_member(member_anna)
    return library_with_books


# ══════════════════════════════════════════════════════════════
#  ТЕСТЫ С ФИКСТУРАМИ
# ══════════════════════════════════════════════════════════════


class TestAddBook:
    """Добавление книг."""

    @pytest.mark.smoke
    def test_add_new_book(self, empty_library, book_python):
        """Добавление новой книги в пустую библиотеку."""
        empty_library.add_book(book_python)
        assert empty_library.get_book("978-1-001") is not None

    def test_add_duplicate_increases_copies(self, library_with_books):
        """При повторном добавлении увеличивается число экземпляров."""
        extra_book = Book(
            title="Python для профессионалов",
            author="Лучано Рамальо",
            isbn="978-1-001",
            total_copies=2,
        )

        library_with_books.add_book(extra_book)

        book = library_with_books.get_book("978-1-001")
        assert book.total_copies == 5
        assert book.available_copies == 5


# ══════════════════════════════════════════════════════════════
#  ПАРАМЕТРИЗАЦИЯ
# ══════════════════════════════════════════════════════════════


class TestSearchBooks:
    """Поиск книг — использует параметризацию."""

    @pytest.mark.parametrize(
        "query, expected_count",
        [
            pytest.param("python", 1, id="by_title"),
            pytest.param("Кормен", 1, id="by_author"),
            pytest.param("PYTHON", 1, id="case_insensitive_upper"),
            pytest.param("несуществующая книга", 0, id="not_found"),
            pytest.param("а", 2, id="multiple_matches"),
        ],
    )
    def test_search(self, library_with_books, query, expected_count):
        results = library_with_books.search_books(query)
        assert len(results) == expected_count


# ══════════════════════════════════════════════════════════════
#  МАРКЕРЫ: SMOKE, BOUNDARY, NEGATIVE
# ══════════════════════════════════════════════════════════════


class TestBorrow:
    """Выдача книг — демонстрация маркеров."""

    @pytest.mark.smoke
    def test_successful_borrow(self, library_full):
        """Анна берёт книгу — happy path."""
        record = library_full.borrow_book("M001", "978-1-001")
        assert record.isbn == "978-1-001"

    @pytest.mark.negative
    def test_borrow_unknown_member(self, library_full):
        """Незарегистрированный читатель → ValueError."""
        with pytest.raises(ValueError, match="не найден"):
            library_full.borrow_book("M999", "978-1-001")

    @pytest.mark.negative
    def test_borrow_unknown_book(self, library_full):
        """Несуществующая книга → ValueError."""
        with pytest.raises(ValueError, match="не найдена"):
            library_full.borrow_book("M001", "000-0-000")

    @pytest.mark.boundary
    def test_borrow_same_book_twice(self, library_full):
        """Повторная выдача той же книги одному читателю → ValueError."""
        library_full.borrow_book("M001", "978-1-001")

        with pytest.raises(ValueError, match="уже взял"):
            library_full.borrow_book("M001", "978-1-001")
