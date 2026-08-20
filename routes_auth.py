"""用户认证路由"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Post, Material, Competition, Textbook
from forms import validate_username, validate_email, validate_password, allowed_image_file

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember'))
            flash('登录成功，欢迎回来！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('用户名或密码错误。', 'error')
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        # 校验
        ok, msg = validate_username(username)
        if not ok:
            flash(msg, 'error')
            return render_template('register.html', username=username, email=email)
        ok, msg = validate_email(email)
        if not ok:
            flash(msg, 'error')
            return render_template('register.html', username=username, email=email)
        ok, msg = validate_password(password)
        if not ok:
            flash(msg, 'error')
            return render_template('register.html', username=username, email=email)
        if password != confirm:
            flash('两次输入的密码不一致。', 'error')
            return render_template('register.html', username=username, email=email)

        if User.query.filter_by(username=username).first():
            flash('用户名已被注册。', 'error')
            return render_template('register.html', username=username, email=email)
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册。', 'error')
            return render_template('register.html', username=username, email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录！', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已安全退出。', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/user/<int:user_id>')
def profile_view(user_id):
    """查看他人公开资料页"""
    user = User.query.get_or_404(user_id)
    from models import Post, Material, Textbook
    tab = request.args.get('tab', 'posts')
    page = request.args.get('page', 1, type=int)
    per_page = 8

    post_count = Post.query.filter_by(user_id=user_id).count()
    material_count = Material.query.filter_by(user_id=user_id).count()
    textbook_count = Textbook.query.filter_by(user_id=user_id).count()
    friend_count = user.get_friend_count()

    items = []
    pagination = None
    if tab == 'posts':
        pagination = Post.query.filter_by(user_id=user_id)\
            .order_by(Post.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        items = pagination.items
    elif tab == 'materials':
        pagination = Material.query.filter_by(user_id=user_id)\
            .order_by(Material.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        items = pagination.items
    elif tab == 'textbooks':
        pagination = Textbook.query.filter_by(user_id=user_id)\
            .order_by(Textbook.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        items = pagination.items

    # 好友关系状态（仅登录用户可查看）
    friend_status = None
    if current_user.is_authenticated and current_user.id != user_id:
        friend_status = current_user.get_friend_request_status(user_id)

    return render_template('user_profile.html',
                           user=user,
                           post_count=post_count,
                           material_count=material_count,
                           textbook_count=textbook_count,
                           friend_count=friend_count,
                           friend_status=friend_status,
                           tab=tab,
                           items=items,
                           pagination=pagination)


@auth_bp.route('/profile')
@login_required
def profile():
    """个人资料页"""
    tab = request.args.get('tab', 'posts')
    page = request.args.get('page', 1, type=int)
    per_page = 8

    # 统计数据
    post_count = Post.query.filter_by(user_id=current_user.id).count()
    material_count = Material.query.filter_by(user_id=current_user.id).count()
    competition_count = Competition.query.filter_by(owner_id=current_user.id).count()
    textbook_count = Textbook.query.filter_by(user_id=current_user.id).count()
    friend_count = current_user.get_friend_count()

    # 按 tab 加载对应内容
    items = []
    pagination = None
    if tab == 'posts':
        pagination = Post.query.filter_by(user_id=current_user.id)\
            .order_by(Post.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        items = pagination.items
    elif tab == 'materials':
        pagination = Material.query.filter_by(user_id=current_user.id)\
            .order_by(Material.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        items = pagination.items
    elif tab == 'competitions':
        pagination = Competition.query.filter_by(owner_id=current_user.id)\
            .order_by(Competition.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        items = pagination.items
    elif tab == 'textbooks':
        pagination = Textbook.query.filter_by(user_id=current_user.id)\
            .order_by(Textbook.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        items = pagination.items

    return render_template('student.html',
                           user=current_user,
                           post_count=post_count,
                           material_count=material_count,
                           competition_count=competition_count,
                           textbook_count=textbook_count,
                           friend_count=friend_count,
                           tab=tab,
                           items=items,
                           pagination=pagination)


@auth_bp.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    """编辑个人资料"""
    bio = request.form.get('bio', '').strip()
    email = request.form.get('email', '').strip()

    if email and email != current_user.email:
        ok, msg = validate_email(email)
        if not ok:
            flash(msg, 'error')
            return redirect(url_for('auth.profile'))
        if User.query.filter(User.email == email, User.id != current_user.id).first():
            flash('该邮箱已被其他用户使用。', 'error')
            return redirect(url_for('auth.profile'))
        current_user.email = email

    if len(bio) > 500:
        flash('个人简介不能超过500字。', 'error')
        return redirect(url_for('auth.profile'))

    current_user.bio = bio
    db.session.commit()
    flash('个人资料更新成功！', 'success')
    return redirect(url_for('auth.profile'))


@auth_bp.route('/profile/avatar', methods=['POST'])
@login_required
def upload_avatar():
    """上传头像"""
    file = request.files.get('avatar')
    if not file or file.filename == '':
        flash('请选择要上传的图片。', 'error')
        return redirect(url_for('auth.profile'))

    if not allowed_image_file(file.filename):
        flash('仅支持 JPG、PNG、GIF、WebP 格式的图片。', 'error')
        return redirect(url_for('auth.profile'))

    from storage import save_file, delete_file

    # 删除旧头像文件
    if current_user.avatar:
        try:
            delete_file(current_user.avatar)
        except Exception:
            pass

    # 保存新头像
    avatar_key = save_file(file, file.filename)
    current_user.avatar = avatar_key
    db.session.commit()
    flash('头像更新成功！', 'success')
    return redirect(url_for('auth.profile'))


@auth_bp.route('/profile/avatar/delete', methods=['POST'])
@login_required
def delete_avatar():
    """删除头像（恢复默认）"""
    if current_user.avatar:
        from storage import delete_file
        try:
            delete_file(current_user.avatar)
        except Exception:
            pass
        current_user.avatar = None
        db.session.commit()
        flash('头像已删除，恢复为默认头像。', 'info')
    else:
        flash('当前没有自定义头像。', 'warning')
    return redirect(url_for('auth.profile'))
