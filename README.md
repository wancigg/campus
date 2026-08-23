# 校桥 CampusBridge - 校园资源交换与交流平台

面向全校学生的资源共享社区，整合**学习资料共享、校园论坛（AI 智能摘要）、竞赛组队、二手教材、社交好友、即时聊天**六大核心功能。

---

## ✨ 特色功能

- 🤖 **AI 智能摘要**：论坛帖子一键生成摘要、核心观点、建议标签（基于 DeepSeek Chat API）
- 👥 **社交好友**：发现同校同学、互加好友、个人主页
- 💬 **即时聊天**：单聊、群聊、创建群组
- 📚 **学习资料**：上传分类、在线预览、下载评分
- 🗣️ **校园论坛**：分区讨论、点赞收藏、回复搜索
- 🏆 **竞赛组队**：发布招募、申请加入、队长审核
- 📖 **二手教材**：闲置发布、私信沟通、状态跟踪
- 🔔 **消息通知**：覆盖评论、点赞、申请、私信全场景
- 🛡️ **后台管理**：RBAC 权限、用户/内容/分区管理

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | Flask 3.1 + Jinja2 + Flask-SQLAlchemy 2.0 |
| **前端样式** | HTML5 + Tailwind CSS + 原生 JavaScript |
| **数据库** | MySQL 5.7+ / MariaDB 5.5+（兼容 CentOS 7 自带 MariaDB） |
| **AI 集成** | DeepSeek Chat API（deepseek-chat 模型） |
| **文件存储** | 本地磁盘 / 腾讯云 COS（可切换） |
| **生产部署** | Gunicorn 23 + Nginx + systemd |
| **公网穿透** | ngrok（可选，用于演示/远程访问） |
| **Python 版本** | Python 3.9+（已验证 3.9.20 完美运行） |

---

## 🚀 快速开始（本地开发）

### 1. 配置环境变量

复制 `.env.example` 为 `.env`，填入真实值：

```bash
cp .env.example .env   # Windows: 手动复制改名
```

编辑 `.env`：

```env
# ===== 必配：数据库 =====
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=campus_bridge

# ===== 必配：Flask =====
SECRET_KEY=change-me-to-random-string

# ===== 可选：腾讯云 COS（不填自动用本地存储）=====
COS_SECRET_ID=
COS_SECRET_KEY=
COS_REGION=ap-guangzhou
COS_BUCKET=

# ===== 可选：AI 摘要（不填论坛 AI 按钮自动隐藏）=====
# 申请地址：https://platform.deepseek.com
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx

# ===== 可选：上传限制 =====
MAX_CONTENT_LENGTH=50
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

> ⚠️ **CentOS 7 注意**：系统自带 OpenSSL 1.0.2 不兼容 urllib3 2.x，需锁定版本：
> ```bash
> pip install "urllib3<=1.26.18" "requests<=2.27.1"
> ```

### 3. 初始化数据库

```bash
# 方式一：自动建表 + 初始化种子数据（推荐）
python seed_data.py

