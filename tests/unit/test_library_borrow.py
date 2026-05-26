"""
Тесты для модуля library.py — выдача, возврат и статистика.
Практика 2: Фикстуры, маркеры и покрытие.

Демонстрирует:
- Многоуровневые фикстуры (library_full, library_with_borrows)
- Маркеры smoke, boundary, negative
- Тестирование побочных эффектов (изменение состояния нескольких объектов)
"""

import pytest
from library import Library, Book, Member


# ══════════════════════════════════════════════════════════
#  РЕГИСТРАЦИЯ ЧИТАТЕЛЕЙ
# ══════════════════════════════════════════════════════════


class TestRegisterMember:
    """Тесты регистрации читателей."""

    @pytest.mark.smoke
    def test_register_new_member(self, empty_library, member_anna):
        """Регистрация нового читателя."""
        # Act
        empty_library.register_member(member_anna)
        # Assert
        result = empty_library.get_member("M001")
        assert result is not None
        assert result.name == "Анна Иванова"

    @pytest.mark.negative
    def test_register_duplicate_raises(self, library_full):
        """
        Given: Анна уже зарегистрирована
        When:  пытаемся зарегистрировать другого читателя с тем же ID
        Then:  ValueError
        """
        duplicate = Member(name="Анна Другая", member_id="M001")
        with pytest.raises(ValueError, match="уже зарегистрирован"):
            library_full.register_member(duplicate)

    def test_get_nonexistent_member(self, empty_library):
        """Запрос несуществующего читателя → None."""
        assert empty_library.get_member("M999") is None


# ══════════════════════════════════════════════════════════
#  ВЫДАЧА КНИГ
# ══════════════════════════════════════════════════════════


class TestBorrowBook:
    """Тесты выдачи книг читателям."""

    @pytest.mark.smoke
    def test_successful_borrow(self, library_full):
        """
        Given: библиотека с книгами и читателями
        When:  Анна берёт книгу по Python
        Then:  создаётся запись, копии уменьшаются, книга в списке Анны
        """
        # Act
        record = library_full.borrow_book("M001", "978-1-001")

        # Assert — запись о выдаче
        assert record.member_id == "M001"
        assert record.isbn == "978-1-001"
        assert record.return_date is None

        # Assert — побочный эффект: книга
        book = library_full.get_book("978-1-001")
        assert book.available_copies == 2  # Было 3

        # Assert — побочный эффект: читатель
        member = library_full.get_member("M001")
        assert "978-1-001" in member.borrowed_books

    def test_borrow_creates_record(self, library_full):
        """Каждая выдача создаёт запись в library.records."""
        assert len(library_full.records) == 0
        library_full.borrow_book("M001", "978-1-001")
        assert len(library_full.records) == 1

    def test_borrow_multiple_books(self, library_full):
        """Читатель может взять несколько разных книг."""
        library_full.borrow_book("M001", "978-1-001")
        library_full.borrow_book("M001", "978-1-002")
        member = library_full.get_member("M001")
        assert len(member.borrowed_books) == 2

    @pytest.mark.boundary
    def test_borrow_last_copy(self, library_full):
        """
        Given: книга «Тестирование» имеет 1 экземпляр
        When:  Анна берёт эту книгу
        Then:  available_copies = 0
        """
        library_full.borrow_book("M001", "978-1-003")
        book = library_full.get_book("978-1-003")
        assert book.available_copies == 0

    @pytest.mark.negative
    def test_borrow_no_copies_available(self, library_full):
        """
        Given: все экземпляры книги выданы
        When:  другой читатель пытается взять ту же книгу
        Then:  ValueError
        """
        library_full.borrow_book("M001", "978-1-003")  # Последний экземпляр
        with pytest.raises(ValueError, match="Нет доступных экземпляров"):
            library_full.borrow_book("M002", "978-1-003")

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

    @pytest.mark.negative
    def test_borrow_same_book_twice(self, library_full):
        """
        Given: Анна уже взяла книгу
        When:  Анна пытается взять ту же книгу снова
        Then:  ValueError
        """
        library_full.borrow_book("M001", "978-1-001")
        with pytest.raises(ValueError, match="уже взял"):
            library_full.borrow_book("M001", "978-1-001")

    @pytest.mark.boundary
    def test_borrow_at_limit(self, library_full, member_limited):
        """
        Given: читатель с лимитом 2 книги, уже взял 2
        When:  пытается взять третью
        Then:  ValueError
        """
        library_full.register_member(member_limited)
        library_full.borrow_book("M003", "978-1-001")
        library_full.borrow_book("M003", "978-1-002")

        with pytest.raises(ValueError, match="лимита"):
            library_full.borrow_book("M003", "978-1-003")

    @pytest.mark.boundary
    def test_borrow_at_limit_minus_one(self, library_full, member_limited):
        """
        Given: читатель с лимитом 2 книги, взял 1
        When:  берёт вторую
        Then:  успешно (ещё в пределах лимита)
        """
        library_full.register_member(member_limited)
        library_full.borrow_book("M003", "978-1-001")
        # Вторая книга — ещё можно
        library_full.borrow_book("M003", "978-1-002")
        member = library_full.get_member("M003")
        assert len(member.borrowed_books) == 2


