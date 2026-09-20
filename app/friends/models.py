# app/friends/models.py
from enum import Enum

from sqlalchemy import CheckConstraint, ForeignKey, String
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
    relation: Mapped[FriendshipStatus] = mapped_column(
        String(20),
        default=FriendshipStatus.PENDING,
        server_default=FriendshipStatus.PENDING.value,
    )
    # Дополнительное ограничение, чтобы пользователь не мог добавить в друзья самого себя
    __table_args__ = (
        CheckConstraint("user_id <> friend_id", name="check_user_not_self_friend"),
    )
