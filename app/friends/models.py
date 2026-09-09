# app/friends/models.py
from enum import Enum

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# Удобно использовать Enum для статуса дружбы
class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"

class Friendship(Base):
    __tablename__ = "friends"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    friend_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    relation: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    # Дополнительное ограничение, чтобы пользователь не мог добавить в друзья самого себя
    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="unique_user_friend_pair"),
    )
