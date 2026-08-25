"""论坛路由"""

import json
import os
import re
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, abort
from flask_login import login_required, current_user
from extensions import db
from models import ForumCategory, Post, Comment, PostLike, PostFavorite, PostImage, Notification
from forms import validate_title, validate_content, allowed_image_file
from moderation import moderate_text, moderate_image_bytes

try:
    import requests as _requests
except ImportError:
    _requests = None

forum_bp = Blueprint('forum', __name__, url_prefix='/forum')


def _visible_posts_q():
    """
    返回可见帖子的 SQLAlchemy 过滤条件：
    - 已审核通过（is_approved=True）OR
    - 当前登录用户就是作者 OR
    - 当前用户是管理员
    匿名用户：仅能看见已通过（is_approved=True）
    """
    from sqlalchemy import or_, and_
    base = Post.is_approved.is_(True)
    if not current_user.is_authenticated:
        return base
    if current_user.is_admin():
        return or_(base, Post.is_approved.is_(False))  # 管理员：全部可见
    # 普通登录用户：可见通过的 + 自己的（不论审核状态）
    return or_(base, and_(Post.is_approved.is_(False), Post.user_id == current_user.id))


@forum_bp.route('/')
def index():
    from datetime import datetime
    from sqlalchemy import func
    from models import User

    categories = ForumCategory.query.order_by(ForumCategory.sort_order).all()

    # ===== A方案：顶部统计小卡数据 =====
    total_posts = Post.query.filter(_visible_posts_q()).count()
    total_comments = Comment.query.count()
    today_start = datetime.utcnow().date()
    today_posts = Post.query.filter(
        db.func.date(Post.created_at) == today_start
    ).filter(_visible_posts_q()).count()
    # 热门板块Top3（按帖子数）
    cat_stats = db.session.query(
        ForumCategory, func.count(Post.id)
    ).outerjoin(Post, db.and_(Post.category_id == ForumCategory.id, _visible_posts_q())
    ).group_by(ForumCategory.id).order_by(func.count(Post.id).desc()).limit(3).all()
    hot_categories = [(c, cnt) for c, cnt in cat_stats]

    # ===== B方案：知乎式最新帖子信息流（跨板块聚合） =====
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('q', '').strip()
    q = Post.query.filter(_visible_posts_q())
    if keyword:
        q = q.filter(Post.title.contains(keyword))
    latest_posts_q = q.options(
        db.joinedload(Post.author), db.joinedload(Post.category),
        db.joinedload(Post.images)
    ).order_by(Post.is_pinned.desc(), Post.created_at.desc())
    # 不取 pagination，直接取 15 条展示
    feed_posts = latest_posts_q.limit(15).all()

    return render_template('forum_index.html',
                           categories=categories,
                           total_posts=total_posts,
                           total_comments=total_comments,
                           today_posts=today_posts,
                           hot_categories=hot_categories,
                           feed_posts=feed_posts,
                           keyword=keyword)


@forum_bp.route('/category/<int:cat_id>')
def category(cat_id):
    cat = ForumCategory.query.get_or_404(cat_id)
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('q', '').strip()
    query = Post.query.filter_by(category_id=cat_id).filter(_visible_posts_q())
    if keyword:
        query = query.filter(Post.title.contains(keyword))
    pagination = query.order_by(Post.is_pinned.desc(), Post.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False)
    return render_template('forum_category.html', category=cat,
                           posts=pagination.items, pagination=pagination,
                           keyword=keyword)


@forum_bp.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    # 非作者非管理员，访问待审核内容 → 403
    if not post.is_approved:
        if not current_user.is_authenticated:
            abort(403)
        if not (current_user.id == post.user_id or current_user.is_admin()):
            abort(403)
    post.views += 1
    db.session.commit()
    # 直接查询评论列表（避免 lazy='dynamic' 问题）
    comments = Comment.query.filter_by(post_id=id).order_by(Comment.created_at).all()
    # 预加载评论作者
    for c in comments:
        _ = c.author  # 触发关系加载
    user_liked = False
    user_favorited = False
    if current_user.is_authenticated:
        user_liked = PostLike.query.filter_by(
            post_id=id, user_id=current_user.id).first() is not None
        user_favorited = PostFavorite.query.filter_by(
            post_id=id, user_id=current_user.id).first() is not None
    return render_template('forum_post.html', post=post,
                           comments=comments,
                           user_liked=user_liked, user_favorited=user_favorited)


