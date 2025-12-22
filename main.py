import datetime
import time

from passlib.context import CryptContext
from starlette.responses import JSONResponse

from models import User, UserRole, Base
from sqlalchemy import Enum as SQLEnum, select
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware  # 【新增1】引入Session功能
import uvicorn
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, sessionmaker
from sqlalchemy.testing.schema import mapped_column
from sqlalchemy import DateTime, func, String, Float
from pydantic import BaseModel, Field
import enum
app = FastAPI()
#定义加密方法
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
# 数据库连接
DATABASE_URL = "postgresql+asyncpg://postgres:cynsjk1221!!@localhost:5432/postgres"
async_engine=create_async_engine(DATABASE_URL,echo=True,#日志输出
                                 pool_size=20,#连接池大小
                                 max_overflow=10 )#溢出连接数
async def create_table():
    async  with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)#使用base类的元数据进行创建
#app实例创建启动数据库连接
@app.on_event("startup")
async def startup_event():
    await create_table()
AsyncSession_Local=async_sessionmaker(bind=async_engine,class_=AsyncSession,#指定会话类
expire_on_commit= False #提交会话后不过期，不会重新查询数据库
 )
async  def get_datebase():
    async with AsyncSession_Local() as session:
        try:
            yield session #返回数据库会话给路由处理函数
            await session.commit() ##提交会话
        except:
            await session.rollback() #异常回滚会话
            raise
        finally:
            await session.close() #关闭会话


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    每次请求都会经过这里。
    负责：拦截未登录用户、给已登录用户续命。
    """
    path = request.url.path
    # A. 白名单：如果是去登录页面，或者拿静态资源，直接放行，不检查
    if path.startswith("/login") or path.startswith("/static"):
        return await call_next(request)
    # B. 检查口袋里有没有 'user' 凭证
    user = request.session.get("user_id")

    # C. 如果没有凭证（没登录，或者超时了），直接踢回 /login
    if not user:
        return RedirectResponse(url="/login")
    # D. 如果有凭证，说明正在操作，静默续命（重置 60 秒倒计时）?
    request.session["_keep_alive"] = time.time()
    return await call_next(request)
# 【新增2】配置 Session
# max_age=60 表示：如果用户 60 秒没有任何操作，登录状态自动失效
app.add_middleware(SessionMiddleware, secret_key="sadahdwioquhdu@@!#1hsajdashdas11", max_age=1800) # 60秒过期
app.mount("/static", StaticFiles(directory="static"), name="static")
# 1. 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")
# 2. 配置模板引擎
templates = Jinja2Templates(directory="templates")
# ================= 【新增3】 全局守卫 (中间件) =================


# =============================================================
# --- 路由定义 ---

# 【修改】根目录不再直接跳转登录，而是作为“登录后的主页”
# 只有登录成功的人才能看到这里，没登录的人会被上面的中间件拦截
@app.get("/")
async def home(request: Request):
    # --- 1. 原有的用户信息获取逻辑 (保持不变) ---
    user_id = request.session.get("user_id")
    role = request.session.get("role")
    username = request.session.get("username")

    # --- 2. 【新增】获取并清除 Flash 消息 (PRG模式的核心) ---
    # 使用 .pop("key", None) 的作用是：尝试取出这个 key 的值，取完后立刻在 Session 中删除它。
    # 这样当你按 F5 刷新时，因为已经被删除了，取到的就是 None，提示框就会消失。

    # 获取错误信息 (比如 "注册失败：用户名已存在")
    error_msg = request.session.pop("flash_error", None)

    # 获取成功信息 (比如 "注册成功！")
    success_msg = request.session.pop("flash_success", None)

    # 获取页面保持指令 (比如 "admin-register")
    # 如果这里有值，前端 JS 就会自动切到管理员注册页
    active_page = request.session.pop("next_active_page", None)

    # --- 3. 返回模板 ---
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user_id": user_id,
        "username": username,
        "role": role,

        # 【新增】把取出来的数据传给 HTML
        "error": error_msg,  # 对应前端 HTML 里的 {% if error %}
        "success_msg": success_msg,  # 对应前端 HTML 里的 {% if success_msg %}
        "active_page": active_page  # 对应前端 JS 里的 const serverActivePage
    })
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    渲染登录页面
    """
    # 优化体验：如果已经登录了，就别让人家再看登录页了，直接去首页
    if request.session.get("user"):
        return RedirectResponse(url="/")

    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, user_id: int = Form(...), password: str = Form(...),db: AsyncSession = Depends(get_datebase)):
    """
    处理登录表单提交
    """
    user = await db.get(User, user_id)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "工号(ID)不存在或密码错误"
        })
    hashed_password: str = user.password
    if not pwd_context.verify(password, hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "用户名或密码错误，请重试！"
        })
    request.session["user_id"] = user.user_id
    request.session["username"] = user.username
    request.session["role"] = user.role.value  # 如果是枚举，记得取 value
    return RedirectResponse(url="/", status_code=302)
# 【新增】退出登录路由
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()  # 清空 Session
    return RedirectResponse(url="/login")

    # 写法 2：如果是传统网页，直接重定向到登录页其实体验更好（“反正你也想出去”）
    # return RedirectResponse(url="/login", status_code=303)


@app.get("/admin/register")  # 浏览器访问这个地址时，显示注册页
async def register_page(request: Request):
    # 1. 从 Session 获取角色
    role = request.session.get("role")

    # 2. 安全检查：如果 Session 过期，或者不是 admin
    # 注意：这里要和数据库存的一致，如果是 "ADMIN" 记得改
    if not role or role!= "admin":
        return HTMLResponse("""
        <script>
            alert("⛔️ 严禁非法访问：您没有管理员权限！");
            window.location.href = "/"; // 踢回首页
        </script>
        """)
    # 3. 只有管理员才能看到这个页面
    return templates.TemplateResponse("register.html", {
        "request": request,
        "form_data": None,
        "alert_msg": None
    })

@app.post("/admin/register", response_class=HTMLResponse)
async def register_submit(
        request: Request,
        user_id: int = Form(...),
        username: str = Form(...),
        password: str = Form(...),
        role: str = Form(...),
        db: AsyncSession = Depends(get_datebase)
):
    try:
        # 1. 检查用户名逻辑...
        stmt = select(User).where(User.user_id == user_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            return templates.TemplateResponse("register.html", {
                "request": request,
                "alert_msg": {
                        "type": "error",                      # 弹窗类型：错误
                        "msg": f"注册失败：用户名 {username} 已存在！"  # 提示内容
                                         },
                "form_data": {  # 把用户填的数据传回去，防止清空，体验更好
                    "user_id": user_id,
                    "username": username,
                    "role": role
                }
            })


        # 2. 正常注册逻辑...
        hashed_password = pwd_context.hash(password)
        new_user = User(user_id=user_id,username=username, password=hashed_password, role=role)
        db.add(new_user)
        await db.commit()

        return templates.TemplateResponse("register.html", {
            "request": request,
            "alert_msg": {
                "type": "success",  # 弹窗类型：成功
                "msg": f"注册成功：用户 {user_id} 已创建！"  # 提示内容
            }, # 告诉前端弹窗
            "form_data": None
        })



    except Exception as e:

        return templates.TemplateResponse("register.html", {

            "request": request,

            "alert_msg": {

                "type": "error",

                "msg": f"注册失败：{str(e)}"

            },

            "form_data": {"user_id": user_id, "username": username, "role": role}

        })


# 启动入口
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)