"""校桥 CampusBridge 数据库模型"""

from datetime import datetime, timedelta

# 中国时区偏移 UTC+8
CHINA_TZ = timedelta(hours=8)
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(UserMixin, db.Model):
    """用户"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' | 'admin'
    avatar = db.Column(db.String(256))
    bio = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    materials = db.relationship('Material', backref='author', lazy='dynamic')
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    competitions = db.relationship('Competition', backref='owner', lazy='dynamic')
    textbooks = db.relationship('Textbook', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def get_friends(self):
        """获取所有已接受的好友列表（按用户名排序）"""
        sent = FriendRequest.query.filter_by(
            sender_id=self.id, status='accepted'
        ).all()
        received = FriendRequest.query.filter_by(
            receiver_id=self.id, status='accepted'
        ).all()
        friends = []
        seen = set()
        for r in sent:
            if r.receiver_id not in seen:
                seen.add(r.receiver_id)
                friends.append(r.receiver)
        for r in received:
            if r.sender_id not in seen:
                seen.add(r.sender_id)
                friends.append(r.sender)
        friends.sort(key=lambda u: u.username.lower())
        return friends

    def get_friend_count(self):
        """好友数量（直接 COUNT 查询，不加载完整列表）"""
        sent_count = FriendRequest.query.filter_by(
            sender_id=self.id, status='accepted'
        ).count()
        received_count = FriendRequest.query.filter_by(
            receiver_id=self.id, status='accepted'
        ).count()
        # 如果互相发送过请求都 accepted，去重：只统计唯一的对方 user_id
        sent_ids = {r.receiver_id for r in FriendRequest.query.filter_by(
            sender_id=self.id, status='accepted'
        ).with_entities(FriendRequest.receiver_id).all()}
        received_ids = {r.sender_id for r in FriendRequest.query.filter_by(
            receiver_id=self.id, status='accepted'
        ).with_entities(FriendRequest.sender_id).all()}
        return len(sent_ids | received_ids)

    def is_friend_with(self, user_id):
        """检查是否与某用户是好友"""
        return FriendRequest.query.filter(
            ((FriendRequest.sender_id == self.id) & (FriendRequest.receiver_id == user_id)) |
            ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == self.id)),
            FriendRequest.status == 'accepted'
        ).first() is not None

    def get_friend_request_status(self, user_id):
        """查看与另一用户的好友关系状态: None/pending_sent/pending_received/accepted/rejected"""
        req = FriendRequest.query.filter(
            ((FriendRequest.sender_id == self.id) & (FriendRequest.receiver_id == user_id)) |
            ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == self.id))
        ).first()
        if not req:
            return None
        if req.status == 'accepted':
            return 'accepted'
        if req.status == 'rejected':
            return 'rejected'
        if req.sender_id == self.id:
            return 'pending_sent'
        return 'pending_received'

    def get_pending_requests(self):
        """获取收到的好友请求（待处理）"""
        return FriendRequest.query.filter_by(
            receiver_id=self.id, status='pending'
        ).order_by(FriendRequest.created_at.desc()).all()


class ForumCategory(db.Model):
    """论坛分区"""
    __tablename__ = 'forum_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    icon = db.Column(db.String(50))
    sort_order = db.Column(db.Integer, default=0)

    posts = db.relationship('Post', backref='category', lazy='dynamic')


class Post(db.Model):
    """论坛帖子"""
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_categories.id'), nullable=False)
    views = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    comments = db.relationship('Comment', backref='post', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='Comment.created_at')
    likes = db.relationship('PostLike', backref='post', lazy='dynamic',
                            cascade='all, delete-orphan')
    favorites = db.relationship('PostFavorite', backref='post', lazy='dynamic',
                                cascade='all, delete-orphan')
    images = db.relationship('PostImage', backref='post', lazy='dynamic',
                             cascade='all, delete-orphan', order_by='PostImage.sort_order')

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()


class PostImage(db.Model):
    """帖子图片"""
    __tablename__ = 'post_images'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    """帖子回复"""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PostLike(db.Model):
    """帖子点赞"""
    __tablename__ = 'post_likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='uq_user_post_like'),)


class PostFavorite(db.Model):
    """帖子收藏"""
    __tablename__ = 'post_favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='uq_user_post_favorite'),)


class Material(db.Model):
    """学习资料"""
    __tablename__ = 'materials'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)  # 课件/试题/笔记/其他
    file_key = db.Column(db.String(500), nullable=False)  # 存储 key
    file_name = db.Column(db.String(200))  # 原始文件名
    file_type = db.Column(db.String(20))  # pdf/doc/ppt/image/other
    file_size = db.Column(db.Integer, default=0)  # 字节
    views = db.Column(db.Integer, default=0)       # 浏览量（页面访问次数）
    downloads = db.Column(db.Integer, default=0)   # 下载量（实际下载次数）
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviews = db.relationship('MaterialReview', backref='material', lazy='dynamic',
                              cascade='all, delete-orphan')

    @property
    def avg_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    @property
    def review_count(self):
        return self.reviews.count()


class MaterialReview(db.Model):
    """资料评价"""
    __tablename__ = 'material_reviews'

    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviewer = db.relationship('User', backref='reviews')

    __table_args__ = (db.UniqueConstraint('material_id', 'user_id', name='uq_user_material_review'),)


class Competition(db.Model):
    """竞赛招募"""
    __tablename__ = 'competitions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    comp_type = db.Column(db.String(50), nullable=False)  # 学科竞赛/创新创业/文艺体育/其他
    deadline = db.Column(db.Date)
    team_size = db.Column(db.Integer, default=0)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='open')  # open/closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='competition', lazy='dynamic',
                                   cascade='all, delete-orphan')
    # uselist=False 是一对一/多对一关系，不能使用 lazy='dynamic'，必须使用默认/select 加载器
    group = db.relationship('TeamGroup', backref='competition', uselist=False,
                            cascade='all, delete-orphan')
    conversation_messages = db.relationship('ConversationMessage', backref='competition',
                                            lazy='dynamic', cascade='all, delete-orphan')

    @property
    def application_count(self):
        return self.applications.count()

    @property
    def approved_count(self):
        return self.applications.filter_by(status='approved').count()


class Application(db.Model):
    """组队申请"""
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applicant = db.relationship('User', backref='applications')
    conversation_messages = db.relationship('ConversationMessage', backref='application',
                                            lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (db.UniqueConstraint('competition_id', 'user_id', name='uq_comp_user_apply'),)


class ConversationMessage(db.Model):
    """竞赛组队对话：申请人与发起人之间的多轮私聊消息
    每条消息都关联到具体的申请(application)，便于发起人为每个申请人维护独立对话。"""
    __tablename__ = 'conversation_messages'

    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_conversation_messages')

    def to_dict(self, current_user_id=None):
        return {
            'id': self.id,
            'competition_id': self.competition_id,
            'application_id': self.application_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.username if self.sender else None,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_self': self.sender_id == current_user_id,
        }


class TeamGroup(db.Model):
    """竞赛交流群：一个竞赛对应一个交流群，成员为发起人及所有已通过审核的申请人。"""
    __tablename__ = 'team_groups'

    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship('GroupMember', backref='group', lazy='dynamic',
                               cascade='all, delete-orphan')
    messages = db.relationship('GroupMessage', backref='group', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='GroupMessage.created_at')

    @property
    def member_count(self):
        return self.members.count()


class GroupMember(db.Model):
    """交流群成员"""
    __tablename__ = 'group_members'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('team_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='group_memberships')

    __table_args__ = (db.UniqueConstraint('group_id', 'user_id', name='uq_group_user'),)


class GroupMessage(db.Model):
    """交流群消息"""
    __tablename__ = 'group_messages'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('team_groups.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_group_messages')

    def to_dict(self, current_user_id=None):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.username if self.sender else None,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_self': self.sender_id == current_user_id,
        }


class Textbook(db.Model):
    """二手闲置物品（泛化，不再限于教材）"""
    __tablename__ = 'textbooks'

    # 物品类型可选值
    CATEGORIES = ['书籍', '数码产品', '服饰鞋包', '生活用品', '运动器材', '其他']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(30), default='书籍', nullable=False)  # 物品类型
    author = db.Column(db.String(100))  # 品牌/作者（可选）
    publisher = db.Column(db.String(100))
    price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(20), nullable=False)  # 全新/良好/一般/较差
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(500))  # 封面图 storage key（单张）
    description_images = db.Column(db.Text)  # 描述图 storage keys（多张，逗号分隔）
    trade_status = db.Column(db.String(20), default='available')  # available/reserved/sold
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship('TextbookMessage', backref='textbook', lazy='dynamic',
                               cascade='all, delete-orphan')


class TextbookMessage(db.Model):
    """教材私信"""
    __tablename__ = 'textbook_messages'

    id = db.Column(db.Integer, primary_key=True)
    textbook_id = db.Column(db.Integer, db.ForeignKey('textbooks.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')


class ChatMessage(db.Model):
    """好友一对一私聊消息"""
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_chat_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_chat_messages')

    def to_dict(self, current_user_id=None):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'sender_name': self.sender.username if self.sender else None,
            'content': self.content,
            'created_at': (self.created_at + CHINA_TZ).strftime('%m-%d %H:%M'),
            'is_self': self.sender_id == current_user_id,
        }


class ChatGroup(db.Model):
    """聊天群组"""
    __tablename__ = 'chat_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by], backref='created_groups')
    members = db.relationship('ChatGroupMember', backref='group', lazy='dynamic',
                               cascade='all, delete-orphan')
    messages = db.relationship('ChatGroupMessage', backref='group', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='ChatGroupMessage.created_at')

    @property
    def member_count(self):
        return self.members.count()


class ChatGroupMember(db.Model):
    """群组成员"""
    __tablename__ = 'chat_group_members'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('chat_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='chat_group_memberships')

    __table_args__ = (db.UniqueConstraint('group_id', 'user_id', name='uq_chat_group_user'),)


class ChatGroupMessage(db.Model):
    """群聊消息"""
    __tablename__ = 'chat_group_messages'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('chat_groups.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_group_chat_messages')

    def to_dict(self, current_user_id=None):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.username if self.sender else None,
            'content': self.content,
            'created_at': (self.created_at + CHINA_TZ).strftime('%m-%d %H:%M'),
            'is_self': self.sender_id == current_user_id,
        }


class Notification(db.Model):
    """消息通知"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # comment/like/application/message/system
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    link = db.Column(db.String(200))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')


class FriendRequest(db.Model):
    """好友请求"""
    __tablename__ = 'friend_requests'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/accepted/rejected
    message = db.Column(db.String(200))  # 申请附言
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_friend_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_friend_requests')

    __table_args__ = (
        db.UniqueConstraint('sender_id', 'receiver_id', name='uq_friend_request'),
    )
