from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user_model import User
    from app.models.post_model import Post


class Comment(Base):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey('posts.id', ondelete='CASCADE'), index=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE')
    )

    author: Mapped["User"] = relationship(
        "User", foreign_keys=[author_id], back_populates="comments", viewonly=True
    )


    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('comments.id', ondelete='CASCADE'), index=True, default=None
    )

    content: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    is_deleted: Mapped[bool] = mapped_column(default=False)

    post: Mapped["Post"] = relationship("Post", back_populates="comments")

    parent: Mapped[Optional["Comment"]] = relationship(
        "Comment", remote_side=[id], back_populates="replies"
    )
    replies: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan"
    )