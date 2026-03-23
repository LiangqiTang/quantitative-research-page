#!/usr/bin/env python3
"""
定时任务调度器
配置和管理系统定时任务
"""

import schedule
import time
import subprocess
import os
import sys
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.logger = self._setup_logging()
        self.job_id_map = {}

    def _setup_logging(self):
        """设置日志系统"""
        logger = logging.getLogger('task_scheduler')
        logger.setLevel(logging.INFO)

        # 创建日志目录
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # 创建文件处理器
        handler = RotatingFileHandler(
            'logs/scheduler.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # 添加处理器
        logger.addHandler(handler)
        logger.addHandler(console_handler)

        return logger

    def run_daily_report(self):
        """运行每日报告生成任务"""
        self.logger.info("🚀 开始执行每日报告生成任务")
        try:
            # 添加项目目录到Python路径
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_dir not in sys.path:
                sys.path.insert(0, project_dir)

            # 运行主程序
            import main
            main.main()

            self.logger.info("✅ 每日报告生成任务执行成功")
        except Exception as e:
            self.logger.error(f"❌ 每日报告生成任务执行失败: {e}", exc_info=True)

    def run_data_update(self):
        """运行数据更新任务"""
        self.logger.info("🔄 开始执行数据更新任务")
        try:
            # 添加项目目录到Python路径
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_dir not in sys.path:
                sys.path.insert(0, project_dir)

            # 运行数据更新脚本
            from scripts.download_data import DataDownloader
            downloader = DataDownloader()
            downloader.update_all_data()

            self.logger.info("✅ 数据更新任务执行成功")
        except Exception as e:
            self.logger.error(f"❌ 数据更新任务执行失败: {e}", exc_info=True)

    def run_strategy_backtest(self):
        """运行策略回测任务"""
        self.logger.info("⏳ 开始执行策略回测任务")
        try:
            # 添加项目目录到Python路径
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_dir not in sys.path:
                sys.path.insert(0, project_dir)

            # 运行回测脚本
            from backtester.qlib_backtester import QlibBacktestEngine
            backtester = QlibBacktestEngine()
            backtester.run_daily_backtest()

            self.logger.info("✅ 策略回测任务执行成功")
        except Exception as e:
            self.logger.error(f"❌ 策略回测任务执行失败: {e}", exc_info=True)

    def setup_daily_schedule(self, time_str='08:30'):
        """设置每日定时任务"""
        self.logger.info(f"📅 设置每日定时任务，执行时间: {time_str}")

        # 清除现有任务
        schedule.clear()

        # 设置每日报告任务
        schedule.every().day.at(time_str).do(self.run_daily_report).tag('daily_report')

        # 设置每日数据更新任务（早半小时）
        update_time = self._calculate_time(time_str, -30)
        schedule.every().day.at(update_time).do(self.run_data_update).tag('data_update')

        # 设置每周策略回测任务（每周日晚）
        schedule.every().sunday.at('22:00').do(self.run_strategy_backtest).tag('weekly_backtest')

        self.logger.info("✅ 定时任务设置完成")

    def setup_hourly_schedule(self):
        """设置每小时任务"""
        self.logger.info("⏰ 设置每小时定时任务")

        # 清除现有任务
        schedule.clear()

        # 设置每小时数据更新任务
        schedule.every().hour.do(self.run_data_update).tag('hourly_data_update')

        self.logger.info("✅ 每小时定时任务设置完成")

    def setup_test_schedule(self):
        """设置测试用的定时任务（每分钟执行）"""
        self.logger.info("🧪 设置测试用定时任务（每分钟执行）")

        # 清除现有任务
        schedule.clear()

        # 设置每分钟测试任务
        schedule.every(1).minutes.do(self.run_daily_report).tag('test_task')

        self.logger.info("✅ 测试定时任务设置完成")

    def _calculate_time(self, time_str, minutes_offset):
        """计算偏移后的时间"""
        try:
            hour, minute = map(int, time_str.split(':'))
            dt = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            dt += timedelta(minutes=minutes_offset)
            return dt.strftime('%H:%M')
        except ValueError:
            self.logger.error(f"❌ 无效的时间格式: {time_str}")
            return time_str

    def list_jobs(self):
        """列出所有定时任务"""
        jobs = schedule.get_jobs()
        if not jobs:
            print("📋 没有定时任务")
            return

        print("📋 定时任务列表:")
        for job in jobs:
            job_info = {
                'id': job.job_id,
                'tags': job.tags,
                'next_run': job.next_run,
                'interval': job.interval,
                'unit': job.unit
            }
            print(f"\n🔹 任务ID: {job.job_id}")
            print(f"   标签: {', '.join(job.tags)}")
            print(f"   下次运行时间: {job.next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   执行间隔: {job.interval} {job.unit}")

    def start_scheduler(self):
        """启动调度器"""
        self.logger.info("🚀 启动任务调度器")
        print("🚀 任务调度器已启动，按 Ctrl+C 停止")

        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次

    def stop_scheduler(self):
        """停止调度器"""
        self.logger.info("🛑 停止任务调度器")
        schedule.clear()

    def run_job_now(self, job_tag):
        """立即运行指定标签的任务"""
        self.logger.info(f"⏱️ 立即运行标签为 '{job_tag}' 的任务")
        jobs = schedule.get_jobs(job_tag)

        if not jobs:
            self.logger.warning(f"⚠️ 没有找到标签为 '{job_tag}' 的任务")
            return

        for job in jobs:
            try:
                job.run()
                self.logger.info(f"✅ 任务 {job.job_id} 执行成功")
            except Exception as e:
                self.logger.error(f"❌ 任务 {job.job_id} 执行失败: {e}")


def main():
    """主函数"""
    scheduler = TaskScheduler()

    if len(sys.argv) < 2:
        print("📖 使用方法:")
        print("  python scheduler.py daily [HH:MM]   # 设置每日定时任务")
        print("  python scheduler.py hourly          # 设置每小时定时任务")
        print("  python scheduler.py test            # 设置测试用定时任务")
        print("  python scheduler.py start           # 启动调度器")
        print("  python scheduler.py list            # 列出所有任务")
        print("  python scheduler.py run <tag>       # 立即运行指定标签的任务")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == 'daily':
            time_str = sys.argv[2] if len(sys.argv) > 2 else '08:30'
            scheduler.setup_daily_schedule(time_str)
            scheduler.list_jobs()
        elif command == 'hourly':
            scheduler.setup_hourly_schedule()
            scheduler.list_jobs()
        elif command == 'test':
            scheduler.setup_test_schedule()
            scheduler.list_jobs()
        elif command == 'start':
            scheduler.start_scheduler()
        elif command == 'list':
            scheduler.list_jobs()
        elif command == 'run':
            if len(sys.argv) < 3:
                print("⚠️ 请指定任务标签")
                sys.exit(1)
            job_tag = sys.argv[2]
            scheduler.run_job_now(job_tag)
        else:
            print(f"❌ 未知命令: {command}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 退出程序")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        scheduler.logger.error(f"❌ 执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()