"""
告警工具模块
负责发送系统告警信息
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import os
import pandas as pd

class AlertSender:
    """告警发送器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._init_alert_config()

    def _init_alert_config(self):
        """初始化告警配置"""
        # 从配置获取邮箱设置
        self.email_enabled = self.config.get('automation', {}).get('alert', {}).get('enabled', False)
        self.smtp_server = self.config.get('automation', {}).get('alert', {}).get('smtp_server', '')
        self.smtp_port = self.config.get('automation', {}).get('alert', {}).get('smtp_port', 587)
        self.smtp_username = self.config.get('automation', {}).get('alert', {}).get('smtp_username', '')
        self.smtp_password = self.config.get('automation', {}).get('alert', {}).get('smtp_password', '')
        self.alert_email = self.config.get('automation', {}).get('alert', {}).get('email', '')

        # 如果配置中没有，尝试从环境变量获取
        if not self.smtp_server:
            self.smtp_server = os.getenv('SMTP_SERVER', '')
        if not self.smtp_port:
            self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        if not self.smtp_username:
            self.smtp_username = os.getenv('SMTP_USERNAME', '')
        if not self.smtp_password:
            self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        if not self.alert_email:
            self.alert_email = os.getenv('ALERT_EMAIL', '')

    def send_alert(self, title: str, content: str) -> bool:
        """
        发送告警信息
        :param title: 告警标题
        :param content: 告警内容
        :return: 是否发送成功
        """
        try:
            # 检查告警是否启用
            if not self.email_enabled:
                print(f"⚠️ 告警功能未启用，忽略告警: {title}")
                return False

            # 检查配置是否完整
            if not all([self.smtp_server, self.smtp_username,
                       self.smtp_password, self.alert_email]):
                print("⚠️ 告警配置不完整，无法发送告警")
                return False

            # 构造邮件
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.alert_email
            msg['Subject'] = f"📊 量化日报系统告警 - {title}"

            # 添加邮件内容
            body = f"""<html>
            <body>
                <h3>{title}</h3>
                <pre>{content}</pre>
                <p>📅 告警时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </body>
            </html>"""
            msg.attach(MIMEText(body, 'html', 'utf-8'))

            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            print(f"✅ 告警邮件已发送到: {self.alert_email}")
            return True

        except Exception as e:
            print(f"❌ 发送告警失败: {e}")
            return False

    def send_data_failure_alert(self, failed_sources: list, symbol: str):
        """
        发送数据获取失败告警
        :param failed_sources: 失败的数据源列表
        :param symbol: 股票代码
        """
        title = f"⚠️ 股票数据获取失败"
        content = f"""股票代码: {symbol}
失败的数据源: {', '.join(failed_sources)}
告警时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

建议:
1. 检查数据源网络连接
2. 验证数据源权限配置
3. 确认股票代码是否正确
"""
        self.send_alert(title, content)

    def send_system_error_alert(self, error_msg: str, traceback_info: str = ''):
        """
        发送系统错误告警
        :param error_msg: 错误信息
        :param traceback_info: 异常栈信息
        """
        title = f"💥 系统异常告警"
        content = f"""错误信息: {error_msg}
异常栈:\n{traceback_info}
告警时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

建议:
1. 查看系统日志排查问题
2. 检查相关服务状态
3. 必要时重启系统
"""
        self.send_alert(title, content)

# 全局告警发送器
alert_sender = AlertSender()

# 测试代码
if __name__ == "__main__":
    import pandas as pd

    # 创建测试配置
    test_config = {
        'automation': {
            'alert': {
                'enabled': True,
                'smtp_server': 'smtp.example.com',
                'smtp_port': 587,
                'smtp_username': 'test@example.com',
                'smtp_password': 'password',
                'email': 'admin@example.com'
            }
        }
    }

    # 创建告警发送器
    sender = AlertSender(test_config)

    # 测试发送告警
    sender.send_alert("测试告警", "这是一条测试告警信息")

    # 测试数据失败告警
    sender.send_data_failure_alert(['akshare', 'tushare'], '000001')