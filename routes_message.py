"""消息通知路由"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Notification

message_bp = Blueprint('message', __name__, url_prefix='/message')


@message_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    pagination = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.is_read, Notification.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    # 标记显示的所有未读消息为已读
    for n in pagination.items:
        if not n.is_read:
            n.is_read = True
    db.session.commit()
    return render_template('message_list.html', notifications=pagination.items,
                           pagination=pagination)


@message_bp.route('/unread-count')
@login_required
def unread_count():
    count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


@message_bp.route('/<int:id>/read', methods=['POST'])
@login_required
def mark_read(id):
    notif = Notification.query.get_or_404(id)
    if notif.user_id != current_user.id:
        return jsonify({'error': '无权限'}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({'status': 'ok'})
