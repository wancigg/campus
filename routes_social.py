"""社交模块：好友系统"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, FriendRequest, Notification

social_bp = Blueprint('social', __name__, url_prefix='/social')


@social_bp.route('/friends')
@login_required
def friend_list():
    """好友列表页（含待处理请求）"""
    tab = request.args.get('tab', 'friends')  # friends / requests
    friends = current_user.get_friends()
    pending_requests = current_user.get_pending_requests()
    return render_template('social_friends.html',
                           friends=friends,
                           pending_requests=pending_requests,
                           tab=tab)


@social_bp.route('/discover')
@login_required
def discover():
    """发现用户（搜索）"""
    q = request.args.get('q', '').strip()
    users = []
    if q:
        users = User.query.filter(
            User.username.contains(q),
            User.id != current_user.id
        ).limit(30).all()
    return render_template('social_discover.html', users=users, q=q)


@social_bp.route('/request/send/<int:user_id>', methods=['POST'])
@login_required
def send_request(user_id):
    """发送好友申请"""
    if user_id == current_user.id:
        flash('不能添加自己为好友。', 'error')
        return redirect_back()

    target = User.query.get_or_404(user_id)

    # 检查是否已是好友
    if current_user.is_friend_with(user_id):
        flash('你们已经是好友了。', 'info')
        return redirect_back()

    # 检查是否已有待处理的请求
    existing = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user.id) & (FriendRequest.receiver_id == user_id)) |
        ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == current_user.id))
    ).first()

    if existing:
        if existing.status == 'pending':
            if existing.sender_id == current_user.id:
                flash('你已经发送过好友申请了，请等待对方处理。', 'warning')
            else:
                # 对方已发来请求，直接接受
                existing.status = 'accepted'
                existing.updated_at = db.func.now()
                # 通知对方
                db.session.add(Notification(
                    user_id=existing.sender_id,
                    type='friend',
                    title='好友申请已通过',
                    content=f'{current_user.username} 通过了你的好友申请。',
                    link=url_for('social.friend_list')
                ))
                db.session.commit()
                flash(f'你与 {target.username} 已成为好友！', 'success')
            return redirect_back()
        elif existing.status == 'rejected':
            # 曾被拒绝，允许重新发送（更新请求）
            existing.sender_id = current_user.id
            existing.receiver_id = user_id
            existing.status = 'pending'
            existing.message = request.form.get('message', '').strip()[:200]
            existing.created_at = db.func.now()
            existing.updated_at = db.func.now()
        else:
            flash('未知错误。', 'error')
            return redirect_back()
    else:
        msg = request.form.get('message', '').strip()[:200]
        req = FriendRequest(
            sender_id=current_user.id,
            receiver_id=user_id,
            message=msg
        )
        db.session.add(req)

    # 发送通知
    db.session.add(Notification(
        user_id=user_id,
        type='friend',
        title='新的好友申请',
        content=f'{current_user.username} 请求添加你为好友。',
        link=url_for('social.friend_list', tab='requests')
    ))

    db.session.commit()
    flash(f'好友申请已发送给 {target.username}。', 'success')
    return redirect_back()


@social_bp.route('/request/accept/<int:request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    """接受好友申请"""
    req = FriendRequest.query.get_or_404(request_id)
    if req.receiver_id != current_user.id:
        flash('无权操作。', 'error')
        return redirect_back()

    if req.status != 'pending':
        flash('该申请已处理。', 'info')
        return redirect_back()

    req.status = 'accepted'
    req.updated_at = db.func.now()

    # 通知对方
    db.session.add(Notification(
        user_id=req.sender_id,
        type='friend',
        title='好友申请已通过',
        content=f'{current_user.username} 通过了你的好友申请。',
        link=url_for('social.friend_list')
    ))

    db.session.commit()
    flash(f'你已接受 {req.sender.username} 的好友申请，你们现在是好友了！', 'success')
    return redirect(url_for('social.friend_list'))


@social_bp.route('/request/accept-user/<int:user_id>', methods=['POST'])
@login_required
def accept_request_from_user(user_id):
    """接受来自指定用户的好友申请（按 user_id 查找 pending 请求）"""
    req = FriendRequest.query.filter_by(
        sender_id=user_id, receiver_id=current_user.id, status='pending'
    ).first()
    if not req:
        flash('没有待处理的好友申请。', 'error')
        return redirect_back()

    req.status = 'accepted'
    req.updated_at = db.func.now()

    db.session.add(Notification(
        user_id=req.sender_id,
        type='friend',
        title='好友申请已通过',
        content=f'{current_user.username} 通过了你的好友申请。',
        link=url_for('social.friend_list')
    ))

    db.session.commit()
    flash(f'你已接受 {req.sender.username} 的好友申请，你们现在是好友了！', 'success')
    return redirect_back()


@social_bp.route('/request/reject/<int:request_id>', methods=['POST'])
@login_required
def reject_request(request_id):
    """拒绝好友申请"""
    req = FriendRequest.query.get_or_404(request_id)
    if req.receiver_id != current_user.id:
        flash('无权操作。', 'error')
        return redirect_back()

    if req.status != 'pending':
        flash('该申请已处理。', 'info')
        return redirect_back()

    req.status = 'rejected'
    req.updated_at = db.func.now()
    db.session.commit()
    flash('已拒绝该好友申请。', 'info')
    return redirect(url_for('social.friend_list'))


@social_bp.route('/friend/remove/<int:user_id>', methods=['POST'])
@login_required
def remove_friend(user_id):
    """删除好友"""
    req = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user.id) & (FriendRequest.receiver_id == user_id)) |
        ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == current_user.id)),
        FriendRequest.status == 'accepted'
    ).first()

    if not req:
        flash('不是好友关系。', 'error')
        return redirect_back()

    db.session.delete(req)
    db.session.commit()
    flash('已删除好友。', 'info')
    return redirect_back()


@social_bp.route('/search')
@login_required
def search_users():
    """JSON 搜索用户（供弹窗用）"""
    q = request.args.get('q', '').strip()
    if len(q) < 1:
        return jsonify([])
    users = User.query.filter(
        User.username.contains(q),
        User.id != current_user.id
    ).limit(15).all()
    result = []
    for u in users:
        status = current_user.get_friend_request_status(u.id)
        result.append({
            'id': u.id,
            'username': u.username,
            'avatar': u.avatar,
            'bio': (u.bio or '')[:50],
            'friend_status': status,
            'is_friend': status == 'accepted'
        })
    return jsonify(result)


def redirect_back():
    """重定向回上一页或首页"""
    next_page = request.args.get('next') or request.referrer
    if next_page:
        return redirect(next_page)
    return redirect(url_for('index'))
