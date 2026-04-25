import re

with open('sync.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 在原本处理 source 目录 git pull/push 的地方，加入对 hermes 目录的独立操作
# 目前的代码长这样：
#     rc_push, _, err_push = run_command("git push -u origin HEAD", path)
#     if rc_push == 0: ...

replacement = r'''
    # [源码区] Git 自动推拉
    rc, out, err = run_command("git pull --rebase", path)
    if rc == 0:
        if "Already up to date." not in out and "最新" not in out:
            log.append(f"在 {now} 成功拉取并应用了远程变更")
    else:
        log.append(f"拉取失败: {err}")

    rc_push, _, err_push = run_command("git push -u origin HEAD", path)
    if rc_push == 0:
        log.append(f"在 {now} 成功推送了变更")
    else:
        return False, f"推送失败: {err_push}"

    # [Hermes运行区] 独立的 Git 自动推拉
    # 既然两个文件夹都是独立从 Github 拉取，那么 Hermes 文件夹也需要做 git 操作
    if os.path.exists(hermes_path):
        if not os.path.exists(os.path.join(hermes_path, '.git')):
            # 如果不是 git 仓库，可能之前是 rsync 过去的物理文件夹。需要删掉用 clone 替代
            # 这里先不管，留给用户手动或之后自动化
            log.append(f"[警告] {hermes_path} 尚未初始化为 Git 仓库，无法同步最新版本。")
        else:
            rc_h, out_h, err_h = run_command("git pull --rebase", hermes_path)
            run_command("git push -u origin HEAD", hermes_path)
            if rc_h == 0 and "Already up to date." not in out_h:
                log.append(f"Hermes区在 {now} 成功更新了代码")
'''

# 替换原来的 `rc, out, err = run_command("git pull --rebase", path)` 及之后的推送部分
new_content = re.sub(
    r'    rc, out, err = run_command\("git pull --rebase", path\).*?return False, f"推送失败: \{err_push\}"',
    replacement,
    content,
    flags=re.DOTALL
)

with open('sync_new2.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
