"""学习资料路由"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Material, MaterialReview, Notification

materials_bp = Blueprint('materials', __name__, url_prefix='/materials')


@materials_bp.route('/')
def list():
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    query = Material.query
    if keyword:
        query = query.filter(Material.title.contains(keyword))
    if category:
        query = query.filter_by(category=category)
    pagination = query.order_by(Material.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)
    return render_template('materials_list.html', materials=pagination.items,
                           pagination=pagination, keyword=keyword,
                           category=category)


@materials_bp.route('/<int:id>')
def detail(id):
    material = Material.query.get_or_404(id)
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
            user_id=current_user.id
        )
        db.session.add(material)
        db.session.commit()
        flash('资料上传成功！', 'success')
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
    db.session.delete(material)
    db.session.commit()
    flash('资料已删除。', 'success')
    return redirect(url_for('materials.list'))
