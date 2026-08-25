"""用户工作台路由：「我的收藏」统一中心（帖子/资料/二手 三类聚合）"""

from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from models import (
    PostFavorite, MaterialFavorite, TextbookFavorite,
    Post, Material, Textbook,
)

user_bp = Blueprint('user', __name__, url_prefix='/my')


@user_bp.route('/favorites')
@login_required
def favorites():
    """
    统一收藏中心。
    Query: ?tab=posts|materials|textbooks（默认 posts）
    返回：3 个渐变统计卡 + Tab 切换 + 对应类别的收藏列表（卡片式展示）
    """
    allowed_tabs = {'posts', 'materials', 'textbooks'}
    tab = request.args.get('tab', 'posts').strip()
    if tab not in allowed_tabs:
        tab = 'posts'

    uid = current_user.id

    # ===== 三个收藏的数量统计 =====
    cnt_posts = PostFavorite.query.filter_by(user_id=uid).count()
    cnt_materials = MaterialFavorite.query.filter_by(user_id=uid).count()
    cnt_textbooks = TextbookFavorite.query.filter_by(user_id=uid).count()

    # ===== 取当前 Tab 的收藏列表（12 条一页）=====
    page = request.args.get('page', 1, type=int)
    items = []
    pagination = None

    if tab == 'posts':
        # 收藏的帖子：按收藏时间倒序（取 Post 对象）
        favs_q = (PostFavorite.query
                  .filter_by(user_id=uid)
                  .join(Post, PostFavorite.post_id == Post.id)
                  .order_by(PostFavorite.created_at.desc()))
        pagination = favs_q.paginate(page=page, per_page=12, error_out=False)
        for fav in pagination.items:
            p = fav.post
            items.append({
                'kind': 'post',
                'obj': p,
                'id': p.id,
                'title': p.title,
                'subtitle': f'{p.category.name if p.category else "未分类"} · {p.comment_count} 评论 · {p.like_count} 赞',
                'desc': (p.content or '')[:140],
                'href': f'/forum/post/{p.id}',
                'created_at': fav.created_at,
            })

    elif tab == 'materials':
        favs_q = (MaterialFavorite.query
                  .filter_by(user_id=uid)
                  .join(Material, MaterialFavorite.material_id == Material.id)
                  .order_by(MaterialFavorite.created_at.desc()))
        pagination = favs_q.paginate(page=page, per_page=12, error_out=False)
        for fav in pagination.items:
            m = fav.material
            ft = (m.file_type or 'other').upper()
            size_mb = round((m.file_size or 0) / 1024 / 1024, 1) if m.file_size else 0
            items.append({
                'kind': 'material',
                'obj': m,
                'id': m.id,
                'title': m.title,
                'subtitle': f'{m.category} · {ft}'
                          + (f' · {size_mb}MB' if size_mb else '')
                          + (f' · 评分 {m.avg_rating}' if m.avg_rating else ''),
                'desc': (m.description or '')[:140] or m.file_name or '',
                'href': f'/materials/{m.id}',
                'created_at': fav.created_at,
            })

    else:  # textbooks
        favs_q = (TextbookFavorite.query
                  .filter_by(user_id=uid)
                  .join(Textbook, TextbookFavorite.textbook_id == Textbook.id)
                  .order_by(TextbookFavorite.created_at.desc()))
        pagination = favs_q.paginate(page=page, per_page=12, error_out=False)
        for fav in pagination.items:
            t = fav.textbook
            status_label = {'available': '在售', 'reserved': '预留', 'sold': '已售'}.get(t.trade_status, t.trade_status)
            items.append({
                'kind': 'textbook',
                'obj': t,
                'id': t.id,
                'title': t.title,
                'subtitle': f'{t.category} · {t.condition} · ¥{t.price:.0f} · {status_label}',
                'desc': (t.description or '')[:140],
                'cover': t.cover_image,
                'href': f'/textbook/{t.id}',
                'created_at': fav.created_at,
            })

    return render_template(
        'user_favorites.html',
        tab=tab,
        items=items,
        pagination=pagination,
        cnt_posts=cnt_posts,
        cnt_materials=cnt_materials,
        cnt_textbooks=cnt_textbooks,
    )