# ══════════════════════════════════════════════════════════
#  ВОЗВРАТ КНИГ
# ══════════════════════════════════════════════════════════


class TestReturnBook:
    """Тесты возврата книг."""

    @pytest.mark.smoke
    def test_successful_return(self, library_with_borrows):
        """
        Given: Анна взяла книгу по Python
        When:  Анна возвращает книгу
        Then:  return_date заполнен, копии +1, книга убрана из списка Анны
        """
        # Act
        record = library_with_borrows.return_book("M001", "978-1-001")

        # Assert — запись обновлена
        assert record.return_date is not None

        # Assert — копии вернулись
        book = library_with_borrows.get_book("978-1-001")
        assert book.available_copies == 3

        # Assert — книга убрана из списка читателя
        member = library_with_borrows.get_member("M001")
        assert "978-1-001" not in member.borrowed_books

    def test_return_allows_reborrow(self, library_with_borrows):
        """После возврата книгу можно взять снова."""
        library_with_borrows.return_book("M001", "978-1-001")
        # Теперь можно взять повторно
        record = library_with_borrows.borrow_book("M001", "978-1-001")
        assert record.isbn == "978-1-001"

    @pytest.mark.negative
    def test_return_not_borrowed_raises(self, library_full):
        """Попытка вернуть книгу, которую не брали → ValueError."""
        with pytest.raises(ValueError, match="не брал"):
            library_full.return_book("M001", "978-1-001")

    @pytest.mark.negative
    def test_return_unknown_member_raises(self, library_with_borrows):
        """Возврат от несуществующего читателя → ValueError."""
        with pytest.raises(ValueError, match="не найден"):
            library_with_borrows.return_book("M999", "978-1-001")


# ══════════════════════════════════════════════════════════
#  СТАТИСТИКА
# ══════════════════════════════════════════════════════════


class TestLibraryStatistics:
    """Тесты статистических методов."""

    def test_member_history_empty(self, library_full):
        """История пустая, если читатель ничего не брал."""
        history = library_full.get_member_history("M001")
        assert history == []

    def test_member_history_after_borrow(self, library_with_borrows):
        """История содержит записи о выдаче."""
        history = library_with_borrows.get_member_history("M001")
        assert len(history) == 1
        assert history[0].isbn == "978-1-001"

    def test_member_history_after_borrow_and_return(self, library_with_borrows):
        """История сохраняется и после возврата."""
        library_with_borrows.return_book("M001", "978-1-001")
        history = library_with_borrows.get_member_history("M001")
        assert len(history) == 1
        assert history[0].return_date is not None

    def test_popular_books_empty(self, library_full):
        """Топ пуст, если никто ничего не брал."""
        popular = library_full.get_popular_books()
        assert popular == []

    def test_popular_books_ranking(self, library_full):
        """
        Given: книгу Python брали 3 раза, Алгоритмы — 1 раз
        When:  запрашиваем топ
        Then:  Python первый
        """
        # Берём Python 3 раза (разные читатели + возврат)
        library_full.borrow_book("M001", "978-1-001")
        library_full.return_book("M001", "978-1-001")
        library_full.borrow_book("M001", "978-1-001")
        library_full.return_book("M001", "978-1-001")
        library_full.borrow_book("M002", "978-1-001")

        # Берём Алгоритмы 1 раз
        library_full.borrow_book("M001", "978-1-002")

        popular = library_full.get_popular_books(top_n=2)
        assert len(popular) == 2
        assert popular[0] == ("978-1-001", 3)  # Python — лидер
        assert popular[1] == ("978-1-002", 1)  # Алгоритмы — второе место

    def test_popular_books_top_n(self, library_full):
        """top_n ограничивает количество результатов."""
        library_full.borrow_book("M001", "978-1-001")
        library_full.borrow_book("M001", "978-1-002")
        library_full.borrow_book("M002", "978-1-003")

        popular = library_full.get_popular_books(top_n=1)
        assert len(popular) == 1
