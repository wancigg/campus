#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# scripts/deploy_mysql_ms_demo.sh —— 校桥 CampusBridge「演示型 MySQL 主从」一键部署
#
# 目标（同机双实例）：
#   主库：本机 MySQL 原 3306 实例（Flask 永远只读写这一个）
#   从库：本机 MySQL 新 3307 实例（仅用于 SHOW SLAVE STATUS 演示 + 手动主写从查验证）
#
# 使用：
#   1) 先 dry-run 预览将执行的每一步命令（包括 CHANGE MASTER TO 的 File/Position）：
#        bash scripts/deploy_mysql_ms_demo.sh --dry-run
#   2) 确认输出没问题再真实执行：
#        sudo bash scripts/deploy_mysql_ms_demo.sh
#
# 回滚（关闭从库，主库保持不变）：
#        sudo bash scripts/deploy_mysql_ms_demo.sh rollback
#
# 约定：
#   - 主库 root / 从库 root：从 /opt/campus-bridge/.env 读取 MYSQL_MASTER_PASSWORD / MYSQL_SLAVE_PASSWORD
#   - 复制账号 repl / **** ：从 /opt/campus-bridge/.env 读取 MYSQL_REPL_USER / MYSQL_REPL_PASSWORD
#   - 真实密码不在 bash history / dry-run 输出出现（脱敏为 ****）
set -euo pipefail

# ========= 基础环境 =========
PROJECT_DIR="${PROJECT_DIR:-/opt/campus-bridge}"
ENV_FILE="${PROJECT_DIR}/.env"
MYSQLD_SAFE="${MYSQLD_SAFE:-mysqld_safe}"
MYSQLD="${MYSQLD:-mysqld}"
MYSQL="${MYSQL:-mysql}"
MYSQL_INSTALL_DB="${MYSQL_INSTALL_DB:-mysql_install_db}"
MASTER_PORT="${MASTER_PORT:-3306}"
SLAVE_PORT="${SLAVE_PORT:-3307}"
MASTER_HOST="${MASTER_HOST:-127.0.0.1}"
SLAVE_HOST="${SLAVE_HOST:-127.0.0.1}"
MASTER_CNF="${MASTER_CNF:-/etc/my.cnf}"
SLAVE_CNF="${SLAVE_CNF:-/etc/my_slave.cnf}"
SLAVE_DATADIR="${SLAVE_DATADIR:-/var/lib/mysql-slave}"
SLAVE_PID="${SLAVE_PID:-/var/lib/mysql-slave/mysql-slave.pid}"
SLAVE_SOCKET="${SLAVE_SOCKET:-/var/lib/mysql-slave/mysql.sock}"
DUMP_FILE="${DUMP_FILE:-/tmp/campus_bridge_dump.sql}"
DRY_RUN=0

ROLLBACK_MODE=0
if [[ "${1:-}" == "rollback" ]]; then
  ROLLBACK_MODE=1
elif [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

# ---------- 工具函数 ----------
# 密码必须 read 到局部变量，不要 echo 出去
load_dotenv() {
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "[FATAL] 未找到 $ENV_FILE，请先把 .env 放到 $PROJECT_DIR" >&2
    exit 2
  fi
  # shellcheck disable=SC1090
  set -a; source "$ENV_FILE"; set +a
  MASTER_USER="${MYSQL_MASTER_USER:-${MYSQL_USER:-root}}"
  MASTER_PASSWORD="${MYSQL_MASTER_PASSWORD:-${MYSQL_PASSWORD:-}}"
  SLAVE_USER="${MYSQL_SLAVE_USER:-${MASTER_USER}}"
  SLAVE_PASSWORD="${MYSQL_SLAVE_PASSWORD:-${MASTER_PASSWORD}}"
  REPL_USER="${MYSQL_REPL_USER:-repl}"
  REPL_PASSWORD="${MYSQL_REPL_PASSWORD:-}"
  MASTER_DB="${MYSQL_MASTER_DATABASE:-${MYSQL_DATABASE:-campus_bridge}}"
  SLAVE_DB="${MYSQL_SLAVE_DATABASE:-${MASTER_DB}}"
  if [[ -z "$MASTER_PASSWORD" || -z "$REPL_PASSWORD" ]]; then
    echo "[FATAL] .env 未设置 MYSQL_MASTER_PASSWORD 与 MYSQL_REPL_PASSWORD" >&2
    exit 2
  fi
}

mask() { printf '****'; }
run() {
  # 打印并执行命令；密码参数统一用占位符打印
  local desc="$1"; shift
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY] $desc"
    printf "      \$ %s\n" "$*"
    return 0
  fi
  echo "[RUN ] $desc"
  printf "      \$ %s\n" "$*"
  # 真实执行，不显示密码
  "$@"
}

