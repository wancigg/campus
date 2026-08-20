# 校桥 CampusBridge - 校园资源交换与交流平台

面向全校学生的资源共享社区，整合学习资料共享、校园论坛、竞赛组队、二手教材四大核心功能。

## 技术栈

- **后端**：Flask 3.0 + Jinja2 + Flask-SQLAlchemy
- **前端**：HTML5 + Tailwind CSS + 原生 JavaScript
- **数据库**：MySQL 8.0
- **运行环境**：Python 3.10+

## 快速开始

### 1. 配置数据库

编辑 `.env` 文件，填写你的 MySQL 连接信息：

```env
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=campus_bridge
SECRET_KEY=your-secret-key
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动应用

```bash
python app.py
```

首次运行将自动创建数据库表，并初始化：

- **管理员账号**：admin / admin123（请尽快修改密码）
- **论坛分区**：学习交流、校园生活、技术讨论、求职升学、闲聊灌水

### 4. 访问

打开浏览器访问 http://127.0.0.1:5000

## 项目结构

```
├── app.py                 # Flask 主入口
├── config.py              # 配置文件
├── extensions.py          # Flask 扩展（db、login）
├── models.py              # 数据库模型
├── storage.py             # 文件存储（本地 + COS）
├── decorators.py          # 权限装饰器
├── forms.py               # 表单校验
├── routes_auth.py         # 用户认证
├── routes_materials.py    # 学习资料
├── routes_forum.py        # 校园论坛
├── routes_competition.py  # 竞赛组队
├── routes_textbook.py     # 二手教材
├── routes_message.py      # 消息通知
├── routes_admin.py        # 后台管理
├── templates/             # Jinja2 模板
├── static/                # 静态资源
├── uploads/               # 本地上传目录
├── requirements.txt       # Python 依赖
├── .env                   # 环境变量
└── README.md              # 本文件
```

## 功能模块

| 模块 | 功能 |
|------|------|
| 用户认证 | 注册、登录、登出、RBAC 权限（普通用户/管理员） |
| 学习资料 | 上传、分类浏览、关键词检索、在线预览、下载、评分评价 |
| 校园论坛 | 分区讨论、发帖、回复、点赞、收藏、关键词搜索 |
| 竞赛组队 | 发布招募、浏览、申请加入、队长审核管理 |
| 二手教材 | 发布闲置、搜索、私信沟通、交易状态跟踪 |
| 消息通知 | 站内通知覆盖评论、点赞、申请、私信等场景 |
| 后台管理 | 用户/资料/帖子/教材管理、分区管理 |
