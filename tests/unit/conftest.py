"""
conftest.py для unit-тестов.

Содержит фикстуры для модулей library и cart.
Фикстуры автоматически доступны во всех тестах этой папки.
"""

import pytest
from library import Book, Member, Library
from cart import Product, Cart


# ══════════════════════════════════════════════════════════
#  ФИКСТУРЫ: КНИГИ
# ══════════════════════════════════════════════════════════


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
def book_testing():
    """Книга 'Тестирование ПО' — 1 экземпляр."""
    return Book(
        title="Тестирование программного обеспечения",
        author="Святослав Куликов",
        isbn="978-1-003",
        total_copies=1,
    )


# ══════════════════════════════════════════════════════════
#  ФИКСТУРЫ: ЧИТАТЕЛИ
# ══════════════════════════════════════════════════════════


@pytest.fixture
def member_anna():
    """Читатель Анна Иванова — стандартный лимит (5 книг)."""
    return Member(name="Анна Иванова", member_id="M001")


@pytest.fixture
def member_boris():
    """Читатель Борис Петров — стандартный лимит (5 книг)."""
    return Member(name="Борис Петров", member_id="M002")


@pytest.fixture
def member_limited():
    """Читатель Виктор Сидоров — ограниченный лимит (2 книги)."""
    return Member(name="Виктор Сидоров", member_id="M003", max_books=2)


# ══════════════════════════════════════════════════════════
#  ФИКСТУРЫ: БИБЛИОТЕКА
# ══════════════════════════════════════════════════════════


@pytest.fixture
def empty_library():
    """Пустая библиотека без книг и читателей."""
    return Library()


@pytest.fixture
def library_with_books(empty_library, book_python, book_algorithms, book_testing):
    """Библиотека с тремя книгами, без читателей."""
    empty_library.add_book(book_python)
    empty_library.add_book(book_algorithms)
    empty_library.add_book(book_testing)
    return empty_library


@pytest.fixture
def library_full(library_with_books, member_anna, member_boris):
    """Библиотека с книгами и двумя зарегистрированными читателями."""
    library_with_books.register_member(member_anna)
    library_with_books.register_member(member_boris)
    return library_with_books


@pytest.fixture
def library_with_borrows(library_full):
    """Библиотека, в которой Анна уже взяла книгу по Python."""
    library_full.borrow_book("M001", "978-1-001")
    return library_full


# ══════════════════════════════════════════════════════════
#  ФИКСТУРЫ: ТОВАРЫ И КОРЗИНА
# ══════════════════════════════════════════════════════════


@pytest.fixture
def product_book():
    """Товар 'Книга' — 500 руб., 10 на складе."""
    return Product(name="Книга", price=500.0, stock=10)


@pytest.fixture
def product_pen():
    """Товар 'Ручка' — 50 руб., 100 на складе."""
    return Product(name="Ручка", price=50.0, stock=100)


@pytest.fixture
def product_laptop():
    """Товар 'Ноутбук' — 75000 руб., 2 на складе."""
    return Product(name="Ноутбук", price=75000.0, stock=2)


@pytest.fixture
def empty_cart():
    """Пустая корзина."""
    return Cart()


@pytest.fixture
def cart_with_items(empty_cart, product_book, product_pen):
    """Корзина с книгой (×2) и ручкой (×3)."""
    empty_cart.add(product_book, 2)
    empty_cart.add(product_pen, 3)
    return empty_cart