@forum_bp.route('/post/<int:id>/comment', methods=['POST'])
@login_required
def comment(id):
    post = Post.query.get_or_404(id)
    content = request.form.get('content', '').strip()
    ok, msg = validate_content(content)
    if not ok:
        flash(msg, 'error')
        return redirect(url_for('forum.post', id=id))

    # ====== 评论内容审核 ======
    check = moderate_text(content, context_type='comment')
    if check['reject']:
        flash(f'评论失败：{check["reason"]}', 'error')
        return redirect(url_for('forum.post', id=id))

    comment = Comment(content=content, user_id=current_user.id, post_id=id)
    db.session.add(comment)
    # 只有审核通过才给评论积分
    if check['level'] == 'pass':
        current_user.add_points(2)
    if post.user_id != current_user.id:
        notif = Notification(
            user_id=post.user_id,
            type='comment',
            title='帖子收到新回复',
            content=f'{current_user.username} 回复了你的帖子《{post.title}》。',
            link=url_for('forum.post', id=id)
        )
        db.session.add(notif)
    db.session.commit()
    flash('回复成功！+2 积分 ✨', 'success')
    return redirect(url_for('forum.post', id=id))


@forum_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id
    if comment.user_id != current_user.id and not current_user.is_admin():
        flash('只有本人或管理员可以删除评论。', 'error')
        return redirect(url_for('forum.post', id=post_id))
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除。', 'success')
    return redirect(url_for('forum.post', id=post_id))


@forum_bp.route('/post/<int:id>/like', methods=['POST'])
@login_required
def like(id):
    post = Post.query.get_or_404(id)
    existing = PostLike.query.filter_by(post_id=id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return {'status': 'unliked', 'count': post.like_count}
    like = PostLike(post_id=id, user_id=current_user.id)
    db.session.add(like)
    if post.user_id != current_user.id:
        # 被点赞的作者 +1 积分
        post.author.add_points(1)
        notif = Notification(
            user_id=post.user_id,
            type='like',
            title='帖子收到点赞',
            content=f'{current_user.username} 赞了你的帖子《{post.title}》。',
            link=url_for('forum.post', id=id)
        )
        db.session.add(notif)
    db.session.commit()
    return {'status': 'liked', 'count': post.like_count}


@forum_bp.route('/post/<int:id>/favorite', methods=['POST'])
@login_required
def favorite(id):
    post = Post.query.get_or_404(id)
    existing = PostFavorite.query.filter_by(post_id=id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return {'status': 'unfavorited'}
    fav = PostFavorite(post_id=id, user_id=current_user.id)
    db.session.add(fav)
    db.session.commit()
    return {'status': 'favorited'}


@forum_bp.route('/post/<int:id>/ai-summary')
@login_required
def ai_summary(id):
    """AJAX：AI 摘要帖子（调用 DeepSeek Chat API）"""
    post = Post.query.get_or_404(id)
    api_key = os.getenv('DEEPSEEK_API_KEY', '').strip()

    if not api_key:
        return jsonify({'error': '管理员尚未配置 DEEPSEEK_API_KEY，AI 摘要暂不可用。'}), 503
    if _requests is None:
        return jsonify({'error': '缺少依赖 requests，请先 pip install requests。'}), 503

    title = (post.title or '').strip()
    content = (post.content or '').strip()
    if len(title) + len(content) < 15:
        return jsonify({'error': '帖子内容太短，无法生成摘要。'}), 400

    text = f'标题：{title}\n\n正文：{content[:4000]}'
    system_prompt = (
        '你是中文校园论坛 AI 助手，负责把用户提供的论坛帖子整理成结构化摘要。'
        '请严格按 JSON 输出（不要任何 markdown 代码块标记、不要额外文字），字段如下：\n'
        '{"summary": "200 字以内的客观摘要，不要加入主观评价", '
        '"key_points": ["第 1 点（不超过 40 字）", "第 2 点", "第 3 点"], '
        '"tags": ["标签1", "标签2", "标签3"]}。\n'
        'tags 从：学习交流、校园生活、技术讨论、求职升学、闲聊灌水、'
        '课程、考研、实习、编程、宿舍、社团、竞赛、恋爱、美食、运动、吐槽 中选 2-4 个，'
        '如果内容明确属于其中某个类别就选，不要生造。'
    )

    try:
        resp = _requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            timeout=30,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'deepseek-chat',
                'temperature': 0.3,
                'max_tokens': 700,
                'response_format': {'type': 'json_object'},
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': text},
                ],
            },
        )
    except Exception as e:
        return jsonify({'error': f'AI 服务连接失败：{str(e)[:60]}'}), 502

    if resp.status_code != 200:
        snippet = resp.text[:200]
        return jsonify({'error': f'AI 服务返回错误（{resp.status_code}）：{snippet}'}), 502

    try:
        data = resp.json()
        raw = data['choices'][0]['message']['content'].strip()
    except Exception:
        return jsonify({'error': 'AI 返回格式异常，请稍后重试。'}), 502

    # 去掉可能的 ```json ... ``` 包裹
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'\s*```$', '', raw, flags=re.IGNORECASE)
    try:
        result = json.loads(raw)
    except Exception:
        return jsonify({
            'summary': raw,
            'key_points': [],
            'tags': [],
        })

    # 字段兜底
    summary = (result.get('summary') or '').strip() or '（无摘要）'
    key_points = result.get('key_points') or []
    if not isinstance(key_points, list):
        key_points = []
    tags = result.get('tags') or []
    if not isinstance(tags, list):
        tags = []

    return jsonify({
        'summary': summary[:500],
        'key_points': [str(p).strip()[:100] for p in key_points if str(p).strip()][:5],
        'tags': [str(t).strip()[:20] for t in tags if str(t).strip()][:6],
    })


