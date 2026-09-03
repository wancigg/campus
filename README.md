# 校桥 CampusBridge · 校园资源交换与交流平台

> 面向全校学生的一站式资源共享社区：**学习资料 / 校园论坛 / 竞赛组队 / 二手教材 / 社交好友 / 即时聊天** 六大核心模块，整合 **AI 摘要（DeepSeek）**、**用户积分等级阶梯**、**4 类差异化页面布局范式**（淘宝橱窗 / 知乎信息流 / 瀑布流 / Trello 看板），内置自动建表与种子数据，开箱即用。

---

## ✨ 核心亮点

### 🤖 AI 智能摘要
论坛帖子详情页右上角一键调用 DeepSeek Chat API，输出「**摘要 · 核心观点 · 建议标签**」三段式 Markdown 结果，未配置 API Key 时按钮自动隐藏不报错。

### 🎨 A + B 方案 UI 改版（2026-08 已上线）
**A 方案 · 首页信息架构重构**：Hero 大搜索条（含热门搜索胶囊）→ 平台数据大盘（6 张实时统计卡）→ 功能快捷入口（6 卡片）→ 精选竞赛 → 最新动态（双栏）
**B 方案 · 4 个列表页差异化布局范式**，答辩视觉更有层次：

| 模块 | 布局范式 | 特色 UI |
|---|---|---|
| 校园论坛 `/forum/` | **知乎式 2/3 + 1/3 双栏信息流** | 顶部 4 渐变统计卡 + 热门板块榜；左头像 + Lv.等级徽章；右栏活跃度进度条 Top3 |
| 学习资料 `/materials/` | **CSS columns-3 瀑布流** | 扩展名巨型彩色标签（PDF/DOC/PPT 分色）+ 5 角实心星评分 |
| 竞赛组队 `/competition/` | **Trello 式 3 列看板** | `招募中` / `满员` / `已截止` 三态动态分组 + 满员 -6° 红色印章 + 进度条 |
| 二手教材 `/textbook/` | **淘宝式橱窗** | 封面 + 价格红绿角标 + 卖家半透明悬浮条 + ❤ 💬 悬浮操作按钮 + 顶部 4 渐变统计卡 + 标签云 |

### 🛡️ 用户积分等级体系（10 级阶梯）
User 表按积分（points）从「萌新→新生→学弟学妹→学长学姐→优秀学子→校园达人→校园精英→校园领袖→校园传说→校桥大佬」，每个等级有独立颜色类徽章，通过 `user.get_level_info()` 渲染在个人主页、论坛帖子头像旁。

### 💬 即时聊天（含图片 & 文件上传）
单聊 / 群聊 / 创建群组，最新支持私聊上传图片（`/chat/upload` 接口，本地磁盘存储），消息气泡自动渲染图片卡片与文件下载按钮。

### 🔒 错误处理兜底
403 / 500 独立渐变错误页（不再伪装首页导致混淆路由）；404 自动跳到搜索结果页框架。

---

## 🛠️ 技术栈

| 层级 | 技术 |
|---|---|
| **后端框架** | Flask 3.1 + Jinja2 + Flask-SQLAlchemy 3.1 |
| **前端样式** | HTML5 + Tailwind CSS + 原生 JavaScript（`static/js/main.js` + `animations.js`） |
| **数据库** | **强制 MySQL 5.7+（单主库模式）**，启动期连接失败直接报错退出，不再提供 SQLite 自动降级。如需演示「主从复制」见 `scripts/deploy_mysql_ms_demo.sh` 一节（Flask 永远只写/读主库，从库用于 SHOW SLAVE STATUS 演示）。 |
| **AI 集成** | DeepSeek Chat API（deepseek-chat 模型，论坛 AI 摘要） |
| **文件存储** | 本地磁盘 `/uploads/`（默认）/ 腾讯云 COS（填 `.env` 自动切换） |
| **生产部署** | Gunicorn 23 + systemd（CentOS 7.4 已验证） |
| **Python 版本** | Python 3.9+（已验证 3.9.20） |

---

## 📦 数据库真实种子数据

执行 `seed_data.py` 后初始化（CentOS 7 服务器上已验证）：

| 表 | 条数 | 备注 |
|---|---|---|
| User | 21 | 管理员：`admin / admin123` |
| Material（学习资料） | 13 | 含 PDF/DOC 等示例文件元数据 |
| Post（论坛帖子） | 63 | 分区 5 类：学习交流 / 校园生活 / 技术讨论 / 求职升学 / 闲聊灌水 |
| Textbook（二手教材） | 15 | `trade_status`：available / reserved / sold |
| Competition（竞赛） | 8 | `status`：`open` × 7 + `closed` × 1；`deadline` 多在 2026-09/10；`team_size=0` 视作无限名额 |

