"""用户认证路由"""

import io
import random
import string

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Post, Material, Competition, Textbook
from sqlalchemy.exc import IntegrityError
from forms import validate_username, validate_email, validate_password, allowed_image_file, normalize_email
from PIL import Image, ImageDraw, ImageFont

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 验证码字符集：去掉易混淆的 0/O/1/I
_CAPTCHA_CHARS = ''.join(
    c for c in (string.ascii_uppercase + string.digits)
    if c not in {'0', 'O', '1', 'I'}
)


def _generate_captcha_text(length=4):
    return ''.join(random.choices(_CAPTCHA_CHARS, k=length))


def _render_captcha_image(text: str) -> bytes:
    """使用 Pillow 生成带干扰线/噪点/轻微倾斜的验证码 PNG 字节流。"""
    width, height = 130, 44
    background = (250, 250, 255)
    img = Image.new('RGB', (width, height), background)
    draw = ImageDraw.Draw(img)

    # 尝试加载可读字体，失败则退回默认字体
    font = None
    font_candidates = [
        'arial.ttf',
        'Arial.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/Arial.ttf',
    ]
    for path in font_candidates:
        try:
            font = ImageFont.truetype(path, 28)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    # 干扰线
    for _ in range(4):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        color = (
            random.randint(160, 220),
            random.randint(160, 220),
            random.randint(180, 230),
        )
        draw.line((x1, y1, x2, y2), fill=color, width=1)

    # 噪点
    for _ in range(width * height // 20):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        color = (
            random.randint(180, 230),
            random.randint(180, 230),
            random.randint(200, 240),
        )
        img.putpixel((x, y), color)

    # 逐字符绘制：随机颜色 + 轻微上下偏移
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        text_w, text_h = draw.textsize(text, font=font)
    total_gap = width - text_w - 12
    step_x = total_gap // max(len(text), 1)
    x = 8
    for ch in text:
        dy = random.randint(-3, 3)
        color = (
            random.randint(30, 110),
            random.randint(50, 140),
            random.randint(160, 230),
        )
        # 随机偏蓝色调，贴近示例图风格
        color = (
            random.randint(10, 80),
            random.randint(60, 160),
            random.randint(180, 245),
        )
        draw.text((x, (height - text_h) // 2 + dy), ch, font=font, fill=color)
        try:
            ch_bbox = draw.textbbox((0, 0), ch, font=font)
            x += (ch_bbox[2] - ch_bbox[0]) + step_x // max(len(text), 1) + 1
        except AttributeError:
            ch_w, _ = draw.textsize(ch, font=font)
            x += ch_w + step_x // max(len(text), 1) + 1

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


@auth_bp.route('/captcha')
def captcha():
    """生成验证码图片并返回 image/png，答案写入 session（一次性）。"""
    answer = _generate_captcha_text(4)
    image_bytes = _render_captcha_image(answer)
    session['captcha_answer'] = answer
    headers = {
        'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
        'Pragma': 'no-cache',
        'Expires': '0',
    }
    return Response(image_bytes, mimetype='image/png', headers=headers)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    username = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # —— 图形验证码校验（一次性、忽略大小写/空白）——
        expected = session.pop('captcha_answer', None)
        user_input = request.form.get('captcha', '').strip()
        captcha_ok = bool(
            expected and user_input
            and expected.lower() == user_input.lower()
        )
        if not captcha_ok:
            flash('验证码错误或已过期，请刷新后重试。', 'error')
            return render_template('login.html', username=username, has_error=True)

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember'))
            flash('登录成功，欢迎回来！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('用户名或密码错误。', 'error')
        return render_template('login.html', username=username, has_error=True)
    return render_template('login.html', username=username)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        # 邮箱统一归一化：去空白 + 小写，确保一个邮箱只能注册一个账号
        email = normalize_email(request.form.get('email', ''))
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
        # 用归一化后的小写邮箱查重，避免 "A@x.com" 与 "a@x.com" 绕过
        if User.query.filter(User.email.isnot(None), db.func.lower(User.email) == email).first():
            flash('邮箱已被注册。', 'error')
            return render_template('register.html', username=username, email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        user.add_points(10)  # 注册奖励：+10 积分
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            # 并发提交兜底：数据库唯一约束冲突时给出明确中文提示
            db.session.rollback()
            flash('该邮箱已注册，请直接登录或更换邮箱。', 'error')
            return render_template('register.html', username=username, email=email)
        flash('注册成功，请登录！赠 10 初始积分 🎁', 'success')
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
    competition_count = Competition.query.filter(
        Competition.owner_id == current_user.id,
        Competition.status != 'archived'
    ).count()
    archived_team_count = Competition.query.filter_by(
        owner_id=current_user.id, status='archived'
    ).count()
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
        pagination = Competition.query.filter(
            Competition.owner_id == current_user.id,
            Competition.status != 'archived'
        ).order_by(Competition.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        items = pagination.items
    elif tab == 'archived_teams':
        pagination = Competition.query.filter_by(
            owner_id=current_user.id, status='archived'
        ).order_by(Competition.created_at.desc())\
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
                           archived_team_count=archived_team_count,
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
    # 邮箱统一归一化：去空白 + 小写，确保一个邮箱只能绑定一个账号
    email = normalize_email(request.form.get('email', ''))

    if email and email != normalize_email(current_user.email):
        ok, msg = validate_email(email)
        if not ok:
            flash(msg, 'error')
            return redirect(url_for('auth.profile'))
        if User.query.filter(
            User.email.isnot(None),
            db.func.lower(User.email) == email,
            User.id != current_user.id
        ).first():
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
