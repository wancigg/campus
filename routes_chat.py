"""好友私聊 + 群聊路由"""
import os
from datetime import timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import User, ChatMessage, ChatGroup, ChatGroupMember, ChatGroupMessage, Notification
from storage import save_file
from sqlalchemy import or_, and_

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

ALLOWED_IMAGE_EXT = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
ALLOWED_FILE_EXT = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'zip', 'rar', 'md'}


def _allowed_file(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in ALLOWED_IMAGE_EXT or ext in ALLOWED_FILE_EXT


def _get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in ALLOWED_IMAGE_EXT:
        return 'image'
    return 'file'


def _format_size(num_bytes):
    """格式化文件大小显示"""
    if num_bytes < 1024:
        return f'{num_bytes} B'
    elif num_bytes < 1024 * 1024:
        return f'{num_bytes // 1024} KB'
    else:
        return f'{(num_bytes / (1024 * 1024)):.1f} MB'


@chat_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    """聊天文件上传接口，返回 file_key/file_name/file_type/file_url/file_size"""
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    f = request.files['file']
    if not f or f.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    filename = secure_filename(f.filename) or 'file'
    if not _allowed_file(filename):
        return jsonify({'error': '不支持的文件类型，支持图片和常见文档格式'}), 400

    try:
        key = save_file(f, filename)
    except Exception as e:
        return jsonify({'error': f'文件上传失败：{str(e)}'}), 500

    ftype = _get_file_type(filename)
    # 计算本地文件大小（如果是本地存储）
    size = 0
    try:
        local_path = os.path.join(current_app.config['UPLOAD_FOLDER'], key)
        if os.path.exists(local_path):
            size = os.path.getsize(local_path)
    except Exception:
        pass

    from flask import url_for
    try:
        url = url_for('uploaded_file', key=key)
    except Exception:
        url = '/uploads/' + key

    return jsonify({
        'ok': True,
        'file_key': key,
        'file_name': filename,
        'file_type': ftype,
        'file_url': url,
        'file_size': size,
        'file_size_str': _format_size(size),
    })


@chat_bp.route('/')
@login_required
def list():
    """聊天列表：展示最近的私聊对象和群聊"""
    # 获取有私聊记录的好友（最近的对话对象排前面）
    friend_chats = db.session.query(
        ChatMessage.sender_id, ChatMessage.receiver_id,
        db.func.max(ChatMessage.created_at).label('last_time'),
        db.func.count(ChatMessage.id).label('unread')
    ).filter(
        or_(
            ChatMessage.sender_id == current_user.id,
            ChatMessage.receiver_id == current_user.id
        )
    ).group_by(
        ChatMessage.sender_id, ChatMessage.receiver_id
    ).order_by(db.text('last_time DESC')).all()

    # 处理私聊列表
    friend_chat_list = []
    seen = set()
    for row in friend_chats:
        partner_id = row.sender_id if row.sender_id != current_user.id else row.receiver_id
        if partner_id in seen:
            continue
        seen.add(partner_id)
        partner = User.query.get(partner_id)
        if not partner or not current_user.is_friend_with(partner_id):
            continue
        # 未读数量：对方发给我的未读消息
        unread_count = ChatMessage.query.filter_by(
            sender_id=partner_id, receiver_id=current_user.id, is_read=False
        ).count()
        # 转换 UTC 时间到北京时间
        last_time_beijing = row.last_time + timedelta(hours=8) if row.last_time else None
        friend_chat_list.append({
            'partner': partner,
            'last_time': last_time_beijing,
            'last_time_str': last_time_beijing.strftime('%m-%d %H:%M') if last_time_beijing else '',
            'unread': unread_count,
        })

    # 获取我参与的群聊
    my_groups = ChatGroup.query.join(ChatGroupMember).filter(
        ChatGroupMember.user_id == current_user.id
    ).order_by(ChatGroup.created_at.desc()).all()

    return render_template('chat_list.html',
                           friend_chats=friend_chat_list,
                           my_groups=my_groups)


@chat_bp.route('/friend/<int:user_id>')
@login_required
def friend_chat(user_id):
    """与好友一对一聊天页面"""
    partner = User.query.get_or_404(user_id)
    if not current_user.is_friend_with(user_id):
        flash('你们还不是好友，无法发起聊天。', 'error')
        return redirect(url_for('social.discover'))
    # 标记对方发给我的消息为已读
    ChatMessage.query.filter_by(
        sender_id=user_id, receiver_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    # 获取好友列表供切换到其他好友
    friends = current_user.get_friends()
    return render_template('chat_friend.html', partner=partner, friends=friends)


@chat_bp.route('/friend/<int:user_id>/send', methods=['POST'])
@login_required
def friend_send(user_id):
    """向好友发送消息（AJAX）——支持文本 + 图片/文件"""
    if not current_user.is_friend_with(user_id):
        return jsonify({'error': '不是好友'}), 403
    data = request.json or {}
    content = (data.get('content') or '').strip()
    file_key = (data.get('file_key') or '').strip()
    file_name = (data.get('file_name') or '').strip()
    file_type = (data.get('file_type') or '').strip() or 'text'

    if not content and not file_key:
        return jsonify({'error': '消息不能是空的'}), 400
    if file_key and file_type not in ('image', 'file'):
        file_type = _get_file_type(file_name) if file_name else 'file'

    msg = ChatMessage(
        sender_id=current_user.id, receiver_id=user_id,
        content=content or None,
        file_key=file_key or None,
        file_name=file_name or None,
        file_type=file_type if file_key else 'text',
    )
    db.session.add(msg)

    # 通知
    notif_text = ''
    if file_type == 'image' and file_key:
        notif_text = '[图片]'
    elif file_key:
        notif_text = f'[文件] {file_name}'
    if content:
        notif_text = (notif_text + ' ' + content).strip() if notif_text else content[:100]
    db.session.add(Notification(
        user_id=user_id,
        type='message',
        title=f'{current_user.username} 发来消息',
        content=notif_text[:100] or '新消息',
        link=url_for('chat.friend_chat', user_id=current_user.id)
    ))
    db.session.commit()
    return jsonify({'ok': True, 'message': msg.to_dict(current_user.id)})


@chat_bp.route('/friend/<int:user_id>/messages')
@login_required
def friend_messages(user_id):
    """获取与好友的消息记录（AJAX，支持增量拉取）"""
    if not current_user.is_friend_with(user_id):
        return jsonify({'error': '不是好友'}), 403
    last_id = request.args.get('last_id', 0, type=int)
    query = ChatMessage.query.filter(
        or_(
            and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == user_id),
            and_(ChatMessage.sender_id == user_id, ChatMessage.receiver_id == current_user.id)
        )
    )
    if last_id:
        query = query.filter(ChatMessage.id > last_id)
    msgs = query.order_by(ChatMessage.created_at.asc()).all()

    # 标记为已读
    ChatMessage.query.filter_by(
        sender_id=user_id, receiver_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()

    # 加入聊天的两个用户信息
    partner = User.query.get(user_id)

    return jsonify({
        'messages': [m.to_dict(current_user.id) for m in msgs],
        'partner': {
            'id': partner.id,
            'username': partner.username,
            'avatar': partner.avatar,
        },
    })


@chat_bp.route('/group/create', methods=['GET', 'POST'])
@login_required
def group_create():
    """创建群聊"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        member_ids = request.form.getlist('member_ids')
        if not name:
            flash('请输入群聊名称', 'error')
            return redirect(url_for('chat.group_create'))
        if len(member_ids) < 2:
            flash('请至少选择 2 位好友', 'error')
            return redirect(url_for('chat.group_create'))

        group = ChatGroup(name=name, created_by=current_user.id)
        db.session.add(group)
        db.session.flush()  # 获取 group.id

        # 创建者自动加入
        db.session.add(ChatGroupMember(group_id=group.id, user_id=current_user.id))
        for mid in member_ids:
            if mid.isdigit() and int(mid) != current_user.id:
                db.session.add(ChatGroupMember(group_id=group.id, user_id=int(mid)))

        # 发送系统消息
        db.session.add(ChatGroupMessage(
            group_id=group.id,
            sender_id=current_user.id,
            content=f'群聊 "{name}" 已创建，欢迎加入！'
        ))

        # 通知被邀请的好友
        for mid in member_ids:
            if mid.isdigit() and int(mid) != current_user.id:
                db.session.add(Notification(
                    user_id=int(mid),
                    type='system',
                    title='群聊邀请',
                    content=f'{current_user.username} 邀请你加入群聊 "{name}"',
                    link=url_for('chat.group_chat', group_id=group.id)
                ))

        db.session.commit()
        flash('群聊创建成功！', 'success')
        return redirect(url_for('chat.group_chat', group_id=group.id))

    friends = current_user.get_friends()
    return render_template('chat_group_create.html', friends=friends)


@chat_bp.route('/group/<int:group_id>')
@login_required
def group_chat(group_id):
    """群聊页面"""
    group = ChatGroup.query.get_or_404(group_id)
    # 检查是否是成员
    member = ChatGroupMember.query.filter_by(
        group_id=group_id, user_id=current_user.id
    ).first()
    if not member:
        flash('你不是该群聊的成员', 'error')
        return redirect(url_for('chat.list'))

    members = [m.user for m in group.members.all()]
    friends_not_in_group = [f for f in current_user.get_friends()
                            if f.id not in {m.id for m in members}]
    return render_template('chat_group.html', group=group, members=members,
                           friends_not_in_group=friends_not_in_group)


@chat_bp.route('/group/<int:group_id>/send', methods=['POST'])
@login_required
def group_send(group_id):
    """发送群聊消息（AJAX）——支持文本 + 图片/文件"""
    member = ChatGroupMember.query.filter_by(
        group_id=group_id, user_id=current_user.id
    ).first()
    if not member:
        return jsonify({'error': '不是群成员'}), 403
    data = request.json or {}
    content = (data.get('content') or '').strip()
    file_key = (data.get('file_key') or '').strip()
    file_name = (data.get('file_name') or '').strip()
    file_type = (data.get('file_type') or '').strip() or 'text'

    if not content and not file_key:
        return jsonify({'error': '消息不能是空的'}), 400
    if file_key and file_type not in ('image', 'file'):
        file_type = _get_file_type(file_name) if file_name else 'file'

    msg = ChatGroupMessage(
        group_id=group_id, sender_id=current_user.id,
        content=content or None,
        file_key=file_key or None,
        file_name=file_name or None,
        file_type=file_type if file_key else 'text',
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({'ok': True, 'message': msg.to_dict(current_user.id)})


@chat_bp.route('/group/<int:group_id>/messages')
@login_required
def group_messages(group_id):
    """获取群聊消息（AJAX，支持增量拉取）"""
    member = ChatGroupMember.query.filter_by(
        group_id=group_id, user_id=current_user.id
    ).first()
    if not member:
        return jsonify({'error': '不是群成员'}), 403
    last_id = request.args.get('last_id', 0, type=int)
    query = ChatGroupMessage.query.filter_by(group_id=group_id)
    if last_id:
        query = query.filter(ChatGroupMessage.id > last_id)
    msgs = query.order_by(ChatGroupMessage.created_at.asc()).all()
    return jsonify({
        'messages': [m.to_dict(current_user.id) for m in msgs],
    })


@chat_bp.route('/group/<int:group_id>/invite', methods=['POST'])
@login_required
def group_invite(group_id):
    """邀请好友加入群聊"""
    member = ChatGroupMember.query.filter_by(
        group_id=group_id, user_id=current_user.id
    ).first()
    if not member:
        flash('不是群成员', 'error')
        return redirect(url_for('chat.list'))
    user_id = request.form.get('user_id', type=int)
    if not user_id:
        flash('请选择好友', 'error')
        return redirect(url_for('chat.group_chat', group_id=group_id))
    # 检查是否已在群中
    existing = ChatGroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
    if existing:
        flash('该用户已在群聊中', 'error')
        return redirect(url_for('chat.group_chat', group_id=group_id))
    db.session.add(ChatGroupMember(group_id=group_id, user_id=user_id))

    group = ChatGroup.query.get(group_id)
    invited_user = User.query.get(user_id)
    db.session.add(ChatGroupMessage(
        group_id=group_id,
        sender_id=current_user.id,
        content=f'邀请了 {invited_user.username} 加入群聊'
    ))
    db.session.add(Notification(
        user_id=user_id,
        type='system',
        title='群聊邀请',
        content=f'{current_user.username} 邀请你加入群聊 "{group.name}"',
        link=url_for('chat.group_chat', group_id=group_id)
    ))
    db.session.commit()
    flash(f'已邀请 {invited_user.username} 加入群聊', 'success')
    return redirect(url_for('chat.group_chat', group_id=group_id))


@chat_bp.route('/group/<int:group_id>/leave', methods=['POST'])
@login_required
def group_leave(group_id):
    """退出群聊"""
    member = ChatGroupMember.query.filter_by(
        group_id=group_id, user_id=current_user.id
    ).first()
    if not member:
        flash('不是群成员', 'error')
        return redirect(url_for('chat.list'))
    group = ChatGroup.query.get(group_id)
    db.session.delete(member)
    # 系统消息
    db.session.add(ChatGroupMessage(
        group_id=group_id,
        sender_id=current_user.id,
        content=f'{current_user.username} 退出了群聊'
    ))
    db.session.commit()
    flash('你已退出群聊', 'success')
    return redirect(url_for('chat.list'))


@chat_bp.route('/unread-count')
@login_required
def unread_count():
    """未读聊天消息数（AJAX）"""
    friend_unread = ChatMessage.query.filter_by(
        receiver_id=current_user.id, is_read=False
    ).count()
    group_ids = [m.group_id for m in ChatGroupMember.query.filter_by(
        user_id=current_user.id
    ).all()]
    # 群聊未读简化处理：统计群聊消息总数（可后续优化）
    return jsonify({
        'friend_unread': friend_unread,
    })
