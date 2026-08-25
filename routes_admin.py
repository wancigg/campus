"""管理员后台路由"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from decorators import admin_required
from models import User, Material, Post, ForumCategory, Textbook, Notification

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.before_request
@login_required
@admin_required
def before_request():
    pass


@admin_bp.route('/')
def dashboard():
    user_count = User.query.count()
    material_count = Material.query.count()
    post_count = Post.query.count()
    textbook_count = Textbook.query.count()
    return render_template('admin_dashboard.html',
                           user_count=user_count,
                           material_count=material_count,
                           post_count=post_count,
                           textbook_count=textbook_count)


@admin_bp.route('/users')
def users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin_dashboard.html', users=pagination.items,
                           pagination=pagination, tab='users')


@admin_bp.route('/users/<int:id>/role', methods=['POST'])
def toggle_role(id):
    user = User.query.get_or_404(id)
    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()
    flash(f'已更新 {user.username} 的角色为 {user.role}。', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/materials')
def materials():
    page = request.args.get('page', 1, type=int)
    pagination = Material.query.order_by(Material.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin_dashboard.html', materials=pagination.items,
                           pagination=pagination, tab='materials')


@admin_bp.route('/materials/<int:id>/delete', methods=['POST'])
def delete_material(id):
    material = Material.query.get_or_404(id)
    db.session.delete(material)
    db.session.commit()
    flash('资料已删除。', 'info')
    return redirect(url_for('admin.materials'))


@admin_bp.route('/posts')
def posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin_dashboard.html', posts=pagination.items,
                           pagination=pagination, tab='posts')


@admin_bp.route('/posts/<int:id>/delete', methods=['POST'])
def delete_post(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash('帖子已删除。', 'info')
    return redirect(url_for('admin.posts'))


@admin_bp.route('/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        if name:
            cat = ForumCategory(name=name, description=description)
            db.session.add(cat)
            db.session.commit()
            flash('分区已创建。', 'success')
        return redirect(url_for('admin.categories'))
    cats = ForumCategory.query.order_by(ForumCategory.sort_order).all()
    return render_template('admin_dashboard.html', categories=cats, tab='categories')


@admin_bp.route('/textbooks')
def textbooks():
    page = request.args.get('page', 1, type=int)
    pagination = Textbook.query.order_by(Textbook.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin_dashboard.html', textbooks=pagination.items,
                           pagination=pagination, tab='textbooks')


@admin_bp.route('/textbooks/<int:id>/delete', methods=['POST'])
def delete_textbook(id):
    textbook = Textbook.query.get_or_404(id)
    db.session.delete(textbook)
    db.session.commit()
    flash('闲置物品已删除。', 'info')
    return redirect(url_for('admin.textbooks'))


# ============ 内容审核队列（三级风控人工审核页） ============

@admin_bp.route('/moderation')
def moderation_queue():
    """待审核列表：3 类 is_approved=False 的内容，按 created_at 倒序"""
    pending_posts = (Post.query.filter_by(is_approved=False)
                     .order_by(Post.created_at.desc()).all())
    pending_materials = (Material.query.filter_by(is_approved=False)
                         .order_by(Material.created_at.desc()).all())
    pending_textbooks = (Textbook.query.filter_by(is_approved=False)
                         .order_by(Textbook.created_at.desc()).all())
    return render_template(
        'admin_dashboard.html',
        tab='moderation',
        pending_posts=pending_posts,
        pending_materials=pending_materials,
        pending_textbooks=pending_textbooks,
        pending_total=len(pending_posts) + len(pending_materials) + len(pending_textbooks),
    )


# 发布类型 → (模型类, 通过时补发积分, 详情链接, 中文名称)
_MOD_META = {
    'post':     (Post, 5, 'forum.post', '帖子'),
    'material': (Material, 5, 'materials.detail', '资料'),
    'textbook': (Textbook, 3, 'textbook.detail', '闲置物品'),
}


@admin_bp.route('/moderation/<string:type>/<int:id>/approve', methods=['POST'])
def moderation_approve(type, id):
    """通过审核：is_approved=True + 补发积分 + 发系统消息通知作者"""
    if type not in _MOD_META:
        flash('未知的内容类型。', 'error')
        return redirect(url_for('admin.moderation_queue'))
    Model, delta, endpoint, cn = _MOD_META[type]
    obj = Model.query.get_or_404(id)
    if obj.is_approved:
        flash('该内容已审核通过，无需重复操作。', 'info')
        return redirect(url_for('admin.moderation_queue'))

    obj.is_approved = True
    obj.moderation_note = ''  # 通过后清空之前的人工审核备注

    # 补发积分（按模型对应：帖子/资料 +5，二手 +3）
    author = None
    if isinstance(obj, Post):
        author = obj.user if hasattr(obj, 'user') else User.query.get(obj.user_id)
    elif isinstance(obj, Material):
        author = obj.uploader if hasattr(obj, 'uploader') else User.query.get(obj.user_id)
    elif isinstance(obj, Textbook):
        author = obj.seller if hasattr(obj, 'seller') else User.query.get(obj.user_id)

    if author:
        author.add_points(delta)

    db.session.commit()

    # 发系统消息通知作者
    if author:
        link = url_for(endpoint, id=obj.id)
        notif = Notification(
            user_id=author.id,
            type='system',
            title=f'✅ 你的{cn}《{obj.title}》审核通过',
            content=(
                f'管理员审核通过了你的{cn}《{obj.title}》，'
                f'已补发 +{delta} 积分，现在用户可以正常看到该内容了。'
            ),
            link=link,
        )
        db.session.add(notif)
        db.session.commit()

    flash(f'{cn}《{obj.title}》审核通过，作者 {author.username if author else "未知"} 已补发 +{delta} 积分。', 'success')
    return redirect(url_for('admin.moderation_queue'))


@admin_bp.route('/moderation/<string:type>/<int:id>/reject', methods=['POST'])
def moderation_reject(type, id):
    """驳回：保留 is_approved=False（不再展示），写驳回原因 + 系统消息通知作者"""
    if type not in _MOD_META:
        flash('未知的内容类型。', 'error')
        return redirect(url_for('admin.moderation_queue'))
    Model, delta, endpoint, cn = _MOD_META[type]
    obj = Model.query.get_or_404(id)
    reason = (request.form.get('reason', '') or '内容不符合社区规范').strip()[:500]

    obj.moderation_note = reason
    obj.is_approved = False
    db.session.commit()

    # 发系统消息通知作者
    author = None
    if isinstance(obj, Post):
        author = obj.user if hasattr(obj, 'user') else User.query.get(obj.user_id)
    elif isinstance(obj, Material):
        author = obj.uploader if hasattr(obj, 'uploader') else User.query.get(obj.user_id)
    elif isinstance(obj, Textbook):
        author = obj.seller if hasattr(obj, 'seller') else User.query.get(obj.user_id)

    if author:
        notif = Notification(
            user_id=author.id,
            type='system',
            title=f'❌ 你的{cn}《{obj.title}》未通过审核',
            content=(
                f'管理员驳回了你的{cn}《{obj.title}》，驳回原因：{reason}。\n'
                f'如有疑问请联系管理员申诉。'
            ),
            link=url_for(endpoint, id=obj.id),
        )
        db.session.add(notif)
        db.session.commit()

    flash(f'{cn}《{obj.title}》已驳回，作者已收到通知。', 'warning')
    return redirect(url_for('admin.moderation_queue'))