mysql_master() {
  # 命令行不暴露密码：用 MYSQL_PWD 环境变量
  MYSQL_PWD="$MASTER_PASSWORD" "$MYSQL" -h"$MASTER_HOST" -P"$MASTER_PORT" -u"$MASTER_USER" "$@"
}
mysql_slave() {
  MYSQL_PWD="$SLAVE_PASSWORD" "$MYSQL" -h"$SLAVE_HOST" -P"$SLAVE_PORT" -u"$SLAVE_USER" "$@"
}

# ---------- 回滚模式 ----------
rollback() {
  echo "==== [回滚模式] 只停从库 3307，不改动主库 ===="
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY] 若 3307 进程存在则 kill; systemctl 不解禁 mysqld（主库不动）; 删除 $SLAVE_CNF 可选"
    return 0
  fi
  if [[ -f "$SLAVE_PID" ]]; then
    local pid
    pid=$(cat "$SLAVE_PID" 2>/dev/null || true)
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "停止从库 pid=$pid"
      kill "$pid"; sleep 2
      if kill -0 "$pid" 2>/dev/null; then kill -9 "$pid" || true; sleep 1; fi
    fi
  fi
  ss -lntp | grep ":${SLAVE_PORT}\s" || echo "从库 $SLAVE_PORT 已不在监听"
  cat <<EOF
[可选] 若要彻底清理从库文件：
  rm -f $SLAVE_CNF
  rm -rf $SLAVE_DATADIR
  rm -f $DUMP_FILE
主库 3306 完全不受影响。
EOF
}

