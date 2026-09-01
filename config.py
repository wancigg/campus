"""校桥 CampusBridge 配置"""

import os
import pymysql
from dotenv import load_dotenv

pymysql.install_as_MySQLdb()

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # 数据库配置：MySQL 可用时作为主库，不可用时使用本地 SQLite 暂存
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', '')
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = os.getenv('MYSQL_PORT', '3306')
    mysql_db = os.getenv('MYSQL_DATABASE', 'campus_bridge')
    MYSQL_DATABASE_URI = DATABASE_URL or (
        f'mysql+pymysql://{mysql_user}:{mysql_password}'
        f'@{mysql_host}:{mysql_port}/{mysql_db}'
        f'?charset=utf8mb4'
    )
    SQLITE_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'campus_bridge.db')
    DATABASE_MODE = 'sqlite'
    try:
        import sqlalchemy
        _engine = sqlalchemy.create_engine(MYSQL_DATABASE_URI)
        with _engine.connect() as _conn:
            _conn.execute(sqlalchemy.text('SELECT 1'))
        _engine.dispose()
        SQLALCHEMY_DATABASE_URI = MYSQL_DATABASE_URI
        DATABASE_MODE = 'mysql'
    except Exception:
        SQLALCHEMY_DATABASE_URI = SQLITE_DATABASE_URI
        DATABASE_MODE = 'sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # 文件上传
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '50')) * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

    # 腾讯云 COS（可选）
    COS_SECRET_ID = os.getenv('COS_SECRET_ID', '')
    COS_SECRET_KEY = os.getenv('COS_SECRET_KEY', '')
    COS_REGION = os.getenv('COS_REGION', 'ap-guangzhou')
    COS_BUCKET = os.getenv('COS_BUCKET', '')

    # DeepSeek AI（可选，用于论坛摘要 + 内容深度审核；不填自动降级为仅本地审核词）
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')

    # 分页
    ITEMS_PER_PAGE = 12