---

## 🚀 快速开始（本地开发）

### 1. 配置环境变量
复制 `.env.example` 为 `.env`（Windows 下手动改名），填入真实值：
```env
# ===== MySQL 主库（必填；未填/连接失败直接报错退出；兼容旧键 MYSQL_*） =====
MYSQL_MASTER_HOST=127.0.0.1
MYSQL_MASTER_PORT=3306
MYSQL_MASTER_USER=root
MYSQL_MASTER_PASSWORD=your_password
MYSQL_MASTER_DATABASE=campus_bridge

# ===== Flask 密钥（生产必改） =====
SECRET_KEY=change-me-to-random-string

# ===== AI 摘要（不填论坛 AI 按钮自动隐藏）=====
# 申请：https://platform.deepseek.com
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx

# ===== 可选：腾讯云 COS（不填自动本地磁盘）=====
COS_SECRET_ID=
COS_SECRET_KEY=
COS_REGION=ap-guangzhou
COS_BUCKET=

# ===== 上传大小限制（MB）=====
MAX_CONTENT_LENGTH=50
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

> ⚠️ **CentOS 7 用户注意**：系统自带 OpenSSL 1.0.2 不兼容 urllib3 2.x，必须锁定版本：
> ```bash
> pip install "urllib3<=1.26.18" "requests<=2.27.1"
> ```

### 3. 初始化数据库 + 种子数据
```bash
python database/seed_data.py
```
脚本会自动执行：SQLAlchemy `db.create_all()` 建表 → 分区 / 管理员 / 示例资料 / 示例帖子 / 示例竞赛 / 示例二手 逐条插入。架构已移除 SQLite fallback，必须确保 `.env` 主库可连。

### 4. 启动开发服务器
```bash
python app.py
```
浏览器访问：**http://127.0.0.1:5000**

### 5. 开发调试：清空 Gunicorn 字节码缓存
任何 Python 代码改动后生产部署记得清 `__pycache__`：
```bash
find /opt/campus-bridge -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find /opt/campus-bridge -name "*.pyc" -delete 2>/dev/null
systemctl restart campus-bridge
```

---

## 🧩 9 个 Flask 蓝图模块

| 模块 | Blueprint | 路由文件 | 模板 | 说明 |
|---|---|---|---|---|
| 用户认证 | `auth_bp` | [routes_auth.py](routes_auth.py) | login.html / register.html / student.html / user_profile.html | 注册 / 登录 / 学生认证 / 个人主页 / 等级徽章 |
| 学习资料 | `materials_bp` | [routes_materials.py](routes_materials.py) | materials_list.html / materials_detail.html / materials_upload.html | 上传 / 分类 / 瀑布流展示 / 评分 / 下载 / 预览 |
| 校园论坛 | `forum_bp` | [routes_forum.py](routes_forum.py) | forum_index.html / forum_category.html / forum_edit.html / forum_post.html | 分区 / 发帖 / 回复 / 点赞 / **AI 摘要** / 等级徽章 |
| 竞赛组队 | `competition_bp` | [routes_competition.py](routes_competition.py) | competition_list.html / competition_detail.html / competition_edit.html | 招募 / 申请 / 审核 / **3 列看板（招募中·满员·已截止）** |
| 二手教材 | `textbook_bp` | [routes_textbook.py](routes_textbook.py) | textbook_list.html / textbook_detail.html / textbook_edit.html | 发布 / 淘宝式橱窗 / 交易状态跟踪（available / reserved / sold） |
| 消息通知 | `message_bp` | [routes_message.py](routes_message.py) | message_list.html | 评论 / 点赞 / 申请 / 私信 系统通知 |
| 社交好友 | `social_bp` | [routes_social.py](routes_social.py) | social_discover.html / social_friends.html | 发现同学 / 加好友 / 好友列表（注意 endpoint 前缀是 `social.*` 非 `chat.*`） |
| 即时聊天 | `chat_bp` | [routes_chat.py](routes_chat.py) | chat_list.html / chat_friend.html / chat_group.html / chat_group_create.html | 单聊 / 群聊 / **图片 & 文件上传卡片** |
| 后台管理 | `admin_bp` | [routes_admin.py](routes_admin.py) | admin_dashboard.html | RBAC 管理员权限（`@admin_required`）/ 用户 / 内容 / 分区管理 |

> 🔔 endpoint 小贴士：之前 A 方案首页大盘热修过两个错误 Blueprint：`chat.friend_list` → `social.friend_list`，`forum.post_detail` → `forum.post`（见 [index.html](templates/index.html) L236 / L416 / L462），不要写错。

---

## 📁 项目结构

```
项目/
├── app.py                   # Flask 主入口，create_app() + 注册 9 蓝图 + 自动建表迁移 + 403/404/500 错误页
├── config.py                # 配置加载（强制 MySQL 单主库；MYSQL_MASTER_* 优先、MYSQL_* 兼容旧部署）
├── extensions.py            # Flask 扩展初始化（db / login_manager）
├── models.py                # 10 个 SQLAlchemy 模型（User 10 级等级表 / Post 点赞收藏评论图片关系 / ...）
├── storage.py               # 文件存储抽象层（本地磁盘 ↔ 腾讯云 COS 可切换）
├── decorators.py            # 权限装饰器（@login_required / @admin_required）
├── forms.py                 # WTForms 表单校验
│
├── database/                # ⭐ 数据库类文件专属目录（见 refactor: 根目录整理）
│   ├── seed_data.py         # 自动建表 + 种子数据（真实部署 User=24 / Post=64 等）
│   └── db_init.sql          # 备用：MySQL 手工建表 SQL
│
├── routes_auth.py           # 用户认证
├── routes_materials.py      # 学习资料
├── routes_forum.py          # 校园论坛（含 /post/<id>/ai-summary AI 接口）
├── routes_competition.py    # 竞赛组队（3 态动态分组算法：status=closed OR deadline<today → closed；approved≥team_size → full）
├── routes_textbook.py       # 二手教材（5 统计卡 + 分类标签云）
├── routes_message.py        # 消息通知
├── routes_admin.py          # 后台管理
├── routes_social.py         # 社交好友
├── routes_chat.py           # 即时聊天（含图片上传接口 /chat/upload）
│
├── templates/               # 26 个 Jinja2 模板
│   ├── base.html            # 公共基模板（导航栏 logo 右侧搜索框必须包 form action=search）
│   ├── index.html           # 首页 A 方案（Hero 搜索条 + 大盘 6 卡 + 功能入口 + 最新动态）
│   ├── search.html          # 全站 4 类聚合搜索（帖子 / 资料 / 二手 / 用户）
│   ├── forum_index.html     # B 方案 · 知乎式双栏信息流（含 Lv.等级徽章）
│   ├── materials_list.html  # B 方案 · 瀑布流
│   ├── competition_list.html# B 方案 · Trello 3 列看板
│   ├── textbook_list.html   # B 方案 · 淘宝橱窗
│   └── ...（其余 18 个页面见 LS 目录）
│
├── static/
│   ├── css/style.css        # 自定义样式
│   └── js/
│       ├── main.js          # 通用交互（搜索框 / 悬浮按钮 / 弹窗）
│       └── animations.js    # 页面入场动画 / 数字滚动 / 进度条补帧
│
├── uploads/                 # 本地上传目录（自动创建，不提交 Git）
├── .env                     # 生产环境变量（不提交 Git，已在 .gitignore）
├── .env.example             # 环境变量模板
├── .gitignore
├── requirements.txt         # Python 依赖
├── package.json             # 可选：generate_ppt.js 答辩 PPT 生成工具
└── README.md                # 本文件
```

---

## 🤖 AI 摘要功能说明

论坛帖子详情页右上角蓝色「**AI 摘要**」按钮 → 前端调 `/post/<id>/ai-summary` → 后端拼接 `标题 + 正文` → 请求 DeepSeek Chat API → 模型输出三段式 Markdown → 前端弹窗渲染。

配置步骤：
1. [https://platform.deepseek.com](https://platform.deepseek.com) 注册 → 创建 API Key
2. `.env` 填 `DEEPSEEK_API_KEY=sk-...`
3. 重启 Flask（不填按钮自动隐藏，不影响其他功能）

---

## 🗄️ 数据库架构说明（单 MySQL 主库 + 可选 3307 演示型主从）

> 2026.09 架构升级：**移除了 SQLite 自动降级 / sync_database.py 回灌脚本**。
> 项目现在只支持「MySQL 单主库」，任何 `.env` 连接配置错误都会在启动期直接抛 `RuntimeError: MySQL 主库连接失败（已禁用 SQLite 降级）`，
> 避免「悄悄降级到 SQLite 结果大盘 count=0」一类生产事故。

### 1) Flask 生产永远只读写「主库 3306」
- `.env` 推荐填写 `MYSQL_MASTER_HOST/PORT/USER/PASSWORD/DATABASE`，同时兼容旧键 `MYSQL_*`
- `.env.example` 里还有可选的 `MYSQL_SLAVE_*`，只是部署从库时给脚本读取，**Flask 代码从不读取 MYSQL_SLAVE_*，不会把写请求打到从库**。

### 2) 演示型主从复制（答辩老师必看 Showstopper）
为了让答辩展示「主从复制 + binlog 同步」的真实机制，我们提供一套「同机 3307 从库」的一键部署脚本：
`scripts/deploy_mysql_ms_demo.sh`（MySQL 5.7 / 8.0 已适配；dry-run 模式先预览再执行）。

**执行步骤（在 hadoop101 `/opt/campus-bridge`）**：
```bash
# (可选) 0. 先 dry-run 预览 7 步会做什么 + CHANGE MASTER File/Pos 是怎么从 dump 头 22 行取出来的：
sudo bash scripts/deploy_mysql_ms_demo.sh --dry-run

