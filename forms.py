"""表单校验辅助函数"""

import re


def validate_username(username):
    """校验用户名：3-20位，字母数字下划线"""
    if not username or len(username) < 3 or len(username) > 20:
        return False, '用户名为 3-20 个字符'
    if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fff]+$', username):
        return False, '用户名只能包含字母、数字、下划线或中文'
    return True, ''


def validate_email(email):
    """校验邮箱格式"""
    if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False, '请输入有效的邮箱地址'
    return True, ''


def validate_password(password):
    """校验密码：至少6位"""
    if not password or len(password) < 6:
        return False, '密码至少需要 6 个字符'
    return True, ''


def validate_title(title):
    """校验标题"""
    if not title or len(title.strip()) < 2:
        return False, '标题至少需要 2 个字符'
    if len(title) > 200:
        return False, '标题不能超过 200 个字符'
    return True, ''


def validate_content(content):
    """校验内容"""
    if not content or len(content.strip()) < 2:
        return False, '内容至少需要 2 个字符'
    return True, ''


ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
    'txt', 'md', 'jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'rar'
}

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def allowed_image_file(filename):
    """检查是否为允许的图片格式"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def get_file_type(filename):
    """根据扩展名返回文件类型"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
        return 'image'
    if ext == 'pdf':
        return 'pdf'
    if ext in ('doc', 'docx'):
        return 'word'
    if ext in ('ppt', 'pptx'):
        return 'ppt'
    if ext in ('xls', 'xlsx'):
        return 'excel'
    if ext in ('txt', 'md'):
        return 'text'
    return 'other'
