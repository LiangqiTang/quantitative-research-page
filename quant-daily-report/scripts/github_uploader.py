"""
GitHub自动上传工具
负责将报告自动部署到GitHub Pages
"""

from github import Github
import os
from datetime import datetime
from typing import Optional
import base64

class GitHubUploader:
    def __init__(self, token: str, repo_name: str):
        self.g = Github(token)
        self.repo = self.g.get_repo(repo_name)

    def upload_report(self, file_path: str, commit_message: Optional[str] = None, branch: str = 'gh-pages'):
        """
        上传报告到GitHub Pages
        :param file_path: 报告文件路径
        :param commit_message: 提交消息
        :param branch: 目标分支（默认为gh-pages）
        """
        try:
            if not commit_message:
                commit_message = f"📈 Update daily report - {datetime.now().strftime('%Y-%m-%d')}"

            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 获取文件名
            file_name = os.path.basename(file_path)

            # 检查文件是否存在
            try:
                contents = self.repo.get_contents(file_name, ref=branch)
                # 更新现有文件
                self.repo.update_file(
                    contents.path,
                    commit_message,
                    content,
                    contents.sha,
                    branch=branch
                )
                print(f"✅ 成功更新文件: {file_name}")
            except:
                # 创建新文件
                self.repo.create_file(
                    file_name,
                    commit_message,
                    content,
                    branch=branch
                )
                print(f"✅ 成功创建文件: {file_name}")

            # 返回访问URL
            return f"https://{self.repo.owner.login}.github.io/{self.repo.name}/{file_name}"

        except Exception as e:
            print(f"❌ 文件上传失败: {e}")
            return None

    def upload_multiple_files(self, file_paths: list, commit_message: Optional[str] = None, branch: str = 'gh-pages'):
        """
        批量上传多个文件
        :param file_paths: 文件路径列表
        :param commit_message: 提交消息
        :param branch: 目标分支
        """
        try:
            if not commit_message:
                commit_message = f"📦 Update multiple reports - {datetime.now().strftime('%Y-%m-%d')}"

            results = []
            for file_path in file_paths:
                try:
                    url = self.upload_report(file_path, commit_message, branch)
                    results.append((file_path, url, 'success'))
                    # 避免过于频繁的请求
                    import time
                    time.sleep(1)
                except Exception as e:
                    results.append((file_path, str(e), 'failed'))

            # 打印上传结果
            print("\n📋 批量上传结果:")
            print("-" * 50)
            for file_path, result, status in results:
                if status == 'success':
                    print(f"✅ {file_path} - {result}")
                else:
                    print(f"❌ {file_path} - {result}")

            return results

        except Exception as e:
            print(f"❌ 批量上传失败: {e}")
            return []

    def upload_image(self, image_path: str, commit_message: Optional[str] = None, branch: str = 'gh-pages'):
        """
        上传图片文件
        :param image_path: 图片文件路径
        :param commit_message: 提交消息
        :param branch: 目标分支
        """
        try:
            if not commit_message:
                commit_message = f"🖼️ Update chart - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            # 读取二进制文件
            with open(image_path, 'rb') as f:
                content = f.read()

            # 编码为base64
            content_base64 = base64.b64encode(content).decode('utf-8')

            # 获取文件名
            file_name = os.path.basename(image_path)

            # 检查文件是否存在
            try:
                contents = self.repo.get_contents(file_name, ref=branch)
                # 更新现有文件
                self.repo.update_file(
                    contents.path,
                    commit_message,
                    content_base64,
                    contents.sha,
                    branch=branch,
                    encoding='base64'
                )
                print(f"✅ 成功更新图片: {file_name}")
            except:
                # 创建新文件
                self.repo.create_file(
                    file_name,
                    commit_message,
                    content_base64,
                    branch=branch,
                    encoding='base64'
                )
                print(f"✅ 成功创建图片: {file_name}")

            return f"https://{self.repo.owner.login}.github.io/{self.repo.name}/{file_name}"

        except Exception as e:
            print(f"❌ 图片上传失败: {e}")
            return None

    def setup_github_pages(self, source_branch: str = 'gh-pages', source_path: str = '/'):
        """
        配置GitHub Pages（如果尚未配置）
        :param source_branch: 源分支
        :param source_path: 源路径
        """
        try:
            # 检查是否已经配置
            pages_info = self.repo.get_pages()
            if pages_info:
                print(f"ℹ️ GitHub Pages已配置: {pages_info.html_url}")
                return pages_info.html_url

            # 如果没有配置，尝试配置
            print("🔧 正在配置GitHub Pages...")
            # 注意：PyGitHub库可能没有直接配置Pages的API
            # 这里需要调用REST API
            headers = {
                'Accept': 'application/vnd.github.switcheroo-preview+json'
            }
            data = {
                "source": {
                    "branch": source_branch,
                    "path": source_path
                }
            }

            # 使用REST API配置Pages
            self.repo._requester.requestJsonAndCheck(
                "POST",
                f"/repos/{self.repo.full_name}/pages",
                headers=headers,
                input=data
            )

            print("✅ GitHub Pages配置成功")
            return f"https://{self.repo.owner.login}.github.io/{self.repo.name}/"

        except Exception as e:
            print(f"⚠️ GitHub Pages配置失败: {e}")
            print("提示: 可能需要手动在GitHub仓库中配置Pages")
            return None

    def ensure_gh_pages_branch_exists(self):
        """
        确保gh-pages分支存在，如果不存在则创建
        """
        try:
            # 检查分支是否存在
            branches = [branch.name for branch in self.repo.get_branches()]
            if 'gh-pages' in branches:
                print("ℹ️ gh-pages分支已存在")
                return True

            # 如果不存在，从main分支创建一个空分支
            print("🔧 正在创建gh-pages分支...")

            # 获取main分支的最新提交
            main_branch = self.repo.get_branch('main')
            base_tree = main_branch.commit.commit.tree.sha

            # 创建一个空的提交树
            tree = self.repo.create_git_tree([], base_tree)

            # 创建提交
            commit = self.repo.create_git_commit(
                "🎉 Initial gh-pages commit",
                tree,
                [main_branch.commit.commit]
            )

            # 创建分支
            self.repo.create_git_ref('refs/heads/gh-pages', commit.sha)

            print("✅ gh-pages分支创建成功")
            return True

        except Exception as e:
            print(f"❌ gh-pages分支创建失败: {e}")
            print("提示: 可能需要手动创建gh-pages分支")
            return False

    def delete_old_reports(self, keep_days: int = 30, branch: str = 'gh-pages'):
        """
        删除旧报告，保留最近N天的报告
        :param keep_days: 保留天数
        :param branch: 目标分支
        """
        try:
            cutoff_date = datetime.now() - datetime.timedelta(days=keep_days)

            # 获取目录下的所有文件
            contents = self.repo.get_contents('', ref=branch)

            deleted_count = 0
            for content in contents:
                if content.type == 'file':
                    # 检查文件提交时间
                    commit = self.repo.get_commit(content.sha)
                    commit_date = commit.commit.committer.date

                    if commit_date < cutoff_date:
                        # 删除旧文件
                        self.repo.delete_file(
                            content.path,
                            f"🧹 Delete old report - {content.name}",
                            content.sha,
                            branch=branch
                        )
                        deleted_count += 1
                        print(f"🗑️ 删除旧文件: {content.name}")

            print(f"\n✅ 清理完成，共删除{deleted_count}个旧文件")
            return deleted_count

        except Exception as e:
            print(f"❌ 清理旧文件失败: {e}")
            return 0

    def verify_pages_accessibility(self, file_path: str = 'index.html', branch: str = 'gh-pages'):
        """
        验证GitHub Pages是否可访问
        :param file_path: 要验证的文件路径
        :param branch: 分支
        """
        import requests

        try:
            pages_url = f"https://{self.repo.owner.login}.github.io/{self.repo.name}/{file_path}"
            response = requests.get(pages_url, timeout=10)

            if response.status_code == 200:
                print(f"✅ GitHub Pages访问正常: {pages_url}")
                return pages_url, True
            else:
                print(f"❌ GitHub Pages访问失败，状态码: {response.status_code}")
                return pages_url, False

        except Exception as e:
            print(f"❌ GitHub Pages访问验证失败: {e}")
            return None, False

if __name__ == "__main__":
    # 测试代码
    import os
    from dotenv import load_dotenv

    # 加载环境变量
    load_dotenv()

    github_token = os.getenv('GITHUB_TOKEN')
    github_repo = os.getenv('GITHUB_REPO')

    if github_token and github_repo:
        uploader = GitHubUploader(github_token, github_repo)

        # 测试上传
        test_file = 'test_report.html'
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('''
        <html>
        <body>
            <h1>Test Report</h1>
            <p>This is a test report.</p>
        </body>
        </html>
        ''')

        # 上传测试文件
        result = uploader.upload_report(test_file)
        print(f"上传结果: {result}")

        # 测试清理
        uploader.delete_old_reports(keep_days=1)

        # 验证访问
        uploader.verify_pages_accessibility('test_report.html')