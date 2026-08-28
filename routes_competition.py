"""竞赛组队路由"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from extensions import db
from models import (Competition, Application, Notification,
                    ConversationMessage, TeamGroup, GroupMember, GroupMessage)
from moderation import moderate_text
from datetime import datetime

competition_bp = Blueprint('competition', __name__, url_prefix='/competition')


def ensure_group(comp):
    """确保交流群存在，并将发起人及所有已通过审核的申请人加入群。
    返回 TeamGroup 实例；若没有任何已通过成员则返回 None。"""
    if comp.approved_count == 0:
        return None
    group = comp.group
    if not group:
        group = TeamGroup(competition_id=comp.id, name=f'{comp.title} 交流群')
        db.session.add(group)
        db.session.flush()  # 取 group.id 用于添加成员
    # 群成员 = 发起人 + 所有已通过申请人
    member_ids = {comp.owner_id}
    for app in comp.applications.filter_by(status='approved'):
        member_ids.add(app.user_id)
    existing_ids = {gm.user_id for gm in group.members}
    for uid in member_ids - existing_ids:
        db.session.add(GroupMember(group_id=group.id, user_id=uid))
    return group


@competition_bp.route('/')
def list():
    today = datetime.utcnow().date()

    page = request.args.get('page', 1, type=int)
    comp_type = request.args.get('type', '')
    # 已归档队伍仅在用户个人中心展示，不再出现在公共招募看板
    query = Competition.query.filter(Competition.status != 'archived')
    if comp_type:
        query = query.filter_by(comp_type=comp_type)
    pagination = query.order_by(Competition.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)

    # ===== A方案：顶部3个状态数字卡 =====
    all_comps = query.all()  # 展示当前筛选条件下的分组 & 计数
    open_count = 0
    full_count = 0
    closed_count = 0

    # ===== B方案：三列看板分组（招募中 / 已满员 / 已截止） =====
    col_opening = []
    col_full = []
    col_closed = []
    for c in all_comps:
        is_closed_status = (c.status == 'closed')
        is_over_deadline = (c.deadline and c.deadline < today)
        is_full = (c.team_size and c.team_size > 0 and c.approved_count >= c.team_size)

        if is_closed_status or is_over_deadline:
            closed_count += 1
            col_closed.append(c)
        elif is_full:
            full_count += 1
            col_full.append(c)
        else:
            open_count += 1
            col_opening.append(c)

    return render_template('competition_list.html', competitions=pagination.items,
                           pagination=pagination, comp_type=comp_type,
                           open_count=open_count, full_count=full_count,
                           closed_count=closed_count,
                           col_opening=col_opening, col_full=col_full,
                           col_closed=col_closed,
                           today=today)


@competition_bp.route('/<int:id>')
def detail(id):
    comp = Competition.query.get_or_404(id)
    user_application = None
    is_group_member = False
    if current_user.is_authenticated:
        user_application = Application.query.filter_by(
            competition_id=id, user_id=current_user.id).first()
        if comp.group:
            is_group_member = bool(GroupMember.query.filter_by(
                group_id=comp.group.id, user_id=current_user.id).first())
    return render_template('competition_detail.html',
                           competition=comp, user_application=user_application,
                           is_group_member=is_group_member)


@competition_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        comp_type = request.form.get('comp_type', '')
        description = request.form.get('description', '').strip()
        team_size = request.form.get('team_size', 0, type=int)
        deadline_str = request.form.get('deadline', '')

        if not title or not comp_type or not description:
            flash('请填写所有必填项。', 'error')
            return render_template('competition_edit.html')

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                flash('日期格式不正确。', 'error')
                return render_template('competition_edit.html')

        comp = Competition(
            title=title, comp_type=comp_type, description=description,
            team_size=team_size, deadline=deadline,
            owner_id=current_user.id
        )
        db.session.add(comp)
        current_user.add_points(3)  # 发布招募奖励：+3
        db.session.commit()
        flash('招募发布成功！+3 积分 🏆', 'success')
        return redirect(url_for('competition.detail', id=comp.id))
    return render_template('competition_edit.html')


@competition_bp.route('/<int:id>/apply', methods=['POST'])
@login_required
def apply(id):
    comp = Competition.query.get_or_404(id)
    if comp.status != 'open':
        flash('该招募已关闭。', 'error')
        return redirect(url_for('competition.detail', id=id))
    if comp.owner_id == current_user.id:
        flash('不能申请自己发布的招募。', 'error')
        return redirect(url_for('competition.detail', id=id))
    existing = Application.query.filter_by(
        competition_id=id, user_id=current_user.id).first()
    if existing:
        flash('您已经申请过了。', 'warning')
        return redirect(url_for('competition.detail', id=id))
    message = request.form.get('message', '').strip()
    app = Application(
        competition_id=id, user_id=current_user.id, message=message
    )
    db.session.add(app)
    db.session.flush()  # 取 app.id 用于初始化对话
    # 将申请留言作为对话的第一条消息，便于双方在此基础上继续沟通
    if message:
        conv = ConversationMessage(
            competition_id=id, application_id=app.id,
            sender_id=current_user.id, content=message
        )
        db.session.add(conv)
    notif = Notification(
        user_id=comp.owner_id,
        type='application',
        title='新的组队申请',
        content=f'{current_user.username} 申请加入你的招募《{comp.title}》。',
        link=url_for('competition.detail', id=id)
    )
    db.session.add(notif)
    db.session.commit()
    flash('申请已提交！你可以在下方与发起人对话沟通。', 'success')
    return redirect(url_for('competition.detail', id=id))


@competition_bp.route('/<int:id>/applications/<int:app_id>/<action>', methods=['POST'])
@login_required
def handle_application(id, app_id, action):
    comp = Competition.query.get_or_404(id)
    if comp.owner_id != current_user.id:
        flash('只有招募发起人可以审核申请。', 'error')
        return redirect(url_for('competition.detail', id=id))
    app = Application.query.get_or_404(app_id)
    if app.competition_id != comp.id:
        abort(404)
    if action not in ('approve', 'reject'):
        flash('无效操作。', 'error')
        return redirect(url_for('competition.detail', id=id))
    old_status = app.status
    app.status = 'approved' if action == 'approve' else 'rejected'
    status_text = '已通过' if action == 'approve' else '已拒绝'
    notif = Notification(
        user_id=app.user_id,
        type='application',
        title=f'组队申请{status_text}',
        content=f'你对《{comp.title}》的申请已被{status_text}。',
        link=url_for('competition.detail', id=id)
    )
    db.session.add(notif)
    # 审核通过后，将该成员自动加入交流群（若已有已通过成员则自动建群）
    if action == 'approve':
        ensure_group(comp)
    db.session.commit()
    if action == 'approve':
        flash(f'已{status_text}该申请，已自动将其加入交流群。', 'success')
    else:
        flash(f'已{status_text}该申请。', 'success')
    return redirect(url_for('competition.detail', id=id))


@competition_bp.route('/<int:id>/conversation/<int:app_id>/send', methods=['POST'])
@login_required
def send_conversation(id, app_id):
    """发送一条组队对话消息（申请人与发起人之间）。"""
    comp = Competition.query.get_or_404(id)
    app = Application.query.get_or_404(app_id)
    if app.competition_id != comp.id:
        abort(404)
    # 仅申请人本人或招募发起人可参与该对话
    if current_user.id != app.user_id and current_user.id != comp.owner_id:
        return jsonify({'error': '无权发送消息'}), 403
    content = (request.form.get('content') or (request.get_json(silent=True) or {}).get('content', '')).strip()
    if not content:
        return jsonify({'error': '消息内容不能为空'}), 400

    # ====== 消息审核 ======
    check = moderate_text(content, context_type='chat')
    if check['reject']:
        return jsonify({'error': f'消息发送失败：{check["reason"]}'}), 400

    msg = ConversationMessage(
        competition_id=comp.id, application_id=app.id,
        sender_id=current_user.id, content=content
    )
    db.session.add(msg)
    # 通知对话的对方
    peer_id = comp.owner_id if current_user.id == app.user_id else app.user_id
    if peer_id != current_user.id:
        notif = Notification(
            user_id=peer_id,
            type='message',
            title='新的对话消息',
            content=f'{current_user.username} 在《{comp.title}》组队对话中给你发了消息。',
            link=url_for('competition.detail', id=id)
        )
        db.session.add(notif)
    db.session.commit()
    return jsonify({'ok': True, 'message': msg.to_dict(current_user.id)})


@competition_bp.route('/<int:id>/conversation/<int:app_id>/messages')
@login_required
def conversation_messages(id, app_id):
    """轮询拉取组队对话消息（增量，可带 last_id 只取新消息）。"""
    comp = Competition.query.get_or_404(id)
    app = Application.query.get_or_404(app_id)
    if app.competition_id != comp.id:
        abort(404)
    if current_user.id != app.user_id and current_user.id != comp.owner_id:
        return jsonify({'error': '无权查看'}), 403
    last_id = request.args.get('last_id', 0, type=int)
    query = ConversationMessage.query.filter_by(application_id=app.id)
    if last_id:
        query = query.filter(ConversationMessage.id > last_id)
    msgs = query.order_by(ConversationMessage.id.asc()).all()
    return jsonify({'messages': [m.to_dict(current_user.id) for m in msgs]})


@competition_bp.route('/<int:id>/group/send', methods=['POST'])
@login_required
def send_group_message(id):
    """向竞赛交流群发送一条消息。"""
    comp = Competition.query.get_or_404(id)
    group = comp.group
    if not group:
        return jsonify({'error': '交流群尚未创建'}), 404
    if not GroupMember.query.filter_by(group_id=group.id, user_id=current_user.id).first():
        return jsonify({'error': '你不是该交流群成员'}), 403
    content = (request.form.get('content') or (request.get_json(silent=True) or {}).get('content', '')).strip()
    if not content:
        return jsonify({'error': '消息内容不能为空'}), 400

    # ====== 消息审核 ======
    check = moderate_text(content, context_type='chat')
    if check['reject']:
        return jsonify({'error': f'消息发送失败：{check["reason"]}'}), 400

    msg = GroupMessage(group_id=group.id, sender_id=current_user.id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'ok': True, 'message': msg.to_dict(current_user.id)})


@competition_bp.route('/<int:id>/group/messages')
@login_required
def group_messages(id):
    """轮询拉取交流群消息（增量，可带 last_id）。"""
    comp = Competition.query.get_or_404(id)
    group = comp.group
    if not group:
        return jsonify({'messages': []})
    if not GroupMember.query.filter_by(group_id=group.id, user_id=current_user.id).first():
        return jsonify({'error': '你不是该交流群成员'}), 403
    last_id = request.args.get('last_id', 0, type=int)
    query = GroupMessage.query.filter_by(group_id=group.id)
    if last_id:
        query = query.filter(GroupMessage.id > last_id)
    msgs = query.order_by(GroupMessage.id.asc()).all()
    return jsonify({'messages': [m.to_dict(current_user.id) for m in msgs]})


@competition_bp.route('/<int:id>/close', methods=['POST'])
@login_required
def close(id):
    comp = Competition.query.get_or_404(id)
    if comp.owner_id != current_user.id:
        flash('只有招募发起人可以关闭。', 'error')
        return redirect(url_for('competition.detail', id=id))
    comp.status = 'closed'
    db.session.commit()
    flash('招募已关闭。', 'info')
    return redirect(url_for('competition.detail', id=id))


@competition_bp.route('/<int:id>/archive', methods=['POST'])
@login_required
def archive(id):
    """归档队伍，保留招募、申请、对话和交流群历史。"""
    comp = Competition.query.get_or_404(id)
    if comp.owner_id != current_user.id:
        flash('只有发起人可以归档该队伍。', 'error')
        return redirect(url_for('competition.detail', id=id))
    if comp.status != 'closed':
        flash('请先关闭招募，再归档队伍。', 'warning')
        return redirect(url_for('competition.detail', id=id))
    comp.status = 'archived'
    db.session.commit()
    flash('队伍已归档，招募详情和历史记录已保留。', 'success')
    return redirect(url_for('auth.profile', tab='archived_teams'))