# 方式二：用 SQL 脚本手动导入
mysql -u root -p campus_bridge < db_init.sql
```

初始化后默认账号：
- **管理员**：`admin` / `admin123`（请尽快修改密码）
- **普通用户**：自行注册
- **论坛分区**：学习交流、校园生活、技术讨论、求职升学、闲聊灌水

### 4. 启动开发服务器

```bash
python app.py
```

### 5. 访问

浏览器打开 http://127.0.0.1:5000

---

## 📦 功能模块详解

| 模块 | 蓝图 | 路由文件 | 模板 | 说明 |
|------|------|----------|------|------|
| 用户认证 | `auth_bp` | [routes_auth.py](routes_auth.py) | login.html, register.html, student.html, user_profile.html | 注册/登录/学生认证/个人主页 |
| 学习资料 | `materials_bp` | [routes_materials.py](routes_materials.py) | materials_list.html, materials_detail.html, materials_upload.html | 上传/浏览/预览/下载/评分 |
| 校园论坛 | `forum_bp` | [routes_forum.py](routes_forum.py) | forum_index.html, forum_category.html, forum_edit.html, forum_post.html | 分区/发帖/回复/点赞/**AI 摘要** |
| 竞赛组队 | `competition_bp` | [routes_competition.py](routes_competition.py) | competition_list.html, competition_detail.html, competition_edit.html | 招募/申请/审核/成员管理 |
| 二手教材 | `textbook_bp` | [routes_textbook.py](routes_textbook.py) | textbook_list.html, textbook_detail.html, textbook_edit.html | 发布/搜索/私信/交易跟踪 |
| 消息通知 | `message_bp` | [routes_message.py](routes_message.py) | message_list.html | 系统通知集中查看 |
| 社交好友 | `social_bp` | [routes_social.py](routes_social.py) | social_discover.html, social_friends.html | 发现同学/加好友/好友列表 |
| 即时聊天 | `chat_bp` | [routes_chat.py](routes_chat.py) | chat_list.html, chat_friend.html, chat_group.html, chat_group_create.html | 单聊/群聊/创建群组 |
| 后台管理 | `admin_bp` | [routes_admin.py](routes_admin.py) | admin_dashboard.html | 用户/内容/分区管理 |

---

## 📁 项目结构

```
项目/
├── app.py                  # Flask 主入口，注册 9 个蓝图
├── config.py               # 配置加载（从 .env 读取环境变量）
├── extensions.py           # Flask 扩展初始化（db、login_manager）
├── models.py               # SQLAlchemy 数据库模型（User、Post 等）
├── storage.py              # 文件存储抽象层（本地/COS 切换）
├── decorators.py           # 权限装饰器（@admin_required 等）
├── forms.py                # WTForms 表单校验
├── seed_data.py            # 数据库初始化 + 种子数据脚本
├── db_init.sql             # 数据库建表 SQL（备选）
│
├── routes_auth.py          # 用户认证蓝图
├── routes_materials.py     # 学习资料蓝图
├── routes_forum.py         # 校园论坛蓝图（含 AI 摘要接口）
├── routes_competition.py   # 竞赛组队蓝图
├── routes_textbook.py      # 二手教材蓝图
├── routes_message.py       # 消息通知蓝图
├── routes_admin.py         # 后台管理蓝图
├── routes_social.py        # 社交好友蓝图
├── routes_chat.py          # 即时聊天蓝图
│
├── templates/              # Jinja2 模板（27 个页面）
│   ├── base.html           # 公共基模板（导航栏 + 页脚）
│   ├── index.html          # 首页
│   ├── login.html / register.html
│   ├── student.html        # 学生认证
│   ├── user_profile.html   # 个人主页
│   ├── forum_*.html        # 论坛（含 AI 摘要弹窗 forum_post.html）
│   ├── materials_*.html    # 学习资料
│   ├── competition_*.html  # 竞赛组队
│   ├── textbook_*.html     # 二手教材
│   ├── social_*.html       # 社交好友
│   ├── chat_*.html         # 即时聊天（单聊/群聊）
│   ├── message_list.html   # 消息通知
│   └── admin_dashboard.html# 后台管理
│
├── static/                 # 静态资源
│   ├── css/style.css       # 自定义样式
│   └── js/
│       ├── main.js         # 通用交互逻辑
│       └── animations.js   # 页面动画效果
│
├── uploads/                # 本地上传目录（自动创建，不提交 Git）
├── .env                    # 真实环境变量（不提交 Git，已在 .gitignore）
├── .env.example            # 环境变量模板（含 AI 配置说明）
├── .gitignore
├── requirements.txt        # Python 依赖清单
├── package.json            # Node 辅助工具（PPT 生成等，可选）
└── README.md               # 本文件
```

---

## 🤖 AI 摘要功能说明

论坛帖子详情页右上角有蓝色 **「AI 摘要」** 按钮，点击后：

1. 前端调用 `/post/<id>/ai-summary` 接口
2. 后端拼接待摘要内容（标题 + 正文），请求 DeepSeek Chat API
3. 提示词要求模型输出三段式结构：**摘要 + 核心观点 + 建议标签**
4. 前端以弹窗形式渲染 Markdown 风格结果

### 配置步骤

1. 去 [https://platform.deepseek.com](https://platform.deepseek.com) 注册并创建 API Key
2. 把 Key 填入 `.env` 的 `DEEPSEEK_API_KEY`
3. 重启 Flask 服务即可（不填 Key 时按钮自动隐藏不报错）

---

## 🏭 生产部署（CentOS 7 方案）

已验证可运行方案：Python 3.9.20 + Gunicorn 23 + Nginx + MariaDB 5.5

### 1. 代码部署路径

```
/opt/campus-bridge/
├── app.py  routes_*.py  models.py  ...（项目文件）
├── .env           # 生产环境变量（含真实 DEEPSEEK_API_KEY）
└── venv/          # Python 虚拟环境
```

### 2. Gunicorn 启动命令

```bash
cd /opt/campus-bridge
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:8000 --timeout 120 "app:create_app()"
```

### 3. Systemd 服务（`/etc/systemd/system/campus-bridge.service`）

```ini
[Unit]
Description=CampusBridge Flask App
After=network.target mariadb.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/campus-bridge
Environment="PATH=/opt/campus-bridge/venv/bin"
ExecStart=/opt/campus-bridge/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 --timeout 120 --access-logfile /var/log/campus-bridge-access.log --error-logfile /var/log/campus-bridge-error.log "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

管理命令：
```bash
systemctl daemon-reload
systemctl enable campus-bridge
systemctl start campus-bridge
systemctl status campus-bridge
```

### 4. Nginx 反向代理（`/etc/nginx/conf.d/campus-bridge.conf`）

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location /static/ {
        alias /opt/campus-bridge/static/;
        expires 7d;
    }

    location /uploads/ {
        alias /opt/campus-bridge/uploads/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

### 5. ngrok 公网穿透（可选，用于演示）

安装 ngrok 并配置 Authtoken 后，创建 systemd 服务后台常驻：

```ini
# /etc/systemd/system/ngrok.service
[Unit]
Description=ngrok HTTP Tunnel for CampusBridge
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/ngrok http 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

查询当前公网 URL：
```bash
curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "import sys,json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])"
```

---

## 🔒 安全注意事项

1. **不要提交真实密钥**：`.env` 已在 `.gitignore`，`.env.example` 只放占位符
2. **修改默认密码**：生产环境务必修改 `admin/admin123` 默认管理员密码
3. **更换 SECRET_KEY**：用随机字符串替换开发用的固定密钥
4. **限制上传目录**：Nginx 中 `uploads/` 不要开启 PHP/脚本执行权限
5. **API Key 安全**：DeepSeek Key 定期轮换，不要硬编码在代码里

---

## 📝 TODO / 后续可扩展

- [ ] WebSocket 改造聊天模块（当前为轮询）
- [ ] 接入微信/QQ 第三方登录
- [ ] 资料全文检索（Elasticsearch / Whoosh）
- [ ] 管理员操作审计日志
- [ ] 移动端响应式优化（当前已可用，可进一步打磨）

---

## 📄 License

校园项目内部使用，代码仅供学习交流。
