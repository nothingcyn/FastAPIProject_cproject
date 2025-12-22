from datetime import datetime, timezone
import enum
from sqlalchemy import Enum as SQLEnum, BigInteger, Integer
from sqlalchemy import DateTime, func, String,Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Dict, Any, Optional
class Base(DeclarativeBase):
    create_time: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(), comment="创建时间"
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(), comment="更新时间"
    )


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


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
    section: Mapped[str] = mapped_column(String(50), comment="所属部门")
    sign_uo_count: Mapped[int] = mapped_column(Integer, default=0, comment="本月登录出错次数")
class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Databaseset(Base):
    __tablename__ = "databaseset"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    # --- 新增：用于区分是哪张表（关键字段） ---
    # 例如存入: 'hr_leave', 'finance_expense', 'it_request'
    form_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    form_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    __table_args__ = (
        # 建议：加一个复合索引，加速查询某类表单下的数据
        Index("ix_type_user", "form_type", "user_id"),
    )