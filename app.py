"""校桥 CampusBridge - 校园资源交换与交流平台"""
import os
from flask import Flask, render_template, send_from_directory, request
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

    # 全站聚合搜索
    @app.route('/search')
    def search():
        from models import Post, Material, Textbook, User
        from sqlalchemy import or_

        keyword = (request.args.get('q') or '').strip()
        category = (request.args.get('type') or 'all').strip()
        page = request.args.get('page', 1, type=int)

        posts = []
        materials = []
        textbooks = []
        users = []
        posts_count = 0
        materials_count = 0
        textbooks_count = 0
        users_count = 0

        def _build_kw_filter(*columns):
            """根据关键字生成 OR LIKE 过滤，空关键字则返回 True（不过滤）"""
            if not keyword:
                return True
            return or_(*[col.contains(keyword) for col in columns])

        # 1. 论坛帖子：标题/内容匹配（空关键字返回最近 8 条）
        if category in ('all', 'posts'):
            post_query = Post.query.filter(_build_kw_filter(
                Post.title, Post.content,
            ))
            posts_count = post_query.count()
            posts = post_query.order_by(Post.created_at.desc()).limit(8).all()

        # 2. 学习资料：标题/描述/分类（description 可能为 NULL，兜底成空串）
        if category in ('all', 'materials'):
            mat_filter = _build_kw_filter(
                Material.title, db.func.coalesce(Material.description, ''), Material.category,
            )
            mat_query = Material.query.filter(mat_filter)
            materials_count = mat_query.count()
            materials = mat_query.order_by(Material.created_at.desc()).limit(6).all()

        # 3. 二手市场：标题/描述/分类/品牌/出版社
        if category in ('all', 'textbooks'):
            tb_filter = _build_kw_filter(
                Textbook.title,
                db.func.coalesce(Textbook.description, ''),
                db.func.coalesce(Textbook.category, ''),
                db.func.coalesce(Textbook.author, ''),
                db.func.coalesce(Textbook.publisher, ''),
            )
            tb_query = Textbook.query.filter(tb_filter)
            textbooks_count = tb_query.count()
            textbooks = tb_query.order_by(Textbook.created_at.desc()).limit(6).all()

        # 4. 校园用户：用户名/简介（User 模型没有 school/major 字段！已修正）
        if category in ('all', 'users'):
            user_filter = _build_kw_filter(
                User.username,
                db.func.coalesce(User.bio, ''),
            )
            user_query = User.query.filter(user_filter)
            users_count = user_query.count()
            users = user_query.order_by(User.points.desc()).limit(6).all()

        total_count = posts_count + materials_count + textbooks_count + users_count

        return render_template(
            'search.html',
            keyword=keyword,
            category=category,
            posts=posts, posts_count=posts_count,
            materials=materials, materials_count=materials_count,
            textbooks=textbooks, textbooks_count=textbooks_count,
            users=users, users_count=users_count,
            total_count=total_count,
        )

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

    # ════════════════════════════════════════════════════════════
    # 自动数据库迁移（兼容 gunicorn 生产部署）
    # ════════════════════════════════════════════════════════════
    with app.app_context():
        from sqlalchemy import text
        try:
            db.create_all()
        except Exception:
            pass
        # users 表：points 积分列（等级体系）
        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        # materials 表：views 浏览量
        try:
            db.session.execute(text("ALTER TABLE materials ADD COLUMN views INTEGER DEFAULT 0"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        # textbooks 表：扩展列
        for _col, _type in [
            ('category', "VARCHAR(50) DEFAULT ''"),
            ('condition', "VARCHAR(50) DEFAULT ''"),
            ('description_images', "TEXT DEFAULT ''"),
            ('trade_status', "VARCHAR(50) DEFAULT 'available'"),
        ]:
            try:
                db.session.execute(text(f"ALTER TABLE textbooks ADD COLUMN {_col} {_type}"))
                db.session.commit()
            except Exception:
                db.session.rollback()

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
        # 迁移：为 users 表添加 points 积分列（用户积分/等级体系）
        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0"))
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
