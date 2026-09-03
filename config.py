"""校桥 CampusBridge 配置

架构(2026.09 起)：
- 强制单 MySQL 实例（主库，演示用 3306），任何连接失败直接抛出 RuntimeError 阻止启动
- 不再提供 SQLite 自动降级 / SQLite 暂存 / 回灌脚本；
- 如要搭建「演示型主从」：参见 scripts/deploy_mysql_ms_demo.sh 与 README 对应章节，
  Flask 业务代码永远只写/读主库，从库仅用于 SHOW SLAVE STATUS 演示和手动主写从查验证。
"""

import os
import urllib.parse

import pymysql
from dotenv import load_dotenv

pymysql.install_as_MySQLdb()

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# 统一子目录：数据库 SQL 脚本与种子脚本放 database/、运维脚本放 scripts/、前端 Node 工具放 frontend/
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
os.makedirs(DATABASE_DIR, exist_ok=True)
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')


def _build_mysql_uri(host: str, port: str, user: str, password: str, database: str) -> str:
    """构造 mysql+pymysql URI：对密码做 urlencode，避免 @/? 等特殊字符破坏解析。"""
    host = host.strip() or '127.0.0.1'
    port = str(int(port)) if str(port).strip().isdigit() else '3306'
    user = user.strip() or 'root'
    password = password or ''
    database = database.strip() or 'campus_bridge'
    return (
        f'mysql+pymysql://{urllib.parse.quote_plus(user)}'
        f':{urllib.parse.quote_plus(password)}'
        f'@{host}:{port}/{urllib.parse.quote_plus(database)}'
        f'?charset=utf8mb4'
    )


class Config:
    """基础配置（仅 MySQL 单模式）"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # 路径常量（供其它模块复用）
    BASE_DIR = BASE_DIR
    DATABASE_DIR = DATABASE_DIR

    # —— 数据库：强制 MySQL ——
    # 兼容旧 .env 的 MYSQL_* 四键（绝大多数部署已经填过）；
    # 新 .env.example 额外提供 MYSQL_MASTER_* 命名（更语义化，主从演示时一眼看清），
    # 若填了 MYSQL_MASTER_* 则优先，否则回退到 MYSQL_*。
    mysql_user = os.getenv('MYSQL_MASTER_USER') or os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_MASTER_PASSWORD') or os.getenv('MYSQL_PASSWORD', '')
    mysql_host = os.getenv('MYSQL_MASTER_HOST') or os.getenv('MYSQL_HOST', '127.0.0.1')
    mysql_port = os.getenv('MYSQL_MASTER_PORT') or os.getenv('MYSQL_PORT', '3306')
    mysql_db = os.getenv('MYSQL_MASTER_DATABASE') or os.getenv('MYSQL_DATABASE', 'campus_bridge')

    MYSQL_MASTER_URI = _build_mysql_uri(
        host=mysql_host, port=mysql_port,
        user=mysql_user, password=mysql_password,
        database=mysql_db,
    )

    # SQLAlchemy 唯一 bind = 主库（Flask 业务永远只走主库）
    SQLALCHEMY_DATABASE_URI = MYSQL_MASTER_URI

    # 启动期强校验：主库必须能连上；失败直接抛，不做任何降级
    try:
        import sqlalchemy
        _engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URI)
        with _engine.connect() as _conn:
            _conn.execute(sqlalchemy.text('SELECT 1'))
        _engine.dispose()
    except Exception as exc:
        raise RuntimeError(
            'MySQL 主库连接失败（已禁用 SQLite 降级）。'
            '请检查 .env 的 MYSQL_MASTER_HOST/PORT/USER/PASSWORD/DATABASE 或兼容旧键 MYSQL_*。'
            f' 原始错误: {exc.__class__.__name__}'
        ) from exc

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # 文件上传
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '50')) * 1024 * 1024
    UPLOAD_FOLDER = UPLOADS_DIR

    # 腾讯云 COS（可选）
    COS_SECRET_ID = os.getenv('COS_SECRET_ID', '')
    COS_SECRET_KEY = os.getenv('COS_SECRET_KEY', '')
    COS_REGION = os.getenv('COS_REGION', 'ap-guangzhou')
    COS_BUCKET = os.getenv('COS_BUCKET', '')

    # DeepSeek AI（可选，用于论坛摘要 + 内容深度审核；不填自动降级为仅本地审核词）
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')

    # 分页
    ITEMS_PER_PAGE = 12
