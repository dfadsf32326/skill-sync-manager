# 自建技能库 GitHub 自动同步脚本需求文档

## 1. 项目背景
老板在 `/Users/robinlu/Self-established_skill` 目录下维护了多个自建的 Hermes 技能。为了确保代码安全及跨设备同步，需要一个自动化脚本定期将这些本地技能同步到 GitHub 个人仓库。

## 2. 核心目标
实现一个 Python 脚本，能够遍历指定目录，识别 Git 状态，并将更新自动推送到老板的 GitHub 账号 (`dfadsf32326`)。

## 3. 功能需求

### 3.1 目录扫描与过滤
- **基础路径**：`/Users/robinlu/Self-established_skill`。
- **排除名单**：明确排除 `create-ex` 文件夹（根据老板的隐私/特定规则要求）。
- **目标识别**：仅处理该路径下的第一级子文件夹。

### 3.2 Git 仓库管理
- **初始化**：若子文件夹下不存在 `.git` 目录，执行 `git init` 并创建对应的 GitHub 远程仓库（使用 `gh repo create`）。
- **远程校验**：
    - 检查 `origin` 是否存在。
    - 确保 `origin` 指向 `github.com/dfadsf32326/{folder_name}`。
    - 若指向第三方仓库，应先移除旧远程并重新绑定到老板的账号。
- **分支管理**：统一推送到 `main` 或 `master` 分支（以本地 HEAD 为准）。

### 3.3 同步逻辑
- **检测改动**：使用 `git status --porcelain` 检查是否有未提交的更改。
- **提交信息**：格式为 `Auto-sync: yyyy-mm-dd HH:MM:SS`。
- **推送策略**：执行 `git push -u origin HEAD`。

### 3.4 任务报告与通知
- **执行日志**：记录每个技能的同步结果（成功、跳过、失败原因）。
- **飞书通知**：同步任务结束后，通过 `lark-cli` 向老板发送一份结构化的执行报告。

## 4. 技术方案
- **语言**：Python 3。
- **依赖工具**：`git`, `gh` (GitHub CLI), `lark-cli`。
- **运行环境**：macOS。

## 5. 调度计划
- 使用 Hermes 内置的 `cronjob` 功能，建议设定为每天凌晨 02:00 或每 12 小时执行一次。

## 6. 安全与备份规则
- 在脚本部署前，不涉及 config.yaml 修改。
- 脚本仅操作指定的 Skill 目录，严禁触碰系统目录。
