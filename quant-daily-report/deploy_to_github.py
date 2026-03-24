#!/usr/bin/env python3
"""
部署量化报告到GitHub Pages
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

try:
    from github import Github, GithubException
except ImportError:
    print("⚠️  PyGithub 未安装，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyGithub"])
    from github import Github, GithubException


def load_env():
    """加载环境变量"""
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        print(f"❌ 环境变量文件不存在: {env_file}")
        return None, None

    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    token = env_vars.get('GITHUB_TOKEN')
    repo = env_vars.get('GITHUB_REPO')

    if not token:
        print("❌ 未找到 GITHUB_TOKEN")
        return None, None
    if not repo:
        print("❌ 未找到 GITHUB_REPO")
        return None, None

    return token, repo


def deploy_report():
    """部署报告到GitHub"""
    print("=" * 60)
    print("🚀 开始部署到GitHub Pages")
    print("=" * 60)

    # 加载配置
    token, repo_name = load_env()
    if not token or not repo_name:
        return False

    # 检查报告文件
    report_file = Path(__file__).parent / 'quant_output' / 'quant_report.html'
    if not report_file.exists():
        print(f"❌ 报告文件不存在: {report_file}")
        print("请先运行 main_quant_system.py 生成报告")
        return False

    print(f"✅ 找到报告文件: {report_file}")

    try:
        # 连接GitHub
        print(f"🔗 连接到GitHub仓库: {repo_name}")
        g = Github(token)
        repo = g.get_repo(repo_name)

        # 读取报告内容
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 尝试创建或更新 index.html
        commit_message = f"更新量化报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        try:
            # 尝试获取现有文件
            contents = repo.get_contents("index.html")
            print("📝 更新现有 index.html...")
            repo.update_file(
                "index.html",
                commit_message,
                content,
                contents.sha,
                branch="main"
            )
        except GithubException as e:
            if e.status == 404:
                # 文件不存在，创建新文件
                print("📝 创建新 index.html...")
                repo.create_file(
                    "index.html",
                    commit_message,
                    content,
                    branch="main"
                )
            else:
                raise

        print("✅ 报告已成功上传到GitHub!")
        print(f"📊 查看地址: https://{repo_name.split('/')[0]}.github.io/{repo_name.split('/')[1]}/")
        print("=" * 60)
        return True

    except GithubException as e:
        print(f"❌ GitHub API错误: {e}")
        if e.status == 401:
            print("   请检查 GITHUB_TOKEN 是否正确")
        elif e.status == 404:
            print(f"   请检查仓库名称是否正确: {repo_name}")
        return False
    except Exception as e:
        print(f"❌ 部署失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = deploy_report()
    sys.exit(0 if success else 1)
