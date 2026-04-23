import os
import subprocess
import datetime
from pathlib import Path

# --- 配置区 ---
BASE_PATH = "/Users/robinlu/Self-established_skill"
GH_USER = "dfadsf32326"
EXCLUDE_DIRS = ["create-ex"] # 排除名单
LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
HERMES_CUSTOM_SKILLS_PATH = os.path.expanduser("~/.hermes/skills/custom")
WORKBUDDY_SKILLS_PATH = os.path.expanduser("~/.workbuddy/skills")

def run_command(cmd, workdir=None):
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=workdir, capture_output=True, text=True, timeout=60
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def ensure_symlink(skill_name):
    """确保 Self-established_skill 中的 skill 在 ~/.workbuddy/skills/ 下有正确的软链接"""
    src = os.path.join(BASE_PATH, skill_name)
    dst = os.path.join(WORKBUDDY_SKILLS_PATH, skill_name)
    log = []

    # 确保目标目录存在
    if not os.path.exists(WORKBUDDY_SKILLS_PATH):
        os.makedirs(WORKBUDDY_SKILLS_PATH, exist_ok=True)

    # 目标已经是正确的软链接
    if os.path.islink(dst):
        current_target = os.readlink(dst)
        if current_target == src:
            return log  # 已经正确，无需操作
        else:
            # 软链接指向错误，删除重建
            os.remove(dst)
            os.symlink(src, dst)
            log.append(f"修正软链接: {dst} -> {src}")
            return log

    # 目标是实体目录（非软链接），备份后替换
    if os.path.isdir(dst):
        backup_name = f"{dst}.backup.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(dst, backup_name)
        os.symlink(src, dst)
        log.append(f"备份实体目录并创建软链接: {dst} -> {src} (备份: {backup_name})")
        return log

    # 目标不存在，直接创建软链接
    os.symlink(src, dst)
    log.append(f"创建软链接: {dst} -> {src}")
    return log


def sync_skill(skill_name):
    path = os.path.join(BASE_PATH, skill_name)
    log = []

    # 0. 实体双向同步归集 (取代经常失效的软链接)
    # 比较 ~/.hermes/skills/custom/ 和 Git 源目录，自动合并最新的文件修改
    hermes_path = os.path.join(HERMES_CUSTOM_SKILLS_PATH, skill_name)

    # 清理过去遗留的软链接，改为物理文件夹，解决软链无法稳定加载的问题
    if os.path.islink(hermes_path):
        run_command(f"rm -f {hermes_path}")

    if not os.path.exists(hermes_path):
        run_command(f"mkdir -p {hermes_path}")

    # 双向合并 (rsync -au 利用文件修改时间，永远保留最新版本):
    # 第一步：把 hermes 目录中较新的修改（比如平时运行调试时改的）抽回 Git 仓库
    run_command(f"rsync -au --exclude='.git' {hermes_path}/ {path}/")
    # 第二步：把 Git 仓库中较新的修改（比如老板直接编辑源码时改的）反向对齐给 hermes
    run_command(f"rsync -au --exclude='.git' {path}/ {hermes_path}/")
    log.append("物理归集并双向同步了 custom 目录代码")

    # 1.1 确保 workbuddy skills 软链接
    symlink_logs = ensure_symlink(skill_name)
    log.extend(symlink_logs)

    # 1. 检查 Git 初始化
    if not os.path.exists(os.path.join(path, ".git")):
        run_command("git init", path)
        log.append("初始化 Git 完成")

    # 2. 检查 GitHub 仓库与 Remote
    rc, stdout, stderr = run_command(f"gh repo view {GH_USER}/{skill_name}", path)
    if rc != 0:
        # 仓库不存在则创建
        run_command(f"gh repo create {skill_name} --public", path)
        run_command(f"git remote add origin https://github.com/{GH_USER}/{skill_name}.git", path)
        log.append("创建了 GitHub 仓库并绑定了 origin")
    else:
        # 检查 origin 是否正确
        rc_rem, remotes, _ = run_command("git remote -v", path)
        if f"{GH_USER}/{skill_name}" not in remotes:
            run_command("git remote remove origin", path)
            run_command(f"git remote add origin https://github.com/{GH_USER}/{skill_name}.git", path)
            log.append("已将 origin 修正为老板的个人账号")

    # 3. 检查改动并提交
    _, status, _ = run_command("git status --porcelain", path)
    if status:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_command("git add .", path)
        run_command(f"git commit -m '自动同步: {now}'", path)
        # 推送
        rc_push, _, err_push = run_command("git push -u origin HEAD", path)
        if rc_push == 0:
            log.append(f"在 {now} 成功推送了变更")
            return True, " | ".join(log)
        else:
            return False, f"推送失败: {err_push}"
    else:
        return True, "没有发现变更"

def send_lark_report(report_lines):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = f"技能自动同步报告 ({now})"
    # 转换为飞书列表格式
    content = "\n".join([f"* {line}" for line in report_lines])
    msg = f"{title}\n........................\n{content}"
    
    # 使用 lark-cli 发送，发送到 Home 频道
    cmd = f"{LARK_CLI} im send --chat-id oc_50ecab6ff9d621208e8a0c8030d8bf8c --text {msg!r}"
    run_command(cmd)

if __name__ == "__main__":
    skills = [d for d in os.listdir(BASE_PATH) 
              if os.path.isdir(os.path.join(BASE_PATH, d)) and d not in EXCLUDE_DIRS]
    
    reports = []
    for skill in skills:
        success, info = sync_skill(skill)
        status_icon = "✅" if success else "❌"
        if info != "没有发现变更" or not success:
            reports.append(f"{status_icon} **{skill}**: {info}")
    
    if reports:
        send_lark_report(reports)
    else:
        print("所有技能都是最新的，没有变更，未发送飞书报告。")
