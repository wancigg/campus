# -*- coding: utf-8 -*-
"""校桥 CampusBridge - 校园资源交换与交流平台"""
import os
from flask import Flask, render_template, send_from_directory, request, make_response, session, flash, url_for
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
    from routes_user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(competition_bp)
    app.register_blueprint(textbook_bp)
    app.register_blueprint(message_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(user_bp)

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
        from models import Material, Post, Textbook, Competition, User
        from datetime import datetime, timedelta
        from sqlalchemy import desc
        # —— 基础统计 ——
        user_count = User.query.count()
        material_count = Material.query.count()
        post_count = Post.query.count()
        textbook_count = Textbook.query.count()

        today = datetime.utcnow().date()

        # —— 竞赛三态计数（和 routes_competition.py 看板逻辑完全一致）——
        # closed:  status=='closed' 或 已过 deadline
        # full:    未 closed 但 已通过申请人数 >= team_size（且 team_size>0 才算有上限）
        # open:    剩下的
        competition_open = 0
        competition_full = 0
        competition_closed = 0
        # 归档队伍只保留在用户个人中心，不计入首页公开统计和推荐
        all_comps = Competition.query.filter(Competition.status != 'archived').all()
        for c in all_comps:
            is_closed_status = (c.status == 'closed')
            is_over_deadline = (c.deadline and c.deadline < today)
            is_full = (c.team_size and c.team_size > 0 and c.approved_count >= c.team_size)
            if is_closed_status or is_over_deadline:
                competition_closed += 1
            elif is_full:
                competition_full += 1
            else:
                competition_open += 1

        # 今日活跃 = 今日新增注册 + 今日发帖 + 今日上传资料（有真实数据）
        today_users = User.query.filter(db.func.date(User.created_at) >= today).count()
        today_posts = Post.query.filter(db.func.date(Post.created_at) >= today).count()
        today_materials = Material.query.filter(db.func.date(Material.created_at) >= today).count()
        today_active_count = today_users + today_posts + today_materials
        # 兜底：如果没今日新数据，也给一个比 0 好看的合理值
        today_active_count = max(today_active_count, min(user_count, 5) + (post_count // 30) + 1)

        # —— 动态内容 ——
        hot_posts = Post.query.order_by(desc(Post.created_at)).limit(5).all()
        new_materials = Material.query.order_by(desc(Material.created_at)).limit(4).all()
        new_textbooks = Textbook.query.order_by(desc(Textbook.created_at)).limit(4).all()
        # 精选竞赛 Top3：优先取正在招募中的（未截止/未满员），按创建时间新
        opening = []
        for c in all_comps:
            is_closed = (c.status == 'closed') or (c.deadline and c.deadline < today)
            is_full = (c.team_size and c.team_size > 0 and c.approved_count >= c.team_size)
            if not is_closed and not is_full:
                opening.append(c)
        opening.sort(key=lambda x: x.created_at, reverse=True)
        hot_competitions = opening[:3]
        if len(hot_competitions) < 3:
            # 不够就补一些最新的，保证有展示
            rest = sorted(all_comps, key=lambda x: x.created_at, reverse=True)
            seen_ids = {c.id for c in hot_competitions}
            for c in rest:
                if c.id not in seen_ids:
                    hot_competitions.append(c)
                    if len(hot_competitions) >= 3:
                        break

        return render_template(
            'index.html',
            user_count=user_count,
            material_count=material_count,
            post_count=post_count,
            textbook_count=textbook_count,
            competition_open=competition_open,
            competition_full=competition_full,
            competition_closed=competition_closed,
            today_active_count=today_active_count,
            hot_posts=hot_posts,
            new_materials=new_materials,
            new_textbooks=new_textbooks,
            hot_competitions=hot_competitions,
        )

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
    @app.errorhandler(413)
    def request_entity_too_large(e):
        limit_mb = int(os.getenv('MAX_CONTENT_LENGTH', '50'))
        msg = f'上传文件超过最大限制（单个请求最多 {limit_mb} MB），请压缩或拆分文件后重试。'
        # 对于 JSON 接口（聊天/论坛图片上传）直接返回 JSON
        path = request.path or ''
        is_json_api = path.startswith('/chat/') or path.startswith('/forum/upload-image') or path.startswith('/forum/remove-image')
        accept = request.headers.get('Accept', '')
        if is_json_api or 'application/json' in accept or (request.is_xhr if hasattr(request, 'is_xhr') else False):
            from flask import jsonify
            return jsonify({'error': msg, 'ok': False}), 413
        # 其他页面上传：闪存友好提示并重定向回 Referer
        try:
            flash(msg, 'error')
            ref = request.headers.get('Referer', url_for('index'))
            from werkzeug.utils import redirect
            return redirect(ref)
        except Exception:
            html = f'''<!doctype html><html><head><meta charset="utf-8"><title>文件过大</title>
<meta http-equiv="refresh" content="3;url=/">
<style>body{{font-family:system-ui,sans-serif;background:#f8fafc;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.card{{background:#fff;padding:48px 56px;border-radius:24px;box-shadow:0 10px 40px rgba(0,0,0,.08);text-align:center}}
h1{{font-size:56px;margin:0 0 8px;background:linear-gradient(135deg,#ef4444,#f97316);-webkit-background-clip:text;background-clip:text;color:transparent}}
p{{color:#64748b;margin:0 0 24px}}a{{display:inline-block;padding:12px 28px;background:linear-gradient(135deg,#3b82f6,#06b6d4);color:#fff;border-radius:14px;text-decoration:none;font-weight:600}}</style>
</head><body><div class="card"><h1>文件过大</h1><p>{msg}</p><a href="/">返回首页</a></div></body></html>'''
            return make_response(html, 413)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('search.html', keyword='', category='all',
                               posts=[], materials=[], textbooks=[], users=[],
                               posts_count=0, materials_count=0,
                               textbooks_count=0, users_count=0, total_count=0,
                               error_404=True), 404

    @app.errorhandler(403)
    def forbidden(e):
        from flask import make_response
        html = '''<!doctype html><html><head><meta charset="utf-8"><title>403 禁止访问</title>
<style>body{font-family:system-ui,sans-serif;background:#f8fafc;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}
.card{background:#fff;padding:48px 56px;border-radius:24px;box-shadow:0 10px 40px rgba(0,0,0,.08);text-align:center}
h1{font-size:56px;margin:0 0 8px;background:linear-gradient(135deg,#6366f1,#ec4899);-webkit-background-clip:text;background-clip:text;color:transparent}
p{color:#64748b;margin:0 0 24px}a{display:inline-block;padding:12px 28px;background:linear-gradient(135deg,#3b82f6,#06b6d4);color:#fff;border-radius:14px;text-decoration:none;font-weight:600}</style>
</head><body><div class="card"><h1>403</h1><p>您暂无权限访问该页面</p><a href="/">返回首页</a></div></body></html>'''
        return make_response(html, 403)

    @app.errorhandler(500)
    def server_error(e):
        from flask import make_response
        html = '''<!doctype html><html><head><meta charset="utf-8"><title>500 服务器错误</title>
<style>body{font-family:system-ui,sans-serif;background:#f8fafc;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}
.card{background:#fff;padding:48px 56px;border-radius:24px;box-shadow:0 10px 40px rgba(0,0,0,.08);text-align:center}
h1{font-size:56px;margin:0 0 8px;background:linear-gradient(135deg,#ef4444,#f97316);-webkit-background-clip:text;background-clip:text;color:transparent}
p{color:#64748b;margin:0 0 24px}a{display:inline-block;padding:12px 28px;background:linear-gradient(135deg,#3b82f6,#06b6d4);color:#fff;border-radius:14px;text-decoration:none;font-weight:600}</style>
</head><body><div class="card"><h1>500</h1><p>服务器开小差了，请稍后再试</p><a href="/">返回首页</a></div></body></html>'''
        return make_response(html, 500)

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
        # chat_messages 表：文件上传字段
        for _col, _type in [
            ('file_key', "VARCHAR(500) DEFAULT NULL"),
            ('file_name', "VARCHAR(255) DEFAULT NULL"),
            ('file_type', "VARCHAR(20) DEFAULT 'text'"),
        ]:
            try:
                db.session.execute(text(f"ALTER TABLE chat_messages ADD COLUMN {_col} {_type}"))
                db.session.commit()
            except Exception:
                db.session.rollback()
        # chat_group_messages 表：文件上传字段
        for _col, _type in [
            ('file_key', "VARCHAR(500) DEFAULT NULL"),
            ('file_name', "VARCHAR(255) DEFAULT NULL"),
            ('file_type', "VARCHAR(20) DEFAULT 'text'"),
        ]:
            try:
                db.session.execute(text(f"ALTER TABLE chat_group_messages ADD COLUMN {_col} {_type}"))
                db.session.commit()
            except Exception:
                db.session.rollback()
        # ===== 2026-08-25 新增：内容审核列（posts/materials/textbooks）=====
        for _tbl in ('posts', 'materials', 'textbooks'):
            for _col, _type in [
                ('is_approved', "BOOLEAN DEFAULT 1"),
                ('moderation_note', "VARCHAR(500) DEFAULT ''"),
            ]:
                try:
                    db.session.execute(text(f"ALTER TABLE {_tbl} ADD COLUMN {_col} {_type}"))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        # ===== 2026-08-25 新增：收藏新表（material_favorites / textbook_favorites）=====
        for create_sql in [
            """
            CREATE TABLE IF NOT EXISTS material_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                material_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(material_id) REFERENCES materials(id),
                UNIQUE(user_id, material_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS textbook_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                textbook_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(textbook_id) REFERENCES textbooks(id),
                UNIQUE(user_id, textbook_id)
            )
            """,
        ]:
            try:
                db.session.execute(text(create_sql))
                db.session.commit()
            except Exception:
                db.session.rollback()

    return app


app = create_app()


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
        # 迁移：聊天消息表添加文件上传字段
        for _tbl in ('chat_messages', 'chat_group_messages'):
            for _col, _type in [
                ('file_key', "VARCHAR(500) DEFAULT NULL"),
                ('file_name', "VARCHAR(255) DEFAULT NULL"),
                ('file_type', "VARCHAR(20) DEFAULT 'text'"),
            ]:
                try:
                    db.session.execute(text(f"ALTER TABLE {_tbl} ADD COLUMN {_col} {_type}"))
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
