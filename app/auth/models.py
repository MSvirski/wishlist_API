from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"  #Имя таблицы в самой postgreSQL

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)

    # Указываем, что список желаний пользователя строится по ключу user_id из таблицы wish_items
    wishes = relationship("WishItem", foreign_keys="WishItem.user_id", back_populates="owner",
                          cascade="all, delete-orphan")
