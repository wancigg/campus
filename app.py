"""校桥 CampusBridge - 校园资源交换与交流平台"""
import os
from flask import Flask, render_template, send_from_directory
from config import Config
from extensions import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)

    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 注册蓝图
    from routes_auth import auth_bp
    from routes_materials import materials_bp
    from routes_forum import forum_bp
    from routes_competition import competition_bp
    from routes_textbook import textbook_bp
    from routes_message import message_bp
    from routes_admin import admin_bp
    from routes_social import social_bp
    from routes_chat import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(competition_bp)
    app.register_blueprint(textbook_bp)
    app.register_blueprint(message_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(chat_bp)

    # 用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # 注入通知数量到模板上下文
    @app.context_processor
    def inject_notification_count():
        from flask_login import current_user
        if current_user.is_authenticated:
            from models import Notification
            count = Notification.query.filter_by(
                user_id=current_user.id, is_read=False).count()
            return {'unread_count': count}
        return {'unread_count': 0}

    # 首页路由
    @app.route('/')
    def index():
        from models import Material, Post, Textbook, Competition
        material_count = Material.query.count()
        post_count = Post.query.count()
        textbook_count = Textbook.query.count()
        competition_count = Competition.query.filter_by(status='open').count()
        return render_template('index.html',
                               material_count=material_count,
                               post_count=post_count,
                               textbook_count=textbook_count,
                               competition_count=competition_count)

    # 本地文件服务（降级方案）
    @app.route('/uploads/<path:key>')
    def uploaded_file(key):
        return send_from_directory(app.config['UPLOAD_FOLDER'], key)

    # 错误处理
    @app.errorhandler(404)
    def not_found(e):
        return render_template('index.html', error_404=True), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('index.html', error_403=True), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template('index.html', error_500=True), 500

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        # 迁移：为 materials 表添加 views 列（SQLite 需手动执行）
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE materials ADD COLUMN views INTEGER DEFAULT 0"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        # 迁移：创建 friend_requests 表（好友关系）
        try:
            from sqlalchemy import text
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS friend_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    message VARCHAR(200),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(sender_id) REFERENCES users(id),
                    FOREIGN KEY(receiver_id) REFERENCES users(id),
                    UNIQUE(sender_id, receiver_id)
                )
            """))
            db.session.commit()
        except Exception:
            db.session.rollback()
        # 迁移：创建聊天相关表
        try:
            from sqlalchemy import text
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(sender_id) REFERENCES users(id),
                    FOREIGN KEY(receiver_id) REFERENCES users(id)
                )
            """))
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    created_by INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(created_by) REFERENCES users(id)
                )
            """))
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_group_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(group_id) REFERENCES chat_groups(id),
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    UNIQUE(group_id, user_id)
                )
            """))
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_group_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    sender_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(group_id) REFERENCES chat_groups(id),
                    FOREIGN KEY(sender_id) REFERENCES users(id)
                )
            """))
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS post_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    sort_order INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(post_id) REFERENCES posts(id)
                )
            """))
            db.session.commit()
        except Exception:
            db.session.rollback()
        # 迁移：为 textbooks 表添加新增列（SQLite 需手动执行）
        _textbook_migrations = [
            ('category', "VARCHAR(50) DEFAULT ''"),
            ('condition', "VARCHAR(50) DEFAULT ''"),
            ('description_images', "TEXT DEFAULT ''"),
            ('trade_status', "VARCHAR(50) DEFAULT 'available'"),
        ]
        for _col, _type in _textbook_migrations:
            try:
                db.session.execute(text(f"ALTER TABLE textbooks ADD COLUMN {_col} {_type}"))
                db.session.commit()
            except Exception:
                db.session.rollback()
        # 初始化默认数据
        from models import User, ForumCategory
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@campusbridge.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
        if ForumCategory.query.count() == 0:
            categories = [
                ForumCategory(name='学习交流', description='课程学习、学术讨论', icon='📚', sort_order=1),
                ForumCategory(name='校园生活', description='校园活动、日常生活分享', icon='🏫', sort_order=2),
                ForumCategory(name='技术讨论', description='编程、设计、技术分享', icon='💻', sort_order=3),
                ForumCategory(name='求职升学', description='实习、考研、求职经验', icon='🎓', sort_order=4),
                ForumCategory(name='闲聊灌水', description='轻松话题、趣事分享', icon='💬', sort_order=5),
            ]
            db.session.add_all(categories)
        db.session.commit()
    app.run(debug=True, host='0.0.0.0', port=5000)
