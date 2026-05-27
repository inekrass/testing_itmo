"""
Тесты для модуля library.py — управление книгами.
Практика 2: Фикстуры и композиция.

Демонстрирует:
- Использование фикстур из conftest.py
- Композицию фикстур (library_with_books зависит от empty_library + книг)
- Параметризацию для поиска
"""

import pytest
from library import Book, Library


# ══════════════════════════════════════════════════════════
#  ДОБАВЛЕНИЕ КНИГ
# ══════════════════════════════════════════════════════════


class TestAddBook:
    """Тесты добавления книг в каталог."""

    @pytest.mark.smoke
    def test_add_new_book(self, empty_library, book_python):
        """
        Given: пустая библиотека
        When:  добавляем новую книгу
        Then:  книга доступна по ISBN
        """
        # Arrange — фикстуры empty_library и book_python
        # Act
        empty_library.add_book(book_python)
        # Assert
        result = empty_library.get_book("978-1-001")
        assert result is not None
        assert result.title == "Python для профессионалов"
        assert result.total_copies == 3
        assert result.available_copies == 3

    def test_add_multiple_books(self, empty_library, book_python, book_algorithms):
        """Добавление нескольких разных книг."""
        # Act
        empty_library.add_book(book_python)
        empty_library.add_book(book_algorithms)
        # Assert
        assert empty_library.get_book("978-1-001") is not None
        assert empty_library.get_book("978-1-002") is not None

    def test_add_duplicate_increases_copies(self, library_with_books):
        """
        Given: библиотека уже содержит книгу с 3 экземплярами
        When:  добавляем ту же книгу ещё раз (2 копии)
        Then:  количество экземпляров увеличивается до 5
        """
        # Arrange
        extra = Book(
            title="Python для профессионалов",
            author="Лучано Рамальо",
            isbn="978-1-001",
            total_copies=2,
        )
        # Act
        library_with_books.add_book(extra)
        # Assert
        book = library_with_books.get_book("978-1-001")
        assert book.total_copies == 5
        assert book.available_copies == 5


# ══════════════════════════════════════════════════════════
#  ПОЛУЧЕНИЕ КНИГИ
# ══════════════════════════════════════════════════════════


class TestGetBook:
    """Тесты получения книги по ISBN."""

    def test_get_existing_book(self, library_with_books):
        """Существующая книга возвращается корректно."""
        book = library_with_books.get_book("978-1-001")
        assert book is not None
        assert book.title == "Python для профессионалов"

    def test_get_nonexistent_book_returns_none(self, empty_library):
        """Несуществующий ISBN → None."""
        result = empty_library.get_book("000-0-000")
        assert result is None

    def test_get_nonexistent_from_filled_library(self, library_with_books):
        """Несуществующий ISBN в непустой библиотеке → None."""
        result = library_with_books.get_book("999-9-999")
        assert result is None


# ══════════════════════════════════════════════════════════
#  ПОИСК КНИГ
# ══════════════════════════════════════════════════════════


class TestSearchBooks:
    """Тесты поиска книг по названию и автору."""

    @pytest.mark.parametrize(
        "query, expected_count",
        [
            pytest.param("python", 1, id="by_title_python"),
            pytest.param("алгоритмы", 1, id="by_title_algorithms"),
            pytest.param("тестирование", 1, id="by_title_testing"),
            pytest.param("Кормен", 1, id="by_author_kormen"),
            pytest.param("Рамальо", 1, id="by_author_ramalho"),
            pytest.param("Куликов", 1, id="by_author_kulikov"),
            pytest.param("философия", 0, id="no_results"),
            pytest.param("PYTHON", 1, id="case_insensitive_upper"),
            pytest.param("Python", 1, id="case_insensitive_mixed"),
        ],
    )
    def test_search_returns_correct_count(
        self, library_with_books, query, expected_count
    ):
        """Поиск возвращает правильное количество результатов."""
        results = library_with_books.search_books(query)
        assert len(results) == expected_count

    def test_search_partial_match(self, library_with_books):
        """Поиск по части слова находит книгу."""
        results = library_with_books.search_books("тест")
        assert len(results) == 1
        assert "Тестирование" in results[0].title

    def test_search_empty_library(self, empty_library):
        """Поиск в пустой библиотеке возвращает пустой список."""
        results = empty_library.search_books("python")
        assert results == []

    def test_search_returns_book_objects(self, library_with_books):
        """Результаты поиска — объекты Book с корректными атрибутами."""
        results = library_with_books.search_books("python")
        assert len(results) == 1
        book = results[0]
        assert isinstance(book, Book)
        assert book.isbn == "978-1-001"
        assert book.author == "Лучано Рамальо"