# 1. 真实执行（在执行前确保 /opt/campus-bridge/.env 已填：MYSQL_MASTER_PASSWORD + MYSQL_REPL_PASSWORD）
sudo bash scripts/deploy_mysql_ms_demo.sh

# 2. 出问题或展示完毕想停掉从库（主库完全不受影响）：
sudo bash scripts/deploy_mysql_ms_demo.sh rollback
```

**答辩现场 15 秒演示脚本**（在 hadoop101 终端粘贴就能赢老师掌声）：
```bash
# A. SHOW SLAVE STATUS 三行关键指标（IO/SQL 双 Yes + Seconds_Behind≈0）
MYSQL_PWD="$(grep ^MYSQL_SLAVE_PASSWORD /opt/campus-bridge/.env | cut -d= -f2)" \
  mysql -h127.0.0.1 -P3307 \
        -u"$(grep ^MYSQL_SLAVE_USER /opt/campus-bridge/.env | cut -d= -f2)" \
        -e "SHOW SLAVE STATUS\G" | grep -E "Slave_IO_Running|Slave_SQL_Running|Seconds_Behind_Master"

# B. 主库 INSERT 一行 → 4s 内在从库查到（视觉冲击：实时同步）
MYSQL_MASTER_PWD="$(grep ^MYSQL_MASTER_PASSWORD /opt/campus-bridge/.env | cut -d= -f2)"
MYSQL_SLAVE_PWD="$(grep ^MYSQL_SLAVE_PASSWORD /opt/campus-bridge/.env | cut -d= -f2)"
MYSQL_MASTER_USER="$(grep ^MYSQL_MASTER_USER /opt/campus-bridge/.env | cut -d= -f2)"
MYSQL_SLAVE_USER="$(grep ^MYSQL_SLAVE_USER /opt/campus-bridge/.env | cut -d= -f2)"
MYSQL_PWD="$MYSQL_MASTER_PWD" mysql -h127.0.0.1 -P3306 -u"$MYSQL_MASTER_USER" -e "
  INSERT INTO campus_bridge.competitions (title, description, status, max_team, deadline, created_at)
  VALUES ('[主从同步测试] 蓝桥杯校内选拔', '2026.09 演示 binlog 复制，5s 内在 3307 从库可见', 'open', 3, DATE_ADD(NOW(), INTERVAL 10 DAY), NOW());
  DO SLEEP(4);
