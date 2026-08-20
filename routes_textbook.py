"""二手闲置路由（泛化，支持所有闲置物品，不限于教材）"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from extensions import db
from models import Textbook, TextbookMessage, Notification, User
from forms import validate_title

textbook_bp = Blueprint('textbook', __name__, url_prefix='/textbook')

# 物品类型选项
CATEGORIES = Textbook.CATEGORIES


@textbook_bp.route('/')
def list():
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('q', '').strip()
    cat = request.args.get('cat', '').strip()
    query = Textbook.query
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
                           categories=CATEGORIES, current_cat=cat)


@textbook_bp.route('/<int:id>')
def detail(id):
    textbook = Textbook.query.get_or_404(id)
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

        cover_image = ''
        description_images = ''
        from storage import save_file
        # 封面图片（单张）
        cover_file = request.files.get('cover')
        if cover_file and cover_file.filename:
            cover_image = save_file(cover_file, cover_file.filename)
        # 描述图片（多张）
        desc_keys = []
        for f in request.files.getlist('desc_images'):
            if f and f.filename:
                desc_keys.append(save_file(f, f.filename))
        description_images = ','.join(desc_keys) if desc_keys else ''

        textbook = Textbook(
            title=title, category=category, author=author, publisher=publisher,
            price=price, condition=condition, description=description,
            cover_image=cover_image, description_images=description_images,
            user_id=current_user.id
        )
        db.session.add(textbook)
        db.session.commit()
        flash('闲置物品发布成功！', 'success')
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
    db.session.delete(textbook)
    db.session.commit()
    flash('闲置物品已删除。', 'success')
    return redirect(url_for('textbook.list'))
