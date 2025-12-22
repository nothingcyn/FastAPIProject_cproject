from datetime import datetime, timezone
import enum

import integer
from jinja2.lexer import integer_re
from sqlalchemy import Enum as SQLEnum, BigInteger, Integer
from sqlalchemy import DateTime, func, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    create_time: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(), comment="创建时间"
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(), comment="更新时间"
    )


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column( Integer,primary_key=True, autoincrement=False)
    username: Mapped[str] = mapped_column(String(50), index=True)
    password: Mapped[str] = mapped_column(String(255))

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(
            UserRole,
            name="userrole",
            native_enum=True,
            create_constraint=False  # 已存在 ENUM 必须加
        ),
        server_default=UserRole.USER.value,
        nullable=False,
        comment="用户角色"
    )
