"""
Корневой conftest.py — общие фикстуры для всех тестов.

Фикстуры в этом файле доступны во всех тестовых модулях
без явного импорта. pytest находит их автоматически.
"""

import sys
from pathlib import Path

# Добавляем src/ в путь, чтобы импорты работали
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
