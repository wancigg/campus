"""论坛路由"""

import json
import os
import re
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import ForumCategory, Post, Comment, PostLike, PostFavorite, PostImage, Notification
from forms import validate_title, validate_content, allowed_image_file

try:
    import requests as _requests
except ImportError:
    _requests = None

forum_bp = Blueprint('forum', __name__, url_prefix='/forum')


@forum_bp.route('/')
def index():
    categories = ForumCategory.query.order_by(ForumCategory.sort_order).all()
    return render_template('forum_index.html', categories=categories)


@forum_bp.route('/category/<int:cat_id>')
def category(cat_id):
    cat = ForumCategory.query.get_or_404(cat_id)
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('q', '').strip()
    query = Post.query.filter_by(category_id=cat_id)
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
    post.views += 1
    db.session.commit()
    user_liked = False
    user_favorited = False
    if current_user.is_authenticated:
        user_liked = PostLike.query.filter_by(
            post_id=id, user_id=current_user.id).first() is not None
        user_favorited = PostFavorite.query.filter_by(
            post_id=id, user_id=current_user.id).first() is not None
    return render_template('forum_post.html', post=post,
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
    comment = Comment(content=content, user_id=current_user.id, post_id=id)
    db.session.add(comment)
    current_user.add_points(2)  # 评论奖励：+2
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
        post = Post(title=title, content=content,
                    user_id=current_user.id, category_id=category_id)
        db.session.add(post)
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
