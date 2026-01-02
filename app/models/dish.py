from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Dish(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    weight = Column(String(50), nullable=True)
    calories = Column(Integer, nullable=True)
    is_available = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)

    # Image paths (WebP format)
    image_thumbnail = Column(String(500), nullable=True)
    image_small = Column(String(500), nullable=True)
    image_medium = Column(String(500), nullable=True)
    image_large = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="dishes")

    def __repr__(self):
        return f"<Dish {self.name}>"

    @property
    def has_image(self) -> bool:
        return bool(self.image_small)