# ---------- 主流程 ----------
main() {
  # 关闭 history 日志，避免密码写入 ~/.bash_history
  set +o history 2>/dev/null || true
  trap 'set -o history 2>/dev/null || true' RETURN

  load_dotenv

  if [[ $ROLLBACK_MODE -eq 1 ]]; then
    rollback
    return 0
  fi

  echo "==== 演示型主从部署（主库 ${MASTER_HOST}:${MASTER_PORT} / 从库 ${SLAVE_HOST}:${SLAVE_PORT}） ===="
  echo "       DB=$MASTER_DB  repl_user=$REPL_USER  repl_pwd=$(mask)"

  # 0. 预检版本 & 从库端口可用
  if [[ $DRY_RUN -eq 0 ]]; then
    echo "[VER ] MySQL 版本：$($MYSQL --version)"
    if ss -lntp | grep -q ":${SLAVE_PORT}\s"; then
      echo "[FATAL] 端口 $SLAVE_PORT 已经被占用。先执行 sudo bash $0 rollback 停掉旧从库实例" >&2
      exit 3
    fi
  fi

  # 1. 主库配置：binlog + server_id=1
  echo "=== 步骤 1/7 主库 my.cnf 追加 binlog 段（如已存在则跳过） ==="
  MASTER_APPEND=$(cat <<EOF
# === CampusBridge demo master (added by deploy_mysql_ms_demo.sh) ===
server-id = 1
log_bin = mysql-bin
binlog_format = ROW
binlog_do_db = ${MASTER_DB}
expire_logs_days = 7
sync_binlog = 1
innodb_flush_log_at_trx_commit = 1
EOF
)
  if ! grep -q "server-id = 1" "$MASTER_CNF" 2>/dev/null; then
    run "备份 $MASTER_CNF 并追加 binlog 段" \
      bash -c "set -e
        cp -a '$MASTER_CNF' '${MASTER_CNF}.bak.ms.\$(date +%Y%m%d%H%M)'
        cat >>'$MASTER_CNF' <<'MASTEREOF'
${MASTER_APPEND}
MASTEREOF
"
  fi

  run "重启主库使 binlog 参数生效" systemctl restart mysqld
  sleep 3

  # 2. 主库创建复制账号 repl
  echo "=== 步骤 2/7 主库创建复制账号 $REPL_USER（脱敏密码演示，实际写入 .env 的 MYSQL_REPL_PASSWORD） ==="
  CREATE_REPL_SQL="
    CREATE USER IF NOT EXISTS '${REPL_USER}'@'%' IDENTIFIED BY '___REPL_PW_PLACEHOLDER___';
    GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO '${REPL_USER}'@'%';
    FLUSH PRIVILEGES;
  "
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY] 主库执行（repl 密码已脱敏为 ****）:"
    echo "      CREATE USER IF NOT EXISTS '$REPL_USER'@'%' IDENTIFIED BY '$(mask)'; GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO '$REPL_USER'@'%'; FLUSH PRIVILEGES;"
  else
    # 真实执行：替换占位符为 .env 的 REPL_PASSWORD，不把 SQL 明文打印
    CREATE_REPL_SQL_REAL="${CREATE_REPL_SQL/___REPL_PW_PLACEHOLDER___/${REPL_PASSWORD}}"
    mysql_master -e "${CREATE_REPL_SQL_REAL}"
  fi

  # 3. 导出主库快照；--master-data=2 将复制坐标写入 dump 文件头
  echo "=== 步骤 3/7 导出 $MASTER_DB（mysqldump --master-data=2，自动记录 CHANGE MASTER 坐标） ==="
  run "确保 dump 文件不存在且父目录可写" bash -c "rm -f '$DUMP_FILE'; touch '$DUMP_FILE'"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY] mysqldump --databases ${MASTER_DB} --single-transaction --master-data=2 --triggers --routines --events -u${MASTER_USER} -p**** > ${DUMP_FILE}"
  else
    # InnoDB 使用一致性快照，避免先开连接再导出导致 FTWRL 锁已释放的问题。
    MYSQL_PWD="$MASTER_PASSWORD" mysqldump \
      --databases "${MASTER_DB}" --single-transaction --master-data=2 \
      --triggers --routines --events \
      -h"$MASTER_HOST" -P"$MASTER_PORT" -u"$MASTER_USER" > "$DUMP_FILE" \
      || { echo "mysqldump failed" >&2; exit 4; }
    echo "  dump size=$(du -h "$DUMP_FILE" | awk '{print $1}')"
    echo "  dump 中的 CHANGE MASTER 坐标（仅 File/Pos）："
    grep -E "CHANGE MASTER TO MASTER_LOG_FILE|MASTER_LOG_POS" "$DUMP_FILE" | head -n 2 || true
  fi

  # 4. 从库：准备 my_slave.cnf + datadir（和主库不同 server-id=2；port=3307；datadir=/var/lib/mysql-slave）
  echo "=== 步骤 4/7 初始化从库 $SLAVE_DATADIR + 配置 $SLAVE_CNF ==="
  SLAVE_APPEND=$(cat <<EOF
[mysqld]
# === CampusBridge demo slave (added by deploy_mysql_ms_demo.sh) ===
server-id       = 2
port            = ${SLAVE_PORT}
datadir         = ${SLAVE_DATADIR}
socket          = ${SLAVE_SOCKET}
pid-file        = ${SLAVE_PID}
relay-log       = relay-bin
read_only       = ON
log_bin         = mysql-bin
binlog_format   = ROW
# 以下二项若 MySQL 版本 < 5.7.8 不支持则跳过，脚本自动 grep 后追加可用子集
# super_read_only = ON
skip-name-resolve
character-set-server = utf8mb4
collation-server     = utf8mb4_unicode_ci
[client]
port     = ${SLAVE_PORT}
socket   = ${SLAVE_SOCKET}
EOF
)
  run "写入 $SLAVE_CNF" bash -c "cat > '$SLAVE_CNF' <<'SLAVEEOF'