@forum_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    categories = ForumCategory.query.order_by(ForumCategory.sort_order).all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category_id = request.form.get('category_id', type=int)
        content = request.form.get('content', '').strip()
        ok, msg = validate_title(title)
        if not ok:
            flash(msg, 'error')
            return render_template('forum_edit.html', categories=categories)
        ok, msg = validate_content(content)
        if not ok:
            flash(msg, 'error')
            return render_template('forum_edit.html', categories=categories)

        # ====== 内容审核（发帖）======
        check = moderate_text(f"{title}\n{content}", context_type='forum_post')
        if check['reject']:
            # BLOCK：严重违规词，直接拦截，不加库
            flash(f"发帖失败：{check['reason']}", 'error')
            return render_template('forum_edit.html', categories=categories)

        post = Post(title=title, content=content,
                    user_id=current_user.id, category_id=category_id)
        if check['level'] == 'warn':
            # WARN：进人工审核队列
            post.is_approved = False
            post.moderation_note = check['reason'][:500]
        db.session.add(post)
        # 积分：只有明确通过才给奖励；待审核等管理员通过后补发
        if check['level'] == 'pass':
            current_user.add_points(5)  # 发帖奖励：+5
        db.session.flush()  # 获取 post.id

        # 处理图片：从隐藏字段获取已上传的图片文件名列表
        image_filenames = request.form.get('images', '').strip()
        if image_filenames:
            for i, filename in enumerate(image_filenames.split(',')):
                filename = filename.strip()
                if filename:
                    db.session.add(PostImage(
                        post_id=post.id, filename=filename, sort_order=i
                    ))

        db.session.commit()
        if check['level'] == 'warn':
            flash('发帖已提交，内容正在人工审核中（一般 24 小时内处理），审核通过后发布并奖励积分。', 'warning')
        else:
            flash('发帖成功！+5 积分 🎉', 'success')
        return redirect(url_for('forum.post', id=post.id))
    return render_template('forum_edit.html', categories=categories)


@forum_bp.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    """AJAX 上传帖子图片，返回文件名供前端暂存"""
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': '请选择图片'}), 400
    if not allowed_image_file(file.filename):
        return jsonify({'error': '仅支持 jpg/jpeg/png/gif/webp 格式'}), 400

    # ====== 图片审核 ======
    try:
        blob = file.read()
        file.seek(0)
    except Exception:
        return jsonify({'error': '读取图片失败'}), 400
    img_check = moderate_image_bytes(blob, filename=file.filename)
    if img_check['reject']:
        return jsonify({'error': img_check['reason']}), 400

    # 生成唯一文件名
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f'forum_{uuid.uuid4().hex}.{ext}'
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
    file.save(upload_path)

    return jsonify({'ok': True, 'filename': unique_name})


@forum_bp.route('/remove-image', methods=['POST'])
@login_required
def remove_image():
    """AJAX 删除上传的临时图片"""
    filename = (request.json or {}).get('filename', '').strip()
    if not filename or not filename.startswith('forum_'):
        return jsonify({'error': '非法文件名'}), 400
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return jsonify({'ok': True})


@forum_bp.route('/post/<int:id>/delete', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if post.user_id != current_user.id:
        flash('只有作者可以删除该帖子。', 'error')
        return redirect(url_for('forum.post', id=id))
    # 删除图片文件
    for img in post.images.all():
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], img.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    PostImage.query.filter_by(post_id=id).delete()
    Comment.query.filter_by(post_id=id).delete()
    PostLike.query.filter_by(post_id=id).delete()
    PostFavorite.query.filter_by(post_id=id).delete()
    db.session.delete(post)
    db.session.commit()
    flash('帖子已删除。', 'success')
    return redirect(url_for('forum.category', cat_id=post.category_id))
