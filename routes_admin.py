"""管理员后台路由"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from decorators import admin_required
from models import User, Material, Post, ForumCategory, Textbook

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
