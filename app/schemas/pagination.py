"""
Схемы для пагинации и фильтрации данных в API
"""
from typing import TypeVar, Generic, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class SortOrder(str, Enum):
    """Направление сортировки"""
    asc = "asc"
    desc = "desc"


class PaginationParams(BaseModel):
    """Параметры пагинации"""
    page: int = Field(default=1, ge=1, description="Номер страницы")
    per_page: int = Field(default=20, ge=1, le=100, description="Записей на странице")
    search: Optional[str] = Field(default=None, description="Поисковый запрос")
    sort_by: Optional[str] = Field(default=None, description="Поле для сортировки")
    sort_order: SortOrder = Field(default=SortOrder.asc, description="Направление сортировки")


# Generic type для элементов списка
T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Ответ с пагинацией"""
    items: List[T] = Field(description="Список элементов")
    total: int = Field(description="Общее количество элементов")
    page: int = Field(description="Текущая страница")
    per_page: int = Field(description="Элементов на странице")
    pages: int = Field(description="Всего страниц")
    has_next: bool = Field(description="Есть следующая страница")
    has_prev: bool = Field(description="Есть предыдущая страница")

    @classmethod
    def create(cls, items: List[T], total: int, page: int, per_page: int) -> "PaginatedResponse[T]":
        """Фабричный метод для создания ответа"""
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


# Схемы для блюд
class DishListItem(BaseModel):
    """Элемент списка блюд"""
    id: int
    name: str
    slug: str
    price: float
    weight: Optional[str] = None
    calories: Optional[int] = None
    is_available: bool = True
    sort_order: int = 0
    image_thumbnail: Optional[str] = None
    category_id: int
    category_name: str

    class Config:
        from_attributes = True


class DishFilters(BaseModel):
    """Фильтры для блюд"""
    category_id: Optional[int] = None
    is_available: Optional[bool] = None


# Схемы для категорий
class CategoryListItem(BaseModel):
    """Элемент списка категорий"""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0
    dishes_count: int = 0

    class Config:
        from_attributes = True


class CategoryFilters(BaseModel):
    """Фильтры для категорий"""
    is_active: Optional[bool] = None


# Схемы для администраторов
class AdminUserListItem(BaseModel):
    """Элемент списка администраторов"""
    id: int
    username: str
    is_active: bool = True
    last_login: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


# Схемы для логов аудита
class AuditLogListItem(BaseModel):
    """Элемент списка логов аудита"""
    id: int
    action: str
    action_display: str
    entity_type: str
    entity_type_display: str
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    admin_username: Optional[str] = None
    created_at: str
    old_data: Optional[Any] = None
    new_data: Optional[Any] = None

    class Config:
        from_attributes = True


class AuditLogFilters(BaseModel):
    """Фильтры для логов аудита"""
    entity_type: Optional[str] = None
    admin_user_id: Optional[int] = None
    action: Optional[str] = None
    entity_id: Optional[int] = None


# Схемы для массовых операций
class BulkActionRequest(BaseModel):
    """Запрос на массовое действие"""
    ids: List[int] = Field(min_length=1, description="ID элементов")
    action: str = Field(description="Действие: delete, activate, deactivate")


class BulkActionResponse(BaseModel):
    """Ответ на массовое действие"""
    success: bool
    affected: int = Field(description="Количество затронутых записей")
    message: str


# Схемы для изменения порядка
class ReorderItem(BaseModel):
    """Элемент для изменения порядка"""
    id: int
    sort_order: int


class ReorderRequest(BaseModel):
    """Запрос на изменение порядка"""
    items: List[ReorderItem]


# Схемы для inline-редактирования
class InlineEditRequest(BaseModel):
    """Запрос на inline-редактирование"""
    field: str = Field(description="Название поля")
    value: Any = Field(description="Новое значение")


class InlineEditResponse(BaseModel):
    """Ответ на inline-редактирование"""
    success: bool
    field: str
    value: Any
    message: Optional[str] = None