"
MYSQL_PWD="$MYSQL_SLAVE_PWD" mysql -h127.0.0.1 -P3307 -u"$MYSQL_SLAVE_USER" -e "
  SELECT id, title, status, created_at FROM campus_bridge.competitions ORDER BY id DESC LIMIT 1;
"
```

**预期答辩回答话术（你照着说）**：
> 「我们先用 Flask+Gunicorn 全量读写主库，保证一致性；再在同一台 VM 上单独开一个 MySQL 3307 实例做从库演示 ROW 格式 binlog 异步复制。
> 主库 FTWRL + mysqldump --master-data=2 把 CHANGE MASTER 坐标自动写进 dump 头，从库导入快照后 START SLAVE，IO/SQL 两个线程都是 Yes，Seconds_Behind_Master 稳定在 0-1 秒。
> Flask 业务层没有做读写分离，避免写后读不一致，但是数据库层已经具备了容灾和只读扩展的基础，后续如果上生产可以用 ProxySQL/MaxScale 再加透明读写分离。」

---

## 🏭 生产部署（CentOS 7.4 已验证）

### 1. 真实部署路径与数据库位置
```
/opt/campus-bridge/
├── app.py  routes_*.py  models.py  config.py  ...
├── .env           # 生产环境变量（MYSQL_MASTER_PASSWORD/DEEPSEEK_API_KEY 等真实值，不入 git）
├── database/      # SQL 脚本与种子脚本（campus_bridge.db 已移除，生产只用 MySQL 主库）
├── uploads/       # 用户上传资料/帖子图片/聊天图片
└── .venv/         # Python 3.9.20 虚拟环境
```

### 2. Gunicorn systemd 服务：`/etc/systemd/system/campus-bridge.service`
```ini
[Unit]
Description=CampusBridge Flask App (Gunicorn)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/campus-bridge
Environment="PATH=/opt/campus-bridge/venv/bin"
ExecStart=/opt/campus-bridge/venv/bin/gunicorn \
  -w 4 -b 127.0.0.1:8000 --timeout 120 \
  --access-logfile /var/log/campus-bridge-access.log \
  --error-logfile  /var/log/campus-bridge-error.log \
  "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```
