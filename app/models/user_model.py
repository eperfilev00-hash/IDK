from typing import TYPE_CHECKING, List
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.post_model import Post
    from app.models.comment_model import Comment


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True,index=True)
    name: Mapped[str]
    surname: Mapped[str] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(unique=True,index=True)
    email: Mapped[str] = mapped_column(nullable=False,unique=True,index=True)
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)

    posts: Mapped[list["Post"]] = relationship(
    "Post", back_populates="author", cascade="all, delete-orphan"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="author", cascade="all, delete-orphan"
    )