"""二手闲置路由（泛化，支持所有闲置物品，不限于教材）"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from extensions import db
from models import Textbook, TextbookMessage, Notification, User, TextbookFavorite
from forms import validate_title
from moderation import moderate_text, moderate_image_bytes

textbook_bp = Blueprint('textbook', __name__, url_prefix='/textbook')


def _visible_textbooks_q():
    """闲置可见过滤：已通过 OR 作者本人 OR 管理员"""
    from sqlalchemy import or_, and_
    base = Textbook.is_approved.is_(True)
    if not current_user.is_authenticated:
        return base
    if current_user.is_admin():
        return or_(base, Textbook.is_approved.is_(False))
    return or_(base, and_(Textbook.is_approved.is_(False), Textbook.user_id == current_user.id))


# 物品类型选项
CATEGORIES = Textbook.CATEGORIES


@textbook_bp.route('/')
def list():
    from datetime import datetime, timedelta
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('q', '').strip()
    cat = request.args.get('cat', '').strip()

    vf = _visible_textbooks_q()
    # ===== A方案：顶部统计小卡数据 =====
    total_count = Textbook.query.filter(vf).count()
    available_count = Textbook.query.filter(vf).filter_by(trade_status='available').count()
    sold_count = Textbook.query.filter(vf).filter_by(trade_status='sold').count()
    today_start = datetime.utcnow().date()
    today_new = Textbook.query.filter(
        db.func.date(Textbook.created_at) == today_start
    ).filter(vf).count()
    # 分类占比（标签云）
    cat_counts = dict(db.session.query(
        Textbook.category, db.func.count(Textbook.id)
    ).filter(vf).group_by(Textbook.category).all())

    query = Textbook.query.filter(vf)
    if keyword:
        query = query.filter(
            or_(Textbook.title.contains(keyword), Textbook.author.contains(keyword))
        )
    if cat:
        query = query.filter(Textbook.category == cat)
    pagination = query.order_by(Textbook.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)
    return render_template('textbook_list.html', textbooks=pagination.items,
                           pagination=pagination, keyword=keyword,
                           categories=CATEGORIES, current_cat=cat,
                           total_count=total_count,
                           available_count=available_count,
                           sold_count=sold_count,
                           today_new=today_new,
                           cat_counts=cat_counts)


@textbook_bp.route('/<int:id>')
def detail(id):
    textbook = Textbook.query.get_or_404(id)
    if not textbook.is_approved:
        if not current_user.is_authenticated:
            abort(403)
        if not (current_user.id == textbook.user_id or current_user.is_admin()):
            abort(403)
    is_participant = False
    can_view = False
    if current_user.is_authenticated:
        is_participant = bool(TextbookMessage.query.filter_by(
            textbook_id=id, sender_id=current_user.id).first())
        can_view = (current_user.id == textbook.user_id) or is_participant
    messages = textbook.messages.order_by(TextbookMessage.created_at).all() if can_view else []

    # 参与对话的买家（非发布者），供商家回复时选择
    participants = []
    if current_user.is_authenticated and current_user.id == textbook.user_id:
        pids = db.session.query(TextbookMessage.sender_id).filter(
            TextbookMessage.textbook_id == id,
            TextbookMessage.sender_id != textbook.user_id
        ).distinct().all()
        if pids:
            participants = User.query.filter(
                User.id.in_([p[0] for p in pids])).all()
    cover_image = textbook.cover_image
    desc_images = textbook.description_images.split(',') if textbook.description_images else []
    return render_template('textbook_detail.html', textbook=textbook, messages=messages,
                           can_view=can_view, is_participant=is_participant,
                           participants=participants, cover_image=cover_image,
                           desc_images=desc_images)


@textbook_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '书籍').strip()
        author = request.form.get('author', '').strip()  # 品牌/作者
        publisher = request.form.get('publisher', '').strip()  # 型号/出版社
        price = request.form.get('price', type=float)
        condition = request.form.get('condition', '')
        description = request.form.get('description', '').strip()

        if not title or not price:
            flash('请填写物品名称和价格。', 'error')
            return render_template('textbook_edit.html', categories=CATEGORIES)
        if price <= 0:
            flash('价格必须大于0。', 'error')
            return render_template('textbook_edit.html', categories=CATEGORIES)
        if category not in CATEGORIES:
            category = '其他'

        # ====== 1) 文字审核：标题/描述/品牌/型号 ======
        text_block = '\n'.join(filter(None, [title, description, author, publisher]))
        check = moderate_text(text_block, context_type='textbook_desc')
        if check['reject']:
            flash(f"发布失败：{check['reason']}", 'error')
            return render_template('textbook_edit.html', categories=CATEGORIES)

        # ====== 2) 图片审核（封面 + 描述图）在存盘前先读 bytes 校验 ======
        cover_image = ''
        description_images = ''
        from storage import save_file

        # 封面图片（单张）
        cover_file = request.files.get('cover')
        if cover_file and cover_file.filename:
            try:
                blob = cover_file.read()
                cover_file.seek(0)
            except Exception:
                flash('封面图片读取失败。', 'error')
                return render_template('textbook_edit.html', categories=CATEGORIES)
            cimg = moderate_image_bytes(blob, filename=cover_file.filename)
            if cimg['reject']:
                flash(f"封面未通过：{cimg['reason']}", 'error')
                return render_template('textbook_edit.html', categories=CATEGORIES)
            cover_image = save_file(cover_file, cover_file.filename)

        # 描述图片（多张）
        desc_keys = []
        for f in request.files.getlist('desc_images'):
            if f and f.filename:
                try:
                    blob = f.read()
                    f.seek(0)
                except Exception:
                    flash('描述图片读取失败。', 'error')
                    return render_template('textbook_edit.html', categories=CATEGORIES)
                dimg = moderate_image_bytes(blob, filename=f.filename)
                if dimg['reject']:
                    flash(f"描述图片 {f.filename} 未通过：{dimg['reason']}", 'error')
                    return render_template('textbook_edit.html', categories=CATEGORIES)
                desc_keys.append(save_file(f, f.filename))
        description_images = ','.join(desc_keys) if desc_keys else ''

        textbook = Textbook(
            title=title, category=category, author=author, publisher=publisher,
            price=price, condition=condition, description=description,
            cover_image=cover_image, description_images=description_images,
            user_id=current_user.id,
            is_approved=(check['level'] == 'pass'),
            moderation_note=(check['reason'][:500] if check['level'] == 'warn' else ''),
        )
        db.session.add(textbook)
        if check['level'] == 'pass':
            current_user.add_points(3)  # 发布闲置奖励：+3
        db.session.commit()
        if check['level'] == 'warn':
            flash('闲置已提交，内容正在人工审核中（一般 24 小时内处理），审核通过后展示并奖励积分。', 'warning')
        else:
            flash('闲置物品发布成功！+3 积分 🛒', 'success')
        return redirect(url_for('textbook.detail', id=textbook.id))
    return render_template('textbook_edit.html', categories=CATEGORIES)


@textbook_bp.route('/<int:id>/message', methods=['POST'])
@login_required
def message(id):
    textbook = Textbook.query.get_or_404(id)
    content = request.form.get('content', '').strip()
    if not content:
        flash('请输入消息内容。', 'error')
        return redirect(url_for('textbook.detail', id=id))

    # 确定接收人：商家回复买家；买家联系商家
    if current_user.id == textbook.user_id:
        # 商家回复，receiver 必须是参与对话的买家
        buyer_ids = [r[0] for r in db.session.query(TextbookMessage.sender_id).filter(
            TextbookMessage.textbook_id == id,
            TextbookMessage.sender_id != textbook.user_id
        ).distinct().all()]
        receiver_id = request.form.get('receiver_id', type=int)
        if not receiver_id or receiver_id not in buyer_ids:
            receiver_id = buyer_ids[0] if buyer_ids else textbook.user_id
    else:
        receiver_id = textbook.user_id

    msg = TextbookMessage(
        textbook_id=id, sender_id=current_user.id,
        receiver_id=receiver_id, content=content
    )
    db.session.add(msg)
    if receiver_id != current_user.id:
        notif = Notification(
            user_id=receiver_id,
            type='message',
            title='闲置物品收到新消息',
            content=f'{current_user.username} 对你的闲置《{textbook.title}》发送了消息。',
            link=url_for('textbook.detail', id=id)
        )
        db.session.add(notif)
    db.session.commit()
    flash('消息已发送。', 'success')
    return redirect(url_for('textbook.detail', id=id))


@textbook_bp.route('/<int:id>/status/<status>', methods=['POST'])
@login_required
def change_status(id, status):
    textbook = Textbook.query.get_or_404(id)
    if textbook.user_id != current_user.id:
        flash('只有发布者可以修改状态。', 'error')
        return redirect(url_for('textbook.detail', id=id))
    if status in ('available', 'reserved', 'sold'):
        textbook.trade_status = status
        db.session.commit()
        flash('状态已更新。', 'success')
    return redirect(url_for('textbook.detail', id=id))


@textbook_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    textbook = Textbook.query.get_or_404(id)
    if textbook.user_id != current_user.id:
        flash('只有发布者可以删除该闲置物品。', 'error')
        return redirect(url_for('textbook.detail', id=id))
    # 删除关联图片文件
    from storage import delete_file
    if textbook.cover_image:
        delete_file(textbook.cover_image)
    if textbook.description_images:
        for key in textbook.description_images.split(','):
            if key:
                delete_file(key)
    TextbookMessage.query.filter_by(textbook_id=id).delete()
    TextbookFavorite.query.filter_by(textbook_id=id).delete()
    db.session.delete(textbook)
    db.session.commit()
    flash('闲置物品已删除。', 'success')
    return redirect(url_for('textbook.list'))


@textbook_bp.route('/<int:id>/favorite', methods=['POST'])
@login_required
def favorite(id):
    """二手闲置收藏/取消收藏（AJAX）"""
    textbook = Textbook.query.get_or_404(id)
    existing = TextbookFavorite.query.filter_by(textbook_id=id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'status': 'unfavorited'})
    fav = TextbookFavorite(textbook_id=id, user_id=current_user.id)
    db.session.add(fav)
    db.session.commit()
    return jsonify({'status': 'favorited'})