管理命令：
```bash
systemctl daemon-reload
systemctl enable campus-bridge
systemctl start  campus-bridge
systemctl status campus-bridge
```

### 3. Nginx 反向代理（可选，未启用时 Gunicorn 直接绑公网 80）
```nginx
server {
    listen 80;
    server_name _;
    client_max_body_size 50M;

    location /static/  { alias /opt/campus-bridge/static/;  expires 7d; }
    location /uploads/ { alias /opt/campus-bridge/uploads/; expires 7d; }

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

### 4. 常见坑位清单
| 坑 | 症状 | 解法 |
|---|---|---|
| **MySQL 未填/密码错误** | 启动期直接报 `RuntimeError: MySQL 主库连接失败（已禁用 SQLite 降级）` | 检查 .env 的 MYSQL_MASTER_PASSWORD / MYSQL_MASTER_HOST；或用兼容旧键 MYSQL_USER / MYSQL_PASSWORD 回填 |
| **__pycache__ 读旧字节码** | 改了 Python 文件重启还显示旧逻辑 | `find ... -name __pycache__ -exec rm -rf {} +` |
| **大盘出现用户数=0** | MySQL campus_bridge 库为空或连上了错误库 | `mysql -uroot -p -e "USE campus_bridge; SELECT COUNT(*) FROM users;"` 校验；并检查 systemd 服务 WorkingDirectory 仍然是 `/opt/campus-bridge` |
| **旧 base.html 搜索框只刷新** | 导航栏输入搜索词回车停在当前页 | SCP 最新 `templates/base.html` 到服务器（已包 `<form action=url_for('search') method=GET>`） |
| **500 页面伪装成首页** | 访问 `/forum/` 视觉上=首页（实际 500） | 已修！app.py L220-249 errorhandler 改成独立渐变 500 卡片 |
| **Post.images eager loading 报错** | 论坛 500：`'Post.images' does not support object population` | 已修！models.py images 关系 `lazy='dynamic'` → `lazy='select'` |
| **`p.author.level_badge` UndefinedError** | 论坛 500 | 已修！forum_index.html 改成 `p.author.get_level_info()` 返回字典 |

---

## 🔒 安全合规

1. **不提交真实密钥**：`.env` 已在 `.gitignore`，`.env.example` 只保留占位符
2. **改默认管理员密码**：生产上登录 admin/admin123 后立刻在「个人设置」改密码
3. **换 SECRET_KEY**：`python -c "import secrets;print(secrets.token_hex(32))"` 生成随机串
4. **限制上传目录执行权限**：Nginx `/uploads/` 路径禁止解析 PHP / 脚本
5. **DeepSeek API Key 定期轮换**：不要硬编码在代码里，只走 `.env`

---

## 📝 可扩展路线（TODO）

- [ ] **WebSocket 改造聊天**：当前是前端轮询 `/chat/api/poll/<friend_id>`，下一步换 Flask-SocketIO
- [ ] **第三方登录**：微信 / QQ OAuth
- [ ] **资料全文检索**：接入 Whoosh（本地）或 Elasticsearch（生产）
- [ ] **管理员审计日志**：操作入库 + 后台可查询
- [ ] **移动端打磨**：当前响应式可用，可进一步做小程序 / PWA

---

## 📄 License

校园项目内部使用，代码仅供学习交流。
