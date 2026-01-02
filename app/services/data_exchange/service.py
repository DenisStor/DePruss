"""
Data exchange service for export/import operations.
"""
from typing import List, Dict, Any, Tuple, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from slugify import slugify

from app.models import Dish, Category
from .helpers import bool_to_str, str_to_bool, safe_int, safe_float
from .excel import create_excel_workbook, read_excel_rows
from .csv_handler import create_csv_content, read_csv_rows, create_csv_template


class DataExchangeService:
    """Service for data export and import."""

    # Common headers
    DISH_HEADERS = [
        'ID', 'Название', 'Категория', 'Описание', 'Цена',
        'Вес', 'Калории', 'В наличии', 'Порядок сортировки'
    ]
    DISH_HEADERS_SHORT = [
        'ID', 'Название', 'Категория', 'Описание', 'Цена',
        'Вес', 'Калории', 'В наличии', 'Порядок'
    ]
    CATEGORY_HEADERS = ['ID', 'Название', 'Описание', 'Активна', 'Порядок сортировки']
    CATEGORY_HEADERS_SHORT = ['ID', 'Название', 'Описание', 'Активна', 'Порядок']

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== DATA PREPARATION ====================

    async def _get_dishes(self) -> List[Dish]:
        """Fetch all dishes with categories."""
        result = await self.db.execute(
            select(Dish)
            .options(selectinload(Dish.category))
            .order_by(Dish.category_id, Dish.sort_order)
        )
        return result.scalars().all()

    async def _get_categories(self) -> List[Category]:
        """Fetch all categories."""
        result = await self.db.execute(
            select(Category).order_by(Category.sort_order)
        )
        return result.scalars().all()

    async def _get_categories_map(self) -> Dict[str, int]:
        """Get category name to ID mapping."""
        result = await self.db.execute(select(Category))
        return {c.name.lower(): c.id for c in result.scalars().all()}

    def _dish_to_row(self, dish: Dish) -> List[Any]:
        """Convert dish to row values."""
        return [
            dish.id,
            dish.name,
            dish.category.name if dish.category else '',
            dish.description or '',
            dish.price,
            dish.weight or '',
            dish.calories or '',
            bool_to_str(dish.is_available),
            dish.sort_order
        ]

    def _category_to_row(self, cat: Category) -> List[Any]:
        """Convert category to row values."""
        return [
            cat.id,
            cat.name,
            cat.description or '',
            bool_to_str(cat.is_active),
            cat.sort_order
        ]

    # ==================== EXPORT ====================

    async def export_dishes_csv(self) -> str:
        """Export dishes to CSV format."""
        dishes = await self._get_dishes()
        rows = [self._dish_to_row(d) for d in dishes]
        return create_csv_content(self.DISH_HEADERS, rows)

    async def export_dishes_excel(self) -> bytes:
        """Export dishes to Excel format."""
        dishes = await self._get_dishes()
        rows = [self._dish_to_row(d) for d in dishes]
        return create_excel_workbook("Блюда", self.DISH_HEADERS_SHORT, rows)

    async def export_categories_csv(self) -> str:
        """Export categories to CSV format."""
        categories = await self._get_categories()
        rows = [self._category_to_row(c) for c in categories]
        return create_csv_content(self.CATEGORY_HEADERS, rows)

    async def export_categories_excel(self) -> bytes:
        """Export categories to Excel format."""
        categories = await self._get_categories()
        rows = [self._category_to_row(c) for c in categories]
        return create_excel_workbook("Категории", self.CATEGORY_HEADERS_SHORT, rows)

    # ==================== IMPORT ====================

    async def import_dishes_csv(self, content: bytes) -> Tuple[int, int, List[str]]:
        """Import dishes from CSV. Returns (created, updated, errors)."""
        return await self._import_dishes(read_csv_rows(content))

    async def import_dishes_excel(self, content: bytes) -> Tuple[int, int, List[str]]:
        """Import dishes from Excel. Returns (created, updated, errors)."""
        return await self._import_dishes(read_excel_rows(content))

    async def _import_dishes(self, rows_iter) -> Tuple[int, int, List[str]]:
        """Import dishes from row iterator."""
        categories = await self._get_categories_map()
        errors = []
        created = updated = 0

        try:
            for row_num, row in rows_iter:
                try:
                    result = await self._import_dish_row(row, row_num, categories)
                    if result == 'created':
                        created += 1
                    elif result == 'updated':
                        updated += 1
                    elif result:
                        errors.append(result)
                except Exception as e:
                    errors.append(f"Строка {row_num}: {str(e)}")

            await self.db.commit()
        except Exception as e:
            errors.append(f"Ошибка чтения файла: {str(e)}")

        return created, updated, errors

    async def _import_dish_row(
        self, row: Dict[str, Any], row_num: int, categories: Dict[str, int]
    ) -> Optional[str]:
        """Import single dish row. Returns: 'created', 'updated', error, or None."""
        name = str(row.get('Название', '')).strip()
        if not name:
            return f"Строка {row_num}: Пустое название"

        category_name = str(row.get('Категория', '')).strip().lower()
        category_id = categories.get(category_name)
        if not category_id:
            return f"Строка {row_num}: Категория '{category_name}' не найдена"

        price = safe_float(row.get('Цена'))
        if price <= 0:
            return f"Строка {row_num}: Некорректная цена"

        dish_data = {
            'name': name,
            'slug': slugify(name, lowercase=True),
            'category_id': category_id,
            'description': str(row.get('Описание', '') or ''),
            'price': price,
            'weight': str(row.get('Вес', '') or ''),
            'calories': safe_int(row.get('Калории')),
            'is_available': str_to_bool(row.get('В наличии', '')),
            'sort_order': safe_int(row.get('Порядок сортировки') or row.get('Порядок'), 0)
        }

        dish_id = safe_int(row.get('ID'))

        if dish_id:
            result = await self.db.execute(select(Dish).where(Dish.id == dish_id))
            dish = result.scalar_one_or_none()
            if dish:
                for key, value in dish_data.items():
                    setattr(dish, key, value)
                return 'updated'
            else:
                return f"Строка {row_num}: Блюдо с ID {dish_id} не найдено"
        else:
            dish = Dish(**dish_data)
            self.db.add(dish)
            return 'created'

    async def import_categories_csv(self, content: bytes) -> Tuple[int, int, List[str]]:
        """Import categories from CSV. Returns (created, updated, errors)."""
        return await self._import_categories(read_csv_rows(content))

    async def _import_categories(self, rows_iter) -> Tuple[int, int, List[str]]:
        """Import categories from row iterator."""
        errors = []
        created = updated = 0

        try:
            for row_num, row in rows_iter:
                try:
                    result = await self._import_category_row(row, row_num)
                    if result == 'created':
                        created += 1
                    elif result == 'updated':
                        updated += 1
                    elif result:
                        errors.append(result)
                except Exception as e:
                    errors.append(f"Строка {row_num}: {str(e)}")

            await self.db.commit()
        except Exception as e:
            errors.append(f"Ошибка чтения файла: {str(e)}")

        return created, updated, errors

    async def _import_category_row(self, row: Dict[str, Any], row_num: int) -> Optional[str]:
        """Import single category row. Returns: 'created', 'updated', error, or None."""
        name = str(row.get('Название', '')).strip()
        if not name:
            return f"Строка {row_num}: Пустое название"

        cat_data = {
            'name': name,
            'slug': slugify(name, lowercase=True),
            'description': str(row.get('Описание', '') or ''),
            'is_active': str_to_bool(row.get('Активна', '')),
            'sort_order': safe_int(row.get('Порядок сортировки') or row.get('Порядок'), 0)
        }

        cat_id = safe_int(row.get('ID'))

        if cat_id:
            result = await self.db.execute(select(Category).where(Category.id == cat_id))
            cat = result.scalar_one_or_none()
            if cat:
                for key, value in cat_data.items():
                    setattr(cat, key, value)
                return 'updated'
            else:
                return f"Строка {row_num}: Категория с ID {cat_id} не найдена"
        else:
            cat = Category(**cat_data)
            self.db.add(cat)
            return 'created'

    # ==================== TEMPLATES ====================

    def get_dishes_template_csv(self) -> str:
        """Get CSV template for dish import."""
        example = ['', 'Пример блюда', 'Закуски', 'Описание блюда', '500',
                   '250 г', '350', 'Нет', 'Нет', 'Да', '1']
        return create_csv_template(self.DISH_HEADERS, example)

    def get_categories_template_csv(self) -> str:
        """Get CSV template for category import."""
        example = ['', 'Пример категории', 'Описание категории', 'Да', '1']
        return create_csv_template(self.CATEGORY_HEADERS, example)
