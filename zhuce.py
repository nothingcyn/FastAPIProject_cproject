
import asyncio  # ✅ 一定要导入 asyncio
import enum
from datetime import datetime
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.types import Enum as SQLEnum
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from models import User, UserRole

# -----------------------------
# 数据库连接
# -----------------------------
DATABASE_URL = "postgresql+asyncpg://postgres:cynsjk1221!!@localhost:5432/postgres"
# -----------------------------
# 加密密码
# -----------------------------
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# -----------------------------
# 添加超级用户（只添加一个）
# -----------------------------
async def main():
    username = "许昊翔"
    password = "xhxtestwebsite!?"
    password_hash = pwd_context.hash(password)

    # 这里 user_id 固定为 1，可根据情况修改
    user = User(
        user_id=10000001,
        username=username,
        password=password_hash,
        role=UserRole.ADMIN,
        section="北京化工大学",
    )

    engine = create_async_engine(DATABASE_URL, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        session.add(user)
        try:
            await session.commit()
            print(f"✅ 超级用户 {username} 创建成功！")
        except Exception as e:
            await session.rollback()
            print("❌ 创建用户失败:", e)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())