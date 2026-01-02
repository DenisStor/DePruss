from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AuditLog(Base):
    """Модель для хранения истории изменений в админ-панели"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Кто сделал изменение
    admin_user_id = Column(Integer, ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True, index=True)
    admin_user = relationship("AdminUser", backref="audit_logs")

    # Тип действия: create, update, delete, login, logout
    action = Column(String(50), nullable=False, index=True)

    # Тип сущности: dish, category, admin_user
    entity_type = Column(String(50), nullable=False, index=True)

    # ID сущности (может быть NULL для login/logout)
    entity_id = Column(Integer, nullable=True, index=True)

    # Название сущности (для отображения в логах, даже после удаления)
    entity_name = Column(String(200), nullable=True)

    # Старые и новые данные в JSON формате
    old_data = Column(JSON, nullable=True)
    new_data = Column(JSON, nullable=True)

    # Дополнительная информация (IP, User-Agent и т.д.)
    details = Column(Text, nullable=True)

    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity_type}:{self.entity_id}>"

    @property
    def action_display(self) -> str:
        """Человекочитаемое название действия"""
        actions = {
            'create': 'Создание',
            'update': 'Изменение',
            'delete': 'Удаление',
            'login': 'Вход',
            'logout': 'Выход',
            'activate': 'Активация',
            'deactivate': 'Деактивация',
            'bulk_delete': 'Массовое удаление',
            'bulk_activate': 'Массовая активация',
            'bulk_deactivate': 'Массовая деактивация',
            'reorder': 'Изменение порядка',
            'import': 'Импорт',
            'export': 'Экспорт'
        }
        return actions.get(self.action, self.action)

    @property
    def entity_type_display(self) -> str:
        """Человекочитаемое название типа сущности"""
        types = {
            'dish': 'Блюдо',
            'category': 'Категория',
            'admin_user': 'Администратор',
            'system': 'Система'
        }
        return types.get(self.entity_type, self.entity_type)
