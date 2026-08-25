"""学习资料路由"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from extensions import db
from models import Material, MaterialReview, Notification, MaterialFavorite
from moderation import moderate_text

materials_bp = Blueprint('materials', __name__, url_prefix='/materials')


def _visible_materials_q():
    """资料可见过滤：已通过 OR 作者本人 OR 管理员"""
    from sqlalchemy import or_, and_
    base = Material.is_approved.is_(True)
    if not current_user.is_authenticated:
        return base
    if current_user.is_admin():
        return or_(base, Material.is_approved.is_(False))
    return or_(base, and_(Material.is_approved.is_(False), Material.user_id == current_user.id))


@materials_bp.route('/')
def list():
    from datetime import datetime, timedelta
    from sqlalchemy import func

    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('q', '').strip()
    category = request.args.get('category', '')

    vf = _visible_materials_q()
    # ===== A方案：顶部统计小卡数据 =====
    total_materials = Material.query.filter(vf).count()
    total_downloads = db.session.query(
        db.func.coalesce(func.sum(Material.downloads), 0)
    ).filter(vf).scalar()
    # 本周新增
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_new = Material.query.filter(Material.created_at >= week_ago).filter(vf).count()
    # 评分Top3（取有评分的，按平均分+评论数排序）
    all_materials = Material.query.filter(vf).all()
    rated = [(m, m.avg_rating, m.review_count) for m in all_materials if m.avg_rating > 0]
    rated.sort(key=lambda x: (x[1], x[2]), reverse=True)
    top_rated = rated[:3]

    query = Material.query.filter(vf)
    if keyword:
        query = query.filter(Material.title.contains(keyword))
    if category:
        query = query.filter_by(category=category)
    pagination = query.order_by(Material.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)
    return render_template('materials_list.html', materials=pagination.items,
                           pagination=pagination, keyword=keyword,
                           category=category,
                           total_materials=total_materials,
                           total_downloads=total_downloads,
                           week_new=week_new,
                           top_rated=top_rated)


@materials_bp.route('/<int:id>')
def detail(id):
    material = Material.query.get_or_404(id)
    if not material.is_approved:
        if not current_user.is_authenticated:
            abort(403)
        if not (current_user.id == material.user_id or current_user.is_admin()):
            abort(403)
    material.views += 1  # 浏览量 +1
    db.session.commit()
    reviews = MaterialReview.query.filter_by(material_id=id)\
        .order_by(MaterialReview.created_at.desc()).all()
    return render_template('materials_detail.html', material=material, reviews=reviews)


@materials_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '')
        description = request.form.get('description', '').strip()
        file = request.files.get('file')

        if not title or not category:
            flash('请填写标题和分类。', 'error')
            return render_template('materials_upload.html')
        if not file or file.filename == '':
            flash('请选择要上传的文件。', 'error')
            return render_template('materials_upload.html')

        from forms import allowed_file, get_file_type
        if not allowed_file(file.filename):
            flash('不支持的文件格式。', 'error')
            return render_template('materials_upload.html')

        # ====== 内容审核（资料：标题+描述+原始文件名，不扫文件字节）======
        check = moderate_text(
            f"{title}\n{description}\n文件名：{file.filename}",
            context_type='material_desc',
        )
        if check['reject']:
            flash(f"上传失败：{check['reason']}", 'error')
            return render_template('materials_upload.html')

        from storage import save_file
        file_key = save_file(file, file.filename)
        file_type = get_file_type(file.filename)
        file_size = 0
        try:
            file.seek(0, 2)
            file_size = file.tell()
        except Exception:
            pass

        material = Material(
            title=title,
            description=description,
            category=category,
            file_key=file_key,
            file_name=file.filename,
            file_type=file_type,
            file_size=file_size,
            user_id=current_user.id,
            is_approved=(check['level'] == 'pass'),
            moderation_note=(check['reason'][:500] if check['level'] == 'warn' else ''),
        )
        db.session.add(material)
        if check['level'] == 'pass':
            current_user.add_points(5)  # 上传资料奖励：+5
        db.session.commit()
        if check['level'] == 'warn':
            flash('资料已提交，内容正在人工审核中（一般 24 小时内处理），审核通过后展示并奖励积分。', 'warning')
        else:
            flash('资料上传成功！+5 积分 📚', 'success')
        return redirect(url_for('materials.detail', id=material.id))
    return render_template('materials_upload.html')


@materials_bp.route('/<int:id>/review', methods=['POST'])
@login_required
def review(id):
    material = Material.query.get_or_404(id)
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()

    if not rating or rating < 1 or rating > 5:
        flash('请给出评分（1-5分）。', 'error')
        return redirect(url_for('materials.detail', id=id))

    existing = MaterialReview.query.filter_by(
        material_id=id, user_id=current_user.id).first()
    if existing:
        flash('您已经评价过这份资料了。', 'warning')
        return redirect(url_for('materials.detail', id=id))

    review = MaterialReview(
        material_id=id, user_id=current_user.id,
        rating=rating, comment=comment
    )
    db.session.add(review)

    if material.user_id != current_user.id:
        notif = Notification(
            user_id=material.user_id,
            type='review',
            title='资料收到新评价',
            content=f'{current_user.username} 对你的资料《{material.title}》给出了 {rating} 分评价。',
            link=url_for('materials.detail', id=id)
        )
        db.session.add(notif)

    db.session.commit()
    flash('评价成功！', 'success')
    return redirect(url_for('materials.detail', id=id))


@materials_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    material = Material.query.get_or_404(id)
    if material.user_id != current_user.id:
        flash('只有上传者可以删除该资料。', 'error')
        return redirect(url_for('materials.detail', id=id))
    from storage import delete_file
    if material.file_key:
        delete_file(material.file_key)
    MaterialReview.query.filter_by(material_id=id).delete()
    MaterialFavorite.query.filter_by(material_id=id).delete()
    db.session.delete(material)
    db.session.commit()
    flash('资料已删除。', 'success')
    return redirect(url_for('materials.list'))


@materials_bp.route('/<int:id>/favorite', methods=['POST'])
@login_required
def favorite(id):
    """资料收藏/取消收藏（AJAX）"""
    material = Material.query.get_or_404(id)
    existing = MaterialFavorite.query.filter_by(material_id=id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'status': 'unfavorited'})
    fav = MaterialFavorite(material_id=id, user_id=current_user.id)
    db.session.add(fav)
    db.session.commit()
    return jsonify({'status': 'favorited'})
