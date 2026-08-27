import enum

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# Создаем Enum для приоритетов (в базе сохранится как текст или специальный тип)
class PriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WishItem(Base):  #Минимально рабочий код
    __tablename__ = "wish_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    link: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Как сильно пользователь желает получить этот подарок
    priority: Mapped[PriorityEnum] = mapped_column(
        Enum(PriorityEnum), default=PriorityEnum.MEDIUM, nullable=False
    )
    # Внешние ключи на владельца и забронировавшего желание
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    booked_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Поле для явного обращения к таблице User. Например wish.owner.username
    owner = relationship("User", foreign_keys=[user_id], back_populates="wishes")

    # Поле для явного обращения к таблице User. Например wish.booker.username
    booker = relationship("User", foreign_keys=[booked_by_user_id])
