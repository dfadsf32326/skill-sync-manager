import re

with open('sync.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到 rsync 那一段并将其注释/删除
# 1. 删除 `if os.path.islink(hermes_path):` 及相关的 rsync 块，由于代码可能比较长，我们直接通过正则表达式替换

new_content = re.sub(
    r'(?<=def sync_skill\(skill_name\):).*?(?=# 1\.1 确保 workbuddy skills 软链接)',
    r'''
    path = os.path.join(BASE_PATH, skill_name)
    log = []
    
    # [架构调整] 移除了原有的 rsync 物理横向双向同步。
    # 现要求 hermes 目录和 source 目录各自作为独立的 git 仓库，通过统一 push/pull 维持同步。
    
    hermes_path = os.path.join(HERMES_CUSTOM_SKILLS_PATH, skill_name)
    
    # 兼容清理：如果曾经是软链接，先删掉，但这部分以后应该由开发者自行通过 git clone 重建
    if os.path.islink(hermes_path):
        run_command(f"rm -f {hermes_path}")
        
''',
    content,
    flags=re.DOTALL
)

with open('sync_new.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