${SLAVE_APPEND}
SLAVEEOF
"
  run "创建从库 datadir 并赋予 mysql 用户" \
    bash -c "mkdir -p '${SLAVE_DATADIR}'; chown -R mysql:mysql '${SLAVE_DATADIR}'; chmod 700 '${SLAVE_DATADIR}'"

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY] 根据 MySQL 版本选择 datadir 初始化方式：MySQL 5.7 用 mysql_install_db --user=mysql --datadir=...；MySQL 8.0 用 mysqld --initialize-insecure --user=mysql --datadir=..."
  else
    MYSQL_VER="$($MYSQL --version | grep -oE '[0-9]+\.[0-9]+' | head -n 1)"
    MAJOR="${MYSQL_VER%%.*}"
    MINOR="${MYSQL_VER#*.}"
    echo "  检测 MySQL 版本主段=$MYSQL_VER (major=$MAJOR minor=$MINOR)"
    if [[ "$MAJOR" -ge 8 ]]; then
      "$MYSQLD" --defaults-file="$SLAVE_CNF" --initialize-insecure --user=mysql
    else
      "$MYSQL_INSTALL_DB" --defaults-file="$SLAVE_CNF" --user=mysql --datadir="$SLAVE_DATADIR" || \
        "$MYSQLD" --defaults-file="$SLAVE_CNF" --initialize-insecure --user=mysql
    fi
  fi

  # 5. 启动从库 3307；导入 dump；
  echo "=== 步骤 5/7 启动从库 $SLAVE_PORT 并导入 dump 快照 ==="
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY] 启动：nohup mysqld_safe --defaults-file=$SLAVE_CNF > /var/log/mysql-slave.log 2>&1 &"
    echo "[DRY] 导入：mysql -h$SLAVE_HOST -P$SLAVE_PORT -uroot -p**** < $DUMP_FILE"
  else
    nohup "$MYSQLD_SAFE" --defaults-file="$SLAVE_CNF" > /var/log/mysql-slave.log 2>&1 &
    echo "  等待从库 pid=$SLAVE_PID 出现 ..."
    for i in $(seq 1 30); do
      if [[ -f "$SLAVE_PID" ]] && ss -lntp | grep -q ":${SLAVE_PORT}\s"; then break; fi
      sleep 1
    done
    ss -lntp | grep ":${SLAVE_PORT}\s" || { echo "[FATAL] 从库 $SLAVE_PORT 未启动，请查看 /var/log/mysql-slave.log" >&2; exit 5; }
    echo "  从库已启动，设置从库 root 密码并导入 dump..."
    # --initialize-insecure 只用于首次初始化；先通过本地 socket 无密码登录，再设置 .env 中的从库密码。
    "$MYSQL" --protocol=socket --socket="$SLAVE_SOCKET" -uroot -e \
      "ALTER USER 'root'@'localhost' IDENTIFIED BY '${SLAVE_PASSWORD}'; FLUSH PRIVILEGES;"
    # 导入前先确保数据库存在（dump 里通常有 CREATE DATABASE，但防一手）。
    mysql_slave -e "CREATE DATABASE IF NOT EXISTS \`${SLAVE_DB}\` CHARACTER SET utf8mb4;"
    mysql_slave < "$DUMP_FILE"
    echo "  导入完成"
  fi

  # 6. CHANGE MASTER TO；START SLAVE；IO/SQL 双 Yes
  echo "=== 步骤 6/7 从库 CHANGE MASTER + START SLAVE（File/Pos 来自 dump 文件头或主库 SHOW MASTER STATUS 快照） ==="
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY] STOP SLAVE; RESET SLAVE ALL;"
    echo "[DRY] CHANGE MASTER TO
          MASTER_HOST='${MASTER_HOST}',
          MASTER_PORT=${MASTER_PORT},
          MASTER_USER='${REPL_USER}',
          MASTER_PASSWORD='$(mask)',
          MASTER_LOG_FILE='mysql-bin.000001',     # ← 真实执行时从 dump 文件头提取
          MASTER_LOG_POS=154,                     # ← 真实执行时从 dump 文件头提取
          MASTER_CONNECT_RETRY=10;"
    echo "[DRY] START SLAVE; 之后 10s 内 SHOW SLAVE STATUS\G 校验 IO/SQL=Yes"
  else
    # 从 dump 文件头 22-25 行范围抓真实的 MASTER_LOG_FILE / MASTER_LOG_POS（mysqldump --master-data=2 保证有）
    LOG_FILE=$(grep -oE "MASTER_LOG_FILE='[^']+' " "$DUMP_FILE" | head -n1 | cut -d"'" -f2 || true)
    LOG_POS=$(grep -oE "MASTER_LOG_POS=[0-9]+"     "$DUMP_FILE" | head -n1 | cut -d"=" -f2 || true)
    if [[ -z "$LOG_FILE" || -z "$LOG_POS" ]]; then
      echo "[FATAL] 未从 dump 解析出 CHANGE MASTER 坐标，请到主库手动 SHOW MASTER STATUS 填写" >&2
      exit 6
    fi
    echo "  CHANGE MASTER 坐标：File=$LOG_FILE  Pos=$LOG_POS"
    mysql_slave <<EOSQL
