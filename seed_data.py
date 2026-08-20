"""校桥 CampusBridge 种子数据脚本
为各大功能区生成丰富的示例数据，方便开发和演示。
运行方式：python seed_data.py
"""

import random
import io
import sys

# 解决 Windows 控制台中文/特殊字符编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from datetime import datetime, timedelta
from app import create_app
from extensions import db
from models import (
    User, ForumCategory, Post, PostLike, PostFavorite, Comment,
    Material, MaterialReview,
    Competition, Application, TeamGroup, GroupMember, GroupMessage,
    Textbook, TextbookMessage,
    Notification, FriendRequest,
    ChatMessage, ChatGroup, ChatGroupMember, ChatGroupMessage,
)

app = create_app()


# ── 工具函数 ──
def rand_date(days_back=30):
    return datetime.utcnow() - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )


def seed():
    with app.app_context():
        # ═══════════════════════════════════════════════════
        # 0. 清理旧数据
        # ═══════════════════════════════════════════════════
        print("=" * 50)
        print("  校桥 CampusBridge 种子数据填充")
        print("=" * 50)
        print("\n清理旧数据...")

        tables = [
            ChatGroupMessage, ChatGroupMember, ChatGroup,
            ChatMessage, FriendRequest, Notification,
            TextbookMessage, Textbook,
            GroupMessage, GroupMember, TeamGroup,
            Application, Competition,
            MaterialReview, Material,
            PostFavorite, PostLike, Comment, Post,
            ForumCategory, User,
        ]
        for t in tables:
            try:
                t.query.delete()
            except Exception:
                pass
        db.session.commit()
        print("[OK] 清理完毕\n")

        # ═══════════════════════════════════════════════════
        # 1. 用户（接地气的中文昵称）
        # ═══════════════════════════════════════════════════
        print("[1/8] 创建用户...")

        USERS_DATA = [
            {"username": "admin",         "email": "admin@campusbridge.com",  "password": "admin123",   "role": "admin", "bio": "校桥管理员，负责平台运营和内容审核。"},
            {"username": "小明学长",       "email": "xiaoming@qq.com",         "password": "123456",     "role": "user",  "bio": "计算机科学大三，热爱开源，喜欢写博客分享技术。"},
            {"username": "图书馆小助手",    "email": "library@campusbridge.com","password": "123456",     "role": "user",  "bio": "整理各科学习资料，欢迎找我要笔记和思维导图～"},
            {"username": "竞赛达人李",      "email": "lilei@qq.com",            "password": "123456",     "role": "user",  "bio": "ACM集训队成员，常年混迹各类竞赛，拿过省赛银牌。"},
            {"username": "文艺少女小王",    "email": "wang@qq.com",             "password": "123456",     "role": "user",  "bio": "汉语言文学专业，爱读书爱生活，喜欢分享校园日常。"},
            {"username": "篮球少年阿杰",    "email": "ajie@qq.com",             "password": "123456",     "role": "user",  "bio": "校篮球队队长，运动器材一大堆，欢迎约球。"},
            {"username": "考研上岸学姐",    "email": "kaoyan@qq.com",           "password": "123456",     "role": "user",  "bio": "刚上岸985计算机，分享考研经验和复习资料。"},
            {"username": "前端小赵",        "email": "zhao@qq.com",             "password": "123456",     "role": "user",  "bio": "大二软工，Vue/React都会一点，正在学TypeScript。"},
            {"username": "摄影爱好者阿林",  "email": "photo@qq.com",            "password": "123456",     "role": "user",  "bio": "用镜头记录校园美好瞬间，有设备可约拍。"},
            {"username": "吉他手小陈",      "email": "chen@qq.com",             "password": "123456",     "role": "user",  "bio": "校园乐队吉他手，欢迎来jam！也收学生教吉他。"},
            {"username": "实验室搬砖人",    "email": "lab@qq.com",              "password": "123456",     "role": "user",  "bio": "电子系研一，天天泡实验室，偶尔冒泡分享科研工具。"},
            {"username": "食堂探店博主",    "email": "foodie@qq.com",           "password": "123456",     "role": "user",  "bio": "吃遍全校食堂及周边小吃，不定期更新美食测评。"},
            {"username": "考研二战老学长",  "email": "kaoyan2@qq.com",          "password": "123456",     "role": "user",  "bio": "一战失误二战逆袭，408专业课132分，欢迎交流。"},
            {"username": "骑行爱好者阿强",  "email": "bike@qq.com",             "password": "123456",     "role": "user",  "bio": "周末经常骑车环城，有同好可以一起组队。出二手山地车配件。"},
            {"username": "萌新小学妹",      "email": "xinxin@qq.com",           "password": "123456",     "role": "user",  "bio": "大一新生，啥都好奇，希望学长学姐多多关照！"},
            {"username": "留学备考ing",     "email": "ielts@qq.com",            "password": "123456",     "role": "user",  "bio": "正在准备雅思和GRE，目标港三新二，有一起的小伙伴吗？"},
            {"username": "二手交易达人",    "email": "secondhand@qq.com",       "password": "123456",     "role": "user",  "bio": "混迹各种二手平台，擅长淘好物砍好价，出闲置回血中。"},
            {"username": "学生会小刘",      "email": "liu@qq.com",              "password": "123456",     "role": "user",  "bio": "校学生会外联部长，经常组织活动，认识很多朋友。"},
            {"username": "熬夜写代码",      "email": "dev@qq.com",              "password": "123456",     "role": "user",  "bio": "全栈开发学习中，MERN/LAMP都会搞，接点小项目练手。"},
            {"username": "考证达人周姐",    "email": "zhou@qq.com",             "password": "123456",     "role": "user",  "bio": "教资/普通话/计算机二级均已拿下，下个目标CPA。"},
        ]

        user_map = {}
        for u in USERS_DATA:
            existing = User.query.filter_by(username=u["username"]).first()
            if existing:
                user_map[u["username"]] = existing
            else:
                obj = User(
                    username=u["username"], email=u["email"],
                    role=u["role"], bio=u["bio"],
                    created_at=rand_date(90),
                )
                obj.set_password(u["password"])
                db.session.add(obj)
                user_map[u["username"]] = obj
        db.session.commit()
        # 重新查询确保 ID 绑定
        for name in list(user_map.keys()):
            user_map[name] = User.query.filter_by(username=name).first()
        user_list = list(user_map.values())
        print(f"[OK] {len(user_map)} 个用户（管理员密码 admin123，普通用户密码 123456）\n")

        # ═══════════════════════════════════════════════════
        # 2. 论坛分区 + 帖子 + 评论 + 点赞 + 收藏
        # ═══════════════════════════════════════════════════
        print("[2/8] 创建论坛帖子...")

        # 先确保分区存在
        CATEGORY_DATA = [
            ("学习交流", "课程学习、学术讨论、资料分享", "📚", 1),
            ("校园生活", "校园活动、日常生活、吃喝玩乐", "🏫", 2),
            ("技术讨论", "编程、设计、开源、技术分享", "💻", 3),
            ("求职升学", "实习、考研、求职、留学交流", "🎓", 4),
            ("闲聊灌水", "轻松话题、趣事分享、日常吐槽", "💬", 5),
        ]
        cat_map = {}
        for name, desc, icon, sort in CATEGORY_DATA:
            c = ForumCategory.query.filter_by(name=name).first()
            if not c:
                c = ForumCategory(name=name, description=desc, icon=icon, sort_order=sort)
                db.session.add(c)
            cat_map[name] = c
        db.session.commit()
        for name in CATEGORY_DATA:
            cat_map[name[0]] = ForumCategory.query.filter_by(name=name[0]).first()

        # 帖子数据 — 按分区组织
        POSTS_BY_CAT = {
            "学习交流": [
                {"title": "高等数学期末复习攻略（附思维导图）",
                 "content": "整理了这学期高数(下)的完整知识框架，包括多元函数微分、重积分、曲线曲面积分三大块。建议按照「概念→公式→题型→易错点」的顺序复习。重点提醒：格林公式和高斯公式的条件一定要看清楚，考试最爱考这个坑！有需要的同学可以私信我要高清PDF版本。", "views": 856, "pinned": True},
                {"title": "数据结构与算法学习路径分享",
                 "content": "很多大一的同学问我数据结构怎么入门。我的建议是：\n1️⃣ 先看《大话数据结构》建立直觉，不要直接啃严蔚敏\n2️⃣ 用Python把每个数据结构实现一遍（链表、栈、队列、树、图）\n3️⃣ 去LeetCode刷对应的专题，从简单题开始\n4️⃣ 最后再做综合题和应用题\n别急着刷难题，把基础打牢比什么都重要。我整理了一份刷题顺序清单，需要的话评论区留言。", "views": 1203, "pinned": False},
                {"title": "四六级资料大礼包分享（真题+听力+模板）",
                 "content": "整理了近五年四六级真题+听力音频mp3+作文万能模板，需要的同学留言或私信。特别推荐刘晓艳老师的作文课，模板真的很实用，我四级写作靠她的模板拿了180+！资料比较大，放网盘了，回复可见链接。", "views": 2340, "pinned": False},
                {"title": "线性代数公式速查表（A4打印版）",
                 "content": "自己手打了一份线代公式速查表，包括行列式、矩阵、向量空间、特征值四大模块的所有核心公式。排版好了直接打印A4纸，考试前看一遍就够了！字迹清晰无水印，放心使用。", "views": 678, "pinned": False},
                {"title": "Python零基础入门资源推荐（非CS专业友好）",
                 "content": "很多非CS专业的同学想学Python，我推荐：\n📖 廖雪峰的Python教程（免费在线）\n📖 《Python Crash Course》中文版\n🎥 B站小甲鱼的零基础Python\n⚠️ 重点：不要只看视频！一定要动手写代码！每学一个概念就做一个小练习。我整理了50个Python小练习题，回复即可获取。", "views": 1567, "pinned": False},
                {"title": "英语口语提升经验：从哑巴英语到流利对话",
                 "content": "坚持了半年英语口语练习，效果显著。我的方法：\n1. 每天用英语自言自语15分钟（描述今天发生的事）\n2. Shadowing跟读BBC 6 Minute English（影子跟读法）\n3. 用HelloTalk找语言交换伙伴\n4. 每周看一部英文电影不带字幕\n三个月的变化比学了三年哑巴英语都好。强烈推荐影子跟读法！", "views": 432, "pinned": False},
                {"title": "期末考试时间管理大法",
                 "content": "分享我用了三年的期末复习时间管理方法——番茄工作法改良版：\n⏰ 50分钟学习 + 10分钟休息为一个周期\n📋 每天早上列出当天必须完成的3个任务（不要贪多）\n📱 学习期间手机开Forest种树，坚决不碰\n🏃 下午4-5点去操场跑两圈，回来效率翻倍\n🌙 晚上11点前睡觉，保证第二天精力充沛\n一周复习下来，效率比通宵高太多了！", "views": 1102, "pinned": False},
            ],
            "校园生活": [
                {"title": "食堂二楼麻辣香锅yyds！人均15吃到撑",
                 "content": "今天发现二食堂二楼新开的麻辣香锅窗口，人均不到15块，量大管饱。推荐中辣+微麻的组合，素菜拼盘才6块钱！阿姨人也超好，每次都多给我加豆皮。还有他们家的酸梅汤是自制的，2块一大杯。大家还吃过哪家食堂的隐藏美食？来互相推荐啊！", "views": 3456, "pinned": False},
                {"title": "操场夜跑组队！每天20:00不见不散",
                 "content": "有没有每天8点操场夜跑的小伙伴？一个人跑太容易偷懒了，想组个小群互相监督打卡。配速6分左右，每次5公里，男女不限！已经有三个人了，再来几个就可以组队跑间歇了。感兴趣的同学直接加我好友，拉你进群。", "views": 890, "pinned": False},
                {"title": "图书馆自习室选位指南（避坑必看）",
                 "content": "作为一个每天泡图书馆的人，给大家整理一下各楼层自习区的优劣：\n✅ 五楼新装修区：充电口充足、有茶水间、靠窗位置采光好\n✅ 三楼南区：安静、空调足、离卫生间近\n❌ 四楼东区：空调时好时坏、夏天闷热\n❌ 二楼大厅：人来人往太吵、WiFi信号差\n⚠️ 考试周建议7:30前到，晚了只剩角落。周末人少可以8:30到。", "views": 2234, "pinned": True},
                {"title": "五一假期周边游求推荐！",
                 "content": "不想走太远，周边有没有适合两三天玩的地方？最好是交通方便、风景好、消费不太高的。目前考虑了：山水景区（怕五一太挤）和古镇（怕太商业化）。有没有去过的小伙伴给点真实建议？最好能附上大概花费，学生党预算有限😂", "views": 567, "pinned": False},
                {"title": "校园流浪猫救助计划——需要你的帮助",
                 "content": "最近南区猫舍多了几只小猫，天气越来越冷了。想组织一次小型募捐活动，买猫粮和猫窝。目前已经联系了学校动物保护协会，他们可以提供场地和基础物资。我们需要：\n🐱 猫粮（皇家/冠能幼猫粮优先）\n🏠 猫窝/纸箱（防水的最好）\n💊 驱虫药和基础药品\n有意向参与的同学请在楼下回复，我们一起行动！", "views": 1678, "pinned": False},
                {"title": "南区宿舍停水通知（及应对攻略）",
                 "content": "刚收到通知说南区1-4号楼明天上午8点到下午6点停水检修。大家今晚记得：\n🚰 接好洗漱用水（建议用大桶接满）\n🚽 接两桶冲厕所的水\n🔌 热水器提前烧好洗澡水\n另外三食堂旁边的公共浴室明天正常开放，实在不行可以去那边。", "views": 345, "pinned": False},
            ],
            "技术讨论": [
                {"title": "搭了一个校园内网网盘，免费给大家用",
                 "content": "用Docker+Nextcloud在宿舍树莓派上搭了个内网文件共享服务，访问速度快（内网千兆），可以用来存课件、代码、笔记。每个人50G空间，支持WebDAV挂载到电脑上像本地硬盘一样用。有需要的同学私信我拿地址和账号，完全免费，就是别存小电影😂", "views": 2345, "pinned": False},
                {"title": "Git从入门到会用——30分钟速成教程",
                 "content": "写了一份极简Git教程，只讲工作中最常用的10个命令：\n```\ngit clone / git pull / git add / git commit\ngit push / git branch / git checkout / git merge\ngit stash / git log\n```\n每个命令都有动图演示和常见场景说明。教程放在GitHub上了，搜 CampusBridge/git-tutorial 即可。学会了别忘了给个Star⭐", "views": 1876, "pinned": True},
                {"title": "VSCode必备插件推荐（前端向）",
                 "content": "作为前端开发重度用户，推荐几个提升效率的VSCode插件：\n🔧 GitLens — Git可视化，每一行代码都能看到谁写的\n🎨 Prettier — 代码格式化，保存自动排版\n🔍 Error Lens — 行内显示错误信息，不用hover\n📝 Markdown All in One — 写文档神器\n⚡ Thunder Client — 轻量级API测试，替代Postman\n🤖 GitHub Copilot — AI代码补全（学生免费！）\n大家还有什么好用的插件推荐？", "views": 3201, "pinned": False},
                {"title": "Flask项目部署后500错误，求大佬帮忙看看",
                 "content": "本地跑得好好的，部署到云服务器后就各种500。查了日志提示数据库连接问题：\n```\nsqlalchemy.exc.OperationalError: unable to open database file\n```\n用的是SQLite，是不是生产环境还是得换MySQL？另外Nginx反向代理的配置也不太确定。求有部署经验的同学指点一下，请喝奶茶！", "views": 678, "pinned": False},
                {"title": "分享C语言课设——贪吃蛇（附源码）",
                 "content": "用C语言+EasyX图形库写了个贪吃蛇小游戏，功能包括：\n🐍 键盘方向键控制\n📈 速度随分数递增\n🏆 本地分数排行榜（文件存储）\n🎵 简单的音效反馈\n代码已开源到GitHub，注释详细适合新手参考。欢迎Star和PR！也欢迎大家分享自己的课设项目～", "views": 1543, "pinned": False},
            ],
            "求职升学": [
                {"title": "2026届秋招提前批信息汇总（持续更新）",
                 "content": "整理了一波已经开启秋招提前批的公司和投递链接：\n🔵 字节跳动 — 7月10日开始，内推码: XXXXX\n🟢 腾讯 — 7月15日开始，产品/技术/设计均有HC\n🟠 美团 — 7月8日开始，今年扩招\n🔴 阿里巴巴 — 7月12日开始\n🟣 百度/京东 — 预计7月下旬\n💡 Tips：尽早投递！前期HC充足面试难度相对低一些。需要内推的同学可以私信我要联系方式。", "views": 5678, "pinned": True},
                {"title": "考研408复习全年时间线（132分经验）",
                 "content": "我是从3月开始准备的，最后408考了132，分享完整时间线：\n📅 3-6月 基础阶段：课本精读+王道单科书，每天4-5h\n📅 7-9月 强化阶段：刷真题+模拟题，整理错题本，每天7-8h\n📅 10-12月 冲刺阶段：查漏补缺+心态调整+模拟考试，每天8-9h\n⚠️ 重点：数据结构占45分，计算机组成原理占45分，这两门一定吃透！OS和网络相对好拿分。真题至少刷3遍！", "views": 8901, "pinned": False},
                {"title": "字节跳动后端实习面经（已拿Offer）",
                 "content": "岗位：后端开发实习生（北京）\n📋 一面（1h）：手撕两道算法（LRU缓存+岛屿数量）+ 项目深挖 + TCP三次握手\n📋 二面（1h）：系统设计（设计一个短链接服务）+ MySQL索引优化 + Redis缓存策略\n📋 三面（45min）：交叉面，聊项目理解和职业规划\n📋 HR面（30min）：常规问题，期望薪资和入职时间\n整体难度中等偏上，重点考察基础和思考深度。LeetCode中等难度题要能秒，系统设计至少了解常见方案。", "views": 4567, "pinned": False},
                {"title": "普通二本→985考研逆袭：我的故事",
                 "content": "本科双非二本，今年上岸某985计算机专硕。初试总分387，政治74/英语78/数学123/408专业课112。\n想跟大家说的是，双非考985完全有可能！关键是：\n1. 目标坚定不动摇（我中间崩溃过两次但都扛过来了）\n2. 信息收集要全面（加考研群、看经验帖、找学长学姐）\n3. 执行力比天赋重要（每天的计划必须完成）\n4. 不要跟别人比进度（按自己的节奏来）\n有什么问题可以在评论区问，我看到都会回～", "views": 10234, "pinned": False},
                {"title": "简历这样写，面试邀请率提高50%",
                 "content": "帮很多学弟学妹改过简历，发现几个高频问题：\n❌ 写成流水账没有量化成果\n❌ 项目经验太空泛，没有技术细节\n❌ 排版花里胡哨，HR根本看不清重点\n✅ 正确做法：\n1. 用STAR法则写项目（情境-任务-行动-结果）\n2. 每个项目写清楚用了什么技术、解决了什么问题\n3. 保持一页纸，格式简洁\n4. 针对不同岗位准备不同版本的简历\n模板我放在评论区了，自取。", "views": 3456, "pinned": False},
            ],
            "闲聊灌水": [
                {"title": "大家来介绍一下各自的专业吧！让高中生选专业有个参考",
                 "content": "我是计算机的，天天和代码打交道，头发暂时还在😂。\n课程方面：高数/线代/概率论/离散数学是基础，然后就是数据结构/操作系统/计网/组成原理四大件。\n就业方面：确实好找工作，但前提是得真的会写代码，光靠考试高分是不够的。\n好奇其他专业的同学日常都在学什么？也让高考完的学弟学妹有个参考！", "views": 4567, "pinned": False},
                {"title": "有没有人一起看《黑镜》第七季？来讨论",
                 "content": "刚看完前两集，每一集都细思极恐啊！最震撼的是讲AI意识上传那一集，联想到现在各种AI工具的发展，感觉离我们并不遥远。还有一集讲社交评分的设定虽然不新鲜但拍得很深刻。\n有人也追了吗？来说说你们最喜欢的集数（不要剧透！）", "views": 1234, "pinned": False},
                {"title": "学校后门那些不为人知的神仙小吃摊",
                 "content": "作为探店两年的资深吃货，曝光一下学校周边被低估的小吃摊：\n🥇 后门右拐第三家烤冷面：加蛋加肠8元，灵魂酱汁一绝\n🥈 西门水果摊后面的煎饼果子：薄脆自己炸的，加辣条更好吃\n🥉 北门晚上的铁板鱿鱼：现串现烤，10元3串\n🏅 东门老奶奶的烤红薯：冬天限定，甜到心里\n大家还有什么私藏的好吃摊位？别藏着掖着！", "views": 5678, "pinned": False},
                {"title": "期末考试安排出来了，来看看谁更惨",
                 "content": "我们专业考6门，从1月8号考到15号，中间只休息一天。最难的数据结构和计组居然排在同一天！上午下午各一门，太狠了。\n大家的考试安排怎么样？有没有更惨的来比比？让我们一起哭一会儿😭", "views": 2345, "pinned": False},
                {"title": "分享一下你的2026年度目标吧",
                 "content": "2026年过半了，大家的年度flag都完成得怎么样了？\n我先来：\n✅ 刷100道LeetCode（完成了68道）\n✅ 读完10本书（完成了6本）\n⬜ 找个暑假实习（正在进行中）\n⬜ 学会弹唱5首歌（吉他已经落灰了...）\n下半年继续加油！大家的年度目标是什么？", "views": 1890, "pinned": False},
            ],
        }

        post_objects = []
        comment_count = 0
        COMMENT_POOL = [
            "写得太好了，收藏了！", "感谢分享，很有帮助👍", "学习了，期待更多内容。",
            "顶一个，让更多人看到。", "赞同！我也是这么想的。", "非常有用的信息！",
            "楼主说得对，深有体会。", "帮大忙了，谢谢！", "先码住，回头细看。",
            "好帖，希望更多人看到。", "请问楼主可以再详细说说吗？", "已收藏，期待后续更新。",
            "实用！解决了我一直以来的困惑。", "深有同感，手动点赞。", "谢谢分享，已转发给室友。",
        ]

        for cat_name, posts_data in POSTS_BY_CAT.items():
            category = cat_map[cat_name]
            for pd in posts_data:
                author = random.choice(user_list)
                post = Post(
                    title=pd["title"],
                    content=pd["content"],
                    user_id=author.id,
                    category_id=category.id,
                    views=pd["views"] + random.randint(-100, 100),
                    is_pinned=pd.get("pinned", False),
                    created_at=rand_date(60),
                )
                db.session.add(post)
                db.session.flush()
                post_objects.append(post)

                # 评论 2~8 条
                for _ in range(random.randint(2, 8)):
                    commenter = random.choice(user_list)
                    c = Comment(
                        content=random.choice(COMMENT_POOL),
                        user_id=commenter.id,
                        post_id=post.id,
                        created_at=post.created_at + timedelta(hours=random.randint(1, 72)),
                    )
                    db.session.add(c)
                    comment_count += 1

                # 点赞 3~12 个
                likers = random.sample(user_list, min(random.randint(3, 12), len(user_list)))
                for liker in likers:
                    if liker.id != author.id:
                        try:
                            db.session.add(PostLike(user_id=liker.id, post_id=post.id))
                        except Exception:
                            pass

                # 收藏 1~5 个
                favers = random.sample(user_list, min(random.randint(1, 5), len(user_list)))
                for faver in favers:
                    if faver.id != author.id:
                        try:
                            db.session.add(PostFavorite(user_id=faver.id, post_id=post.id))
                        except Exception:
                            pass

        db.session.commit()
        total_posts = sum(len(v) for v in POSTS_BY_CAT.values())
        print(f"[OK] {len(cat_map)} 个分区、{total_posts} 篇帖子、{comment_count} 条评论\n")

        # ═══════════════════════════════════════════════════
        # 3. 学习资料 + 评价
        # ═══════════════════════════════════════════════════
        print("[3/8] 创建学习资料...")

        MATERIALS_DATA = [
            {"title": "高等数学(下)期末复习笔记（手写扫描）", "desc": "手写扫描版，覆盖多元函数微分、重积分、曲线曲面积分全章节。字迹清晰，公式标注准确，包含经典例题和易错点提示。", "cat": "笔记", "ftype": "pdf", "fsize": 15_680_000, "dls": 345},
            {"title": "大学英语四级真题2019-2025合集", "desc": "7年真题+答案解析+听力音频mp3。按年份分类，每套题都有详细解析和做题技巧提示。听力音频在压缩包里。", "cat": "试题", "ftype": "other", "fsize": 256_000_000, "dls": 1234},
            {"title": "数据结构课件全套（王老师版）", "desc": "计算机学院王老师的全套PPT课件，含线性表、树、图、查找、排序。PPT配合教材使用效果最佳，重点部分有标注。", "cat": "课件", "ftype": "ppt", "fsize": 45_000_000, "dls": 567},
            {"title": "线性代数课后习题详细解答", "desc": "同济版线代全部课后习题的详细解答过程，每一步都有推导说明。适合自学和考研复习参考。", "cat": "笔记", "ftype": "pdf", "fsize": 8_500_000, "dls": 289},
            {"title": "Python编程从入门到实践——项目代码合集", "desc": "《Python Crash Course》书中三个项目的完整源码：外星人入侵游戏、数据可视化、Web应用程序。每个文件都有中文注释。", "cat": "其他", "ftype": "other", "fsize": 3_200_000, "dls": 678},
            {"title": "计算机网络期末重点总结（谢希仁版）", "desc": "谢希仁教材配套考点总结，含OSI七层模型、TCP/IP协议栈、应用层协议等核心考点。附带历年期末真题分析。", "cat": "笔记", "ftype": "pdf", "fsize": 5_100_000, "dls": 423},
            {"title": "C语言程序设计期末试题（含答案+AC代码）", "desc": "近三年C语言期末试卷+参考答案+编程题AC代码。考前刷一遍效果显著！", "cat": "试题", "ftype": "pdf", "fsize": 2_800_000, "dls": 534},
            {"title": "马克思主义原理全章思维导图", "desc": "用XMind制作的马原全章节思维导图，导出为高清图片。适合建立知识框架，配合课本使用。", "cat": "笔记", "ftype": "image", "fsize": 12_400_000, "dls": 198},
            {"title": "数据库原理实验报告Word模板", "desc": "MySQL实验报告标准模板，包含ER图绘制、SQL语句、实验结果截图的规范格式。直接套用即可。", "cat": "其他", "ftype": "doc", "fsize": 1_200_000, "dls": 312},
            {"title": "考研数学一真题（2010-2025）", "desc": "16年数一真题高清PDF+逐题详细解析。按年份和知识点双重索引，方便针对性刷题。", "cat": "试题", "ftype": "pdf", "fsize": 98_000_000, "dls": 890},
            {"title": "操作系统概念（恐龙书）英文原版PDF", "desc": "Operating System Concepts 第10版英文原版，计算机专业必读经典。英文阅读对提升专业英语很有帮助。", "cat": "课件", "ftype": "pdf", "fsize": 34_000_000, "dls": 445},
            {"title": "算法导论第三版中文版", "desc": "CLRS算法导论中文高清扫描版，含全部章节+部分习题答案。算法学习的终极参考书，适合进阶阅读。", "cat": "课件", "ftype": "pdf", "fsize": 178_000_000, "dls": 567},
        ]

        POSITIVE_REVIEWS = [
            "质量很高，推荐下载！", "整理得很用心，感谢分享。", "刚好需要，太及时了！",
            "讲得很清楚，帮大忙了。", "已下载，资料很全面。", "非常实用，给五星好评。",
            "内容详实，排版清晰，一目了然。", "大佬太强了！跪谢！",
            "考试全靠它了，感谢分享！", "比课本好看多了，通俗易懂。",
        ]
        MID_REVIEWS = [
            "还可以，有些地方不太全，希望更新。", "总体还行，格式可以再优化一下。",
            "部分内容有点老，但也够用了。", "希望能补充更多例题。",
        ]

        for md in MATERIALS_DATA:
            author = random.choice(user_list)
            mat = Material(
                title=md["title"],
                description=md["desc"],
                category=md["cat"],
                file_key=f"demo/{md['title']}.{md['ftype']}",
                file_name=f"{md['title']}.{md['ftype']}",
                file_type=md["ftype"],
                file_size=md["fsize"],
                views=random.randint(50, 800),
                downloads=md["dls"] + random.randint(-30, 50),
                user_id=author.id,
                created_at=rand_date(90),
            )
            db.session.add(mat)
            db.session.flush()

            # 0~5 条评价
            reviewers = random.sample(user_list, min(random.randint(0, 5), len(user_list)))
            for reviewer in reviewers:
                if reviewer.id == author.id:
                    continue
                rating = random.choices([5, 5, 5, 4, 4, 3], weights=[5, 4, 4, 2, 2, 1])[0]
                pool = POSITIVE_REVIEWS if rating >= 4 else MID_REVIEWS
                try:
                    mr = MaterialReview(
                        material_id=mat.id,
                        user_id=reviewer.id,
                        rating=rating,
                        comment=random.choice(pool),
                        created_at=mat.created_at + timedelta(days=random.randint(1, 30)),
                    )
                    db.session.add(mr)
                except Exception:
                    pass

        db.session.commit()
        print(f"[OK] {len(MATERIALS_DATA)} 份学习资料\n")

        # ═══════════════════════════════════════════════════
        # 4. 竞赛招募 + 申请
        # ═══════════════════════════════════════════════════
        print("[4/8] 创建竞赛招募...")

        COMPS_DATA = [
            {"title": "2026全国大学生数学建模竞赛组队", "desc": "国赛9月开赛，现招募2名队友。我负责建模部分（数学系），希望找一位编程强的（MATLAB/Python）和一位写作好的（LaTeX排版）。有参赛经验者优先，没有也可以一起学。目标是省一冲国奖！", "type": "学科竞赛", "size": 3, "status": "open"},
            {"title": "互联网+创新创业大赛——智慧校园项目招人", "desc": "项目方向：AI校园智能助手。已写好商业计划书初稿，有导师指导。还需要：UI设计1名、前端1名、后端1名。目标校赛金奖+进省赛！项目有落地潜力和投资意向。", "type": "创新创业", "size": 5, "status": "open"},
            {"title": "ACM-ICPC集训队新学期招新", "desc": "校ACM集训队招新！要求：熟练掌握至少一门编程语言（C++/Java/Python均可），有一定算法基础（至少刷过50道LeetCode）。入队后每周集训2次+定期线上赛，下半年目标区域赛银牌以上。大一新生特别欢迎！", "type": "学科竞赛", "size": 0, "status": "open"},
            {"title": "校园十佳歌手大赛——寻找合唱搭档", "desc": "一年一度的校园歌手大赛来了！想找一位会吉他/钢琴的同学搭档，曲目可以一起商量，流行/民谣方向。我有舞台经验（参加过院级比赛），希望搭档也有一些音乐基础。排练时间灵活可协调。", "type": "文艺体育", "size": 2, "status": "open"},
            {"title": "毕业设计组队：校园二手交易小程序", "desc": "毕设选题是校园二手交易微信小程序，技术栈：uni-app + Node.js + MongoDB。目前我一个人，想再找1-2个同学一起做，可以分担前后端，答辩也有底气。有相关技术栈经验的最好，没有的话愿意学的也行。", "type": "其他", "size": 3, "status": "open"},
            {"title": "全国大学生英语竞赛(NECCS)备考小组", "desc": "组建NECCS备考互助小组，每天打卡背单词+做真题，互相批改作文。目前3人，再招2人满员。要求：每天至少投入1小时，每周参加一次在线讨论。目标初赛高分晋级决赛。", "type": "学科竞赛", "size": 5, "status": "open"},
            {"title": "RoboCup机器人足球赛队伍组建", "desc": "学院支持组建RoboCup参赛队伍，提供设备和场地！需要：机械设计（SolidWorks/CAD）、电路控制（STM32/Arduino）、视觉算法（OpenCV/Python）各方向的同学。零基础可学，有老师带队指导。这是一个非常好的项目经历！", "type": "学科竞赛", "size": 6, "status": "closed"},
            {"title": "校园微电影大赛创作团队招募", "desc": "拍摄一部关于大学生活的微电影（15分钟），参加省大学生微电影大赛。主题：青春与成长。需要：编剧（会写剧本）、摄影（有设备更佳）、剪辑（会PR/达芬奇）、演员若干。有热情最重要！", "type": "文艺体育", "size": 8, "status": "open"},
        ]

        APP_MSGS = [
            "你好，我对这个项目非常感兴趣！我有相关经验，希望能加入团队。",
            "看到招募很心动，我是相关专业的，可以一起合作吗？",
            "想加入！我的技能是Python和数据分析，能吃苦耐劳。",
            "请问还缺人吗？我可以做前端/后端开发。",
            "这个方向正好是我感兴趣的！希望能有机会一起参赛。",
            "你好，我是通过朋友推荐看到这个招募的。我有项目经验，希望能加入。",
        ]

        for cd in COMPS_DATA:
            owner = random.choice(user_list)
            comp = Competition(
                title=cd["title"],
                description=cd["desc"],
                comp_type=cd["type"],
                deadline=datetime.utcnow().date() + timedelta(days=random.randint(10, 60)),
                team_size=cd["size"],
                owner_id=owner.id,
                status=cd["status"],
                created_at=rand_date(45),
            )
            db.session.add(comp)
            db.session.flush()

            # 1~5个申请
            applicants = random.sample(
                [u for u in user_list if u.id != owner.id],
                min(random.randint(1, 5), len(user_list) - 1),
            )
            for applicant in applicants:
                application = Application(
                    competition_id=comp.id,
                    user_id=applicant.id,
                    message=random.choice(APP_MSGS),
                    status=random.choice(["pending", "pending", "approved", "approved", "rejected"]),
                    created_at=comp.created_at + timedelta(hours=random.randint(1, 48)),
                )
                db.session.add(application)

        db.session.commit()
        print(f"[OK] {len(COMPS_DATA)} 条竞赛招募\n")

        # ═══════════════════════════════════════════════════
        # 5. 二手闲置（多种品类）
        # ═══════════════════════════════════════════════════
        print("[5/8] 创建二手闲置...")

        TEXTBOOKS_DATA = [
            # 书籍
            {"title": "高等数学（第七版）上下册", "cat": "书籍", "author": "同济大学数学系", "publisher": "高等教育出版社", "price": 15, "condition": "良好", "desc": "上册有一些笔记，下册几乎全新。两本一起出，不单卖。校内面交。"},
            {"title": "数据结构（C语言版）", "cat": "书籍", "author": "严蔚敏", "publisher": "清华大学出版社", "price": 10, "condition": "一般", "desc": "经典教材，书边有翻阅痕迹，内部有部分标注。不影响阅读。"},
            {"title": "大学英语四级词汇书+真题", "cat": "书籍", "author": "", "publisher": "星火英语", "price": 8, "condition": "良好", "desc": "词汇书背了一遍，真题只做了三套。基本干净，扔掉可惜，便宜出。"},
            {"title": "考研政治全套（肖秀荣精讲精练+1000题+肖四肖八）", "cat": "书籍", "author": "肖秀荣", "publisher": "高等教育出版社", "price": 20, "condition": "一般", "desc": "全书有笔记和划线，适合提前了解考研政治的同学。不介意的来。"},
            # 数码
            {"title": "Switch游戏机 续航版 红蓝手柄", "cat": "数码产品", "author": "任天堂", "publisher": "", "price": 1200, "condition": "良好", "desc": "买来半年，玩了不到20小时，基本吃灰。带原装配件+保护壳+收纳包。送塞尔达卡带一张！"},
            {"title": "iPad Air 4 64G 深空灰 + Apple Pencil 2", "cat": "数码产品", "author": "Apple", "publisher": "", "price": 2800, "condition": "良好", "desc": "2024年购买，一直带壳+贴膜使用，屏幕无划痕。考研看网课记笔记神器！带原装充电器。"},
            {"title": "九成新机械键盘 C104 Cherry青轴 白色", "cat": "数码产品", "author": "ikbc", "publisher": "", "price": 220, "condition": "良好", "desc": "用了三个月换了红轴就闲置了。键帽已清洗消毒，包装盒还在。青轴打字手感绝佳。"},
            {"title": "AirPods Pro 2 蓝牙降噪耳机", "cat": "数码产品", "author": "Apple", "publisher": "", "price": 900, "condition": "良好", "desc": "用了大半年，续航正常。带原装充电盒+三副耳塞(M/S/L)。降噪效果真的很香，换了新款所以出。"},
            # 生活用品
            {"title": "宿舍用迷你小冰箱 6L", "cat": "生活用品", "author": "美的", "publisher": "", "price": 200, "condition": "良好", "desc": "容量6L可以放4罐饮料。制冷效果好，噪音很小不影响休息。夏天冰饮料冬天暖牛奶都可以。毕业出。"},
            {"title": "折叠床上书桌", "cat": "生活用品", "author": "", "publisher": "", "price": 25, "condition": "良好", "desc": "宿舍神器！冬天不用下床就能学习。可折叠不占地方，桌面有一点小划痕不影响使用。"},
            {"title": "床上三件套 纯棉 1.2m", "cat": "生活用品", "author": "南极人", "publisher": "", "price": 35, "condition": "全新", "desc": "买大了用不上，全新未拆封！适用1.2m单人床。花色素雅，男女通用。"},
            {"title": "落地挂衣架 简约款 高160cm", "cat": "生活用品", "author": "宜家", "publisher": "", "price": 40, "condition": "良好", "desc": "宿舍挂衣服用，可拆卸携带方便。底座稳当不会倒，承重好。毕业清仓出。"},
            # 运动器材
            {"title": "Wilson网球拍一对+6个球", "cat": "运动器材", "author": "Wilson", "publisher": "", "price": 150, "condition": "良好", "desc": "体育课买的，用了一个学期。拍面完好，手柄握布新换的。适合初学入门。"},
            {"title": "Keep加厚瑜伽垫 10mm防滑款", "cat": "运动器材", "author": "Keep", "publisher": "", "price": 30, "condition": "良好", "desc": "Keep旗舰款，加厚10mm，防滑效果很好。跟风买的结果用了不到5次...有需要的收了吧。"},
            {"title": "Nike篮球鞋 42码 实战款", "cat": "服饰鞋包", "author": "Nike", "publisher": "", "price": 180, "condition": "一般", "desc": "穿了半个学期，鞋底有磨损但不影响打球。因为入手了新款所以出掉。42码标准码。"},
        ]

        for td in TEXTBOOKS_DATA:
            seller = random.choice(user_list)
            status = random.choice(["available", "available", "available", "available", "reserved", "sold"])
            tb = Textbook(
                title=td["title"],
                category=td["cat"],
                author=td.get("author", ""),
                publisher=td.get("publisher", ""),
                price=td["price"],
                condition=td["condition"],
                description=td["desc"],
                trade_status=status,
                user_id=seller.id,
                created_at=rand_date(45),
            )
            db.session.add(tb)

        db.session.commit()
        print(f"[OK] {len(TEXTBOOKS_DATA)} 件二手闲置\n")

        # ═══════════════════════════════════════════════════
        # 6. 好友关系
        # ═══════════════════════════════════════════════════
        print("[6/8] 创建好友关系...")

        existing_pairs = set()
        friend_count = 0
        for _ in range(35):
            a, b = random.sample(user_list, 2)
            pair = tuple(sorted([a.id, b.id]))
            if pair in existing_pairs:
                continue
            existing_pairs.add(pair)
            fr = FriendRequest(
                sender_id=pair[0],
                receiver_id=pair[1],
                status=random.choice(["accepted", "accepted", "accepted", "pending", "rejected"]),
                message=random.choice([
                    "你好，想加个好友交流一下学习经验！",
                    "看了你的帖子觉得很有意思，加个好友吧～",
                    "同在准备考研，一起加油！",
                    "你好呀，看到你也喜欢打球，交个朋友？",
                    None, None,
                ]),
                created_at=rand_date(60),
            )
            db.session.add(fr)
            friend_count += 1

        db.session.commit()
        print(f"[OK] {friend_count} 条好友关系\n")

        # ═══════════════════════════════════════════════════
        # 7. 消息通知
        # ═══════════════════════════════════════════════════
        print("[7/8] 创建消息通知...")

        NOTI_TEMPLATES = [
            ("comment", "有人评论了你的帖子", "你的帖子收到了新的回复，快去看看吧！"),
            ("like", "你的帖子获得了新的点赞", "你的分享获得了同学们的认可！"),
            ("application", "有人申请了你的竞赛招募", "有人对你的竞赛招募感兴趣并提交了申请。"),
            ("message", "你收到了一条新私信", "有人向你发送了一条私信，点击查看。"),
            ("system", "欢迎加入校桥！", "欢迎来到校桥 CampusBridge！在这里你可以分享资料、参与讨论、寻找队友。祝你使用愉快！"),
        ]
        noti_count = 0
        for user in user_list:
            for _ in range(random.randint(2, 5)):
                t = random.choice(NOTI_TEMPLATES)
                n = Notification(
                    user_id=user.id,
                    type=t[0],
                    title=t[1],
                    content=t[2],
                    is_read=random.random() < 0.6,
                    created_at=rand_date(30),
                )
                db.session.add(n)
                noti_count += 1
        db.session.commit()
        print(f"[OK] {noti_count} 条通知\n")

        # ═══════════════════════════════════════════════════
        # 8. 聊天消息
        # ═══════════════════════════════════════════════════
        print("[8/8] 创建聊天消息...")

        CHAT_MSGS = [
            "在吗？", "在的，怎么了？", "你那个资料我看了，很有用！谢谢！",
            "哈哈太好了，能帮到你就好", "周末一起去图书馆吗？", "好啊，几点？",
            "下午两点吧，老地方。", "OK，到时候见！", "你那有数据结构的作业答案吗？",
            "我找找电脑里有没有", "找到了发你", "谢谢大佬！救命了",
            "不客气～", "今天食堂人好多啊", "是啊，考试周大家都来图书馆了",
            "这道题你会做吗？我用动态规划一直WA", "我看看...应该用贪心，不是DP",
            "好的我试试！", "加油！", "你报了那个数学建模的竞赛吗？",
            "还没，在犹豫要不要参加", "一起报吧，人多力量大", "行，那我也报上！",
            "今天天气不错诶", "是的，适合出去打球", "哈哈下午走起！",
            "最近在学什么新东西吗？", "在学React，有点难但是很有意思",
            "厉害了，学会教我", "没问题，先学好JS基础再说",
        ]
        chat_count = 0
        for pair in list(existing_pairs)[:15]:
            for _ in range(random.randint(1, 4)):
                cm = ChatMessage(
                    sender_id=pair[0],
                    receiver_id=pair[1],
                    content=random.choice(CHAT_MSGS),
                    is_read=random.random() < 0.7,
                    created_at=rand_date(20),
                )
                db.session.add(cm)
                chat_count += 1
        db.session.commit()
        print(f"[OK] {chat_count} 条聊天消息\n")

        # ═══════════════════════════════════════════════════
        # 统计
        # ═══════════════════════════════════════════════════
        print("=" * 50)
        print("  🎉 种子数据填充完毕！")
        print("=" * 50)
        print(f"  用户:       {User.query.count()}")
        print(f"  论坛分区:   {ForumCategory.query.count()}")
        print(f"  论坛帖子:   {Post.query.count()}")
        print(f"  评论:       {Comment.query.count()}")
        print(f"  点赞:       {PostLike.query.count()}")
        print(f"  收藏:       {PostFavorite.query.count()}")
        print(f"  学习资料:   {Material.query.count()}")
        print(f"  资料评价:   {MaterialReview.query.count()}")
        print(f"  竞赛招募:   {Competition.query.count()}")
        print(f"  组队申请:   {Application.query.count()}")
        print(f"  二手闲置:   {Textbook.query.count()}")
        print(f"  好友关系:   {FriendRequest.query.count()}")
        print(f"  通知:       {Notification.query.count()}")
        print(f"  聊天消息:   {ChatMessage.query.count()}")
        print("=" * 50)
        print("\n📋 测试账号：")
        print("  管理员:  admin / admin123")
        print("  普通用户密码统一: 123456")
        print("  推荐登录用户体验：小明学长 / 图书馆小助手 / 考研上岸学姐")
        print(f"\n🌐 访问地址: http://localhost:5000")


if __name__ == "__main__":
    seed()
