-- 校桥 CampusBridge 数据库初始化脚本
-- 注意：SQLAlchemy 会自动建表，此脚本供手动备用

CREATE DATABASE IF NOT EXISTS campus_bridge
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE campus_bridge;

-- 表结构由 SQLAlchemy ORM 自动创建，启动 app.py 即可
-- python app.py 会自动调用 db.create_all() 并在首次运行时创建管理员账号

-- 手动创建管理员（可选）:
-- INSERT INTO users (username, email, password_hash, role, created_at)
-- VALUES ('admin', 'admin@campusbridge.com', '<hash>', 'admin', NOW());

-- ============================================================
-- 下方为四个对话/群聊相关表的建表语句（供手动建库时使用）
-- ============================================================

-- 组队对话：申请人与发起人之间的多轮私聊消息
CREATE TABLE IF NOT EXISTS conversation_messages (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    competition_id  INT          NOT NULL,
    application_id  INT          NOT NULL,
    sender_id       INT          NOT NULL,
    content         TEXT         NOT NULL,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_conv_competition FOREIGN KEY (competition_id) REFERENCES competitions(id) ON DELETE CASCADE,
    CONSTRAINT fk_conv_application FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    CONSTRAINT fk_conv_sender      FOREIGN KEY (sender_id)      REFERENCES users(id)         ON DELETE CASCADE,
    INDEX idx_conv_app (application_id, id),
    INDEX idx_conv_comp (competition_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 竞赛交流群：一个竞赛对应一个交流群
CREATE TABLE IF NOT EXISTS team_groups (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    competition_id  INT          NOT NULL UNIQUE,
    name            VARCHAR(200) NOT NULL,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_group_competition FOREIGN KEY (competition_id) REFERENCES competitions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 交流群成员
CREATE TABLE IF NOT EXISTS group_members (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    group_id    INT      NOT NULL,
    user_id     INT      NOT NULL,
    joined_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_gm_group FOREIGN KEY (group_id) REFERENCES team_groups(id) ON DELETE CASCADE,
    CONSTRAINT fk_gm_user  FOREIGN KEY (user_id)  REFERENCES users(id)       ON DELETE CASCADE,
    UNIQUE KEY uq_group_user (group_id, user_id),
    INDEX idx_gm_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 交流群消息
CREATE TABLE IF NOT EXISTS group_messages (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    group_id    INT      NOT NULL,
    sender_id   INT      NOT NULL,
    content     TEXT     NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_gmsg_group  FOREIGN KEY (group_id)  REFERENCES team_groups(id) ON DELETE CASCADE,
    CONSTRAINT fk_gmsg_sender FOREIGN KEY (sender_id) REFERENCES users(id)       ON DELETE CASCADE,
    INDEX idx_gmsg_group (group_id, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 迁移：textbooks 表新增 description_images 字段（描述图片，逗号分隔多 key）
-- 如果已存在字段会报错（Duplicate column），可忽略
-- ============================================================
ALTER TABLE textbooks ADD COLUMN description_images TEXT AFTER cover_image;

-- ============================================================
-- 迁移：materials 表新增 views 字段（浏览量），与 downloads（下载量）分开
-- ============================================================
ALTER TABLE materials ADD COLUMN views INTEGER DEFAULT 0;

-- ============================================================
-- 迁移：创建 friend_requests 表（好友关系系统）
-- ============================================================
CREATE TABLE IF NOT EXISTS friend_requests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id   INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    status      VARCHAR(20) DEFAULT 'pending',
    message     VARCHAR(200),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(sender_id) REFERENCES users(id),
    FOREIGN KEY(receiver_id) REFERENCES users(id),
    UNIQUE(sender_id, receiver_id)
);