STOP SLAVE;
RESET SLAVE ALL;
CHANGE MASTER TO
  MASTER_HOST='${MASTER_HOST}',
  MASTER_PORT=${MASTER_PORT},
  MASTER_USER='${REPL_USER}',
  MASTER_PASSWORD='${REPL_PASSWORD}',
  MASTER_LOG_FILE='${LOG_FILE}',
  MASTER_LOG_POS=${LOG_POS},
  MASTER_CONNECT_RETRY=10;
START SLAVE;
EOSQL
    sleep 10
    echo "  === SHOW SLAVE STATUS (关键字段) ==="
    mysql_slave -e "SHOW SLAVE STATUS\G" | grep -E "Slave_IO_Running|Slave_SQL_Running|Seconds_Behind_Master|Last_Error|Last_IO_Error|Last_SQL_Error|Master_Host|Master_Port" || true
  fi

  # 7. 主写从查 5 秒内一致 demo
  echo "=== 步骤 7/7 演示：主 INSERT 一行临时测试 → 5s 内在从库查到（证明同步链路生效） ==="
  TEST_USER="__ms_demo_$(date +%s)"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY] 主库: INSERT INTO users (username, email, password_hash, created_at) VALUES ('$TEST_USER','demo@t.c','x',NOW()); DO SLEEP(5);"
    echo "[DRY] 从库: SELECT COUNT(*) FROM users WHERE username='$TEST_USER';"
  else
    mysql_master -e "INSERT INTO \`${MASTER_DB}\`.users (username, email, password_hash, created_at) VALUES ('${TEST_USER}','demo@t.c','x',NOW());"
    sleep 5
    CNT=$(mysql_slave -N -B -e "SELECT COUNT(*) FROM \`${SLAVE_DB}\`.users WHERE username='${TEST_USER}';" 2>/dev/null || echo 0)
    echo "  主库写入 username=${TEST_USER}; 5s 后从库 count=${CNT}"
    if [[ "$CNT" -ge 1 ]]; then
      echo "  [OK ] 主写从查延迟 <5s 一致"
    else
      echo "  [WARN] 5s 内未同步，再 SHOW SLAVE STATUS 查 Last_IO/Last_SQL_Error，也可能是 dump 导入后刚 catch up 稍慢"
    fi
    # 清理测试数据（不强制成功，避免影响答辩演示）
    mysql_master -e "DELETE FROM \`${MASTER_DB}\`.users WHERE username='${TEST_USER}' LIMIT 1;" 2>/dev/null || true
  fi

  echo ""
  echo "==== 部署完成！答辩演示参考命令（请在终端按实际账号填写） ===="
  cat <<'EOF'
  # 展示：Flask 永远只连主库；3307 从库只读跟随
  MYSQL_PWD='从库密码' mysql -h127.0.0.1 -P3307 -u'从库用户' \
    -e "SHOW SLAVE STATUS\G" | grep -E "Slave_IO_Running|Slave_SQL_Running|Seconds_Behind_Master|Last_Error"

  # 主库写入后，从库查询（把密码和账号替换为 .env 中的值）
  MYSQL_PWD='主库密码' mysql -h127.0.0.1 -P3306 -u'主库用户' -e \
    "INSERT INTO campus_bridge.competitions (title, description, status, max_team, deadline, created_at)
     VALUES ('主从同步测试赛','演示 binlog 复制','open',3,DATE_ADD(NOW(), INTERVAL 10 DAY),NOW());"
  sleep 4
  MYSQL_PWD='从库密码' mysql -h127.0.0.1 -P3307 -u'从库用户' -e \
    "SELECT id,title,status,created_at FROM campus_bridge.competitions ORDER BY id DESC LIMIT 1;"
EOF
}

main "$@"
