#!/usr/bin/env python3
"""
数据下载脚本
下载和更新A股市场数据
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
import pandas as pd

# 添加项目目录到Python路径
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from data_collector.multi_source_fetcher import MultiSourceDataFetcher
from data_collector.data_validator import DataQualityValidator


class DataDownloader:
    """数据下载器"""

    def __init__(self):
        self.logger = self._setup_logging()
        self.fetcher = MultiSourceDataFetcher()
        self.validator = DataQualityValidator()

        # 创建数据目录
        self.data_dir = 'data'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        self.daily_data_dir = os.path.join(self.data_dir, 'daily')
        if not os.path.exists(self.daily_data_dir):
            os.makedirs(self.daily_data_dir)

        self.history_data_dir = os.path.join(self.data_dir, 'history')
        if not os.path.exists(self.history_data_dir):
            os.makedirs(self.history_data_dir)

    def _setup_logging(self):
        """设置日志系统"""
        logger = logging.getLogger('data_downloader')
        logger.setLevel(logging.INFO)

        # 创建日志目录
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # 创建文件处理器
        handler = logging.FileHandler(
            'logs/download_data.log',
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

    def update_daily_data(self, date=None):
        """更新每日数据"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        self.logger.info(f"📅 开始更新 {date} 的每日数据")

        try:
            # 获取市场概览数据
            self.logger.info("🔍 下载市场概览数据...")
            market_overview = self.fetcher.fetch_market_overview(date)
            self._save_data(market_overview, 'market_overview', date)

            # 获取指数数据
            self.logger.info("📈 下载指数数据...")
            index_data = self.fetcher.fetch_index_data(date)
            self._save_data(index_data, 'index_data', date)

            # 获取板块数据
            self.logger.info("📊 下载板块数据...")
            sector_data = self.fetcher.fetch_sector_data(date)
            self._save_data(sector_data, 'sector_data', date)

            # 获取热门股票数据
            self.logger.info("🔥 下载热门股票数据...")
            hot_stocks = self.fetcher.fetch_hot_stocks(date)
            self._save_data(hot_stocks, 'hot_stocks', date)

            self.logger.info(f"✅ {date} 的每日数据更新完成")
            return True

        except Exception as e:
            self.logger.error(f"❌ 更新每日数据失败: {e}", exc_info=True)
            return False

    def download_history_data(self, start_date, end_date):
        """下载历史数据"""
        self.logger.info(f"⏳ 开始下载历史数据 ({start_date} 至 {end_date})")

        try:
            # 转换日期格式
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')

            current_date = start_dt
            total_days = (end_dt - start_dt).days + 1
            success_count = 0

            while current_date <= end_dt:
                date_str = current_date.strftime('%Y-%m-%d')

                # 跳过周末
                if current_date.weekday() >= 5:
                    self.logger.info(f"📅 跳过周末: {date_str}")
                    current_date += timedelta(days=1)
                    continue

                self.logger.info(f"🔍 下载 {date_str} 的数据 ({success_count+1}/{total_days})")

                try:
                    # 下载当日数据
                    market_overview = self.fetcher.fetch_market_overview(date_str)
                    index_data = self.fetcher.fetch_index_data(date_str)
                    sector_data = self.fetcher.fetch_sector_data(date_str)

                    # 保存数据
                    self._save_data(market_overview, 'market_overview', date_str, history=True)
                    self._save_data(index_data, 'index_data', date_str, history=True)
                    self._save_data(sector_data, 'sector_data', date_str, history=True)

                    success_count += 1
                    self.logger.info(f"✅ {date_str} 的数据下载完成")

                except Exception as e:
                    self.logger.error(f"❌ 下载 {date_str} 的数据失败: {e}")

                # 延迟避免请求过于频繁
                time.sleep(1)
                current_date += timedelta(days=1)

            self.logger.info(f"🎉 历史数据下载完成，成功下载 {success_count}/{total_days} 天的数据")
            return success_count == total_days

        except Exception as e:
            self.logger.error(f"❌ 下载历史数据失败: {e}", exc_info=True)
            return False

    def download_stock_history(self, symbol, start_date, end_date):
        """下载个股历史数据"""
        self.logger.info(f"📈 下载个股 {symbol} 的历史数据 ({start_date} 至 {end_date})")

        try:
            stock_data = self.fetcher.fetch_stock_history(symbol, start_date, end_date)

            if stock_data and 'kline' in stock_data:
                # 保存K线数据
                kline_df = stock_data['kline']
                filename = os.path.join(self.history_data_dir, f'stock_{symbol}_kline.csv')
                kline_df.to_csv(filename, index=False, encoding='utf-8-sig')
                self.logger.info(f"✅ 个股 {symbol} 的K线数据已保存到 {filename}")

                # 保存基本面数据
                if 'financial' in stock_data:
                    financial_data = stock_data['financial']
                    financial_df = pd.DataFrame([financial_data])
                    filename = os.path.join(self.history_data_dir, f'stock_{symbol}_financial.csv')
                    financial_df.to_csv(filename, index=False, encoding='utf-8-sig')
                    self.logger.info(f"✅ 个股 {symbol} 的基本面数据已保存到 {filename}")

                return True

            else:
                self.logger.error(f"❌ 未能获取个股 {symbol} 的数据")
                return False

        except Exception as e:
            self.logger.error(f"❌ 下载个股 {symbol} 的历史数据失败: {e}", exc_info=True)
            return False

    def update_all_data(self):
        """更新所有数据"""
        self.logger.info("🔄 开始更新所有数据")

        try:
            # 更新今日数据
            today = datetime.now().strftime('%Y-%m-%d')
            if not self.update_daily_data(today):
                self.logger.warning(f"⚠️ 更新今日数据失败，但将继续执行其他任务")

            # 检查并更新昨日数据（如果是交易日）
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            yesterday_dt = datetime.strptime(yesterday, '%Y-%m-%d')
            if yesterday_dt.weekday() < 5:  # 不是周末
                yesterday_file = os.path.join(self.daily_data_dir, f'market_overview_{yesterday}.csv')
                if not os.path.exists(yesterday_file):
                    self.logger.info(f"📅 补充下载昨日 ({yesterday}) 的数据")
                    self.update_daily_data(yesterday)

            # 验证最新数据质量
            self._validate_recent_data()

            self.logger.info("🎉 所有数据更新完成")
            return True

        except Exception as e:
            self.logger.error(f"❌ 更新所有数据失败: {e}", exc_info=True)
            return False

    def _save_data(self, data, data_type, date, history=False):
        """保存数据到文件"""
        if not data:
            self.logger.warning(f"⚠️ 没有数据可保存: {data_type}")
            return

        try:
            # 选择保存目录
            if history:
                save_dir = self.history_data_dir
            else:
                save_dir = self.daily_data_dir

            # 创建数据类型子目录
            type_dir = os.path.join(save_dir, data_type)
            if not os.path.exists(type_dir):
                os.makedirs(type_dir)

            # 生成文件名
            filename = os.path.join(type_dir, f'{data_type}_{date}.csv')

            # 保存数据
            if isinstance(data, pd.DataFrame):
                data.to_csv(filename, index=False, encoding='utf-8-sig')
            elif isinstance(data, dict):
                # 如果是嵌套字典，转换为DataFrame
                if any(isinstance(v, dict) for v in data.values()):
                    df = pd.DataFrame.from_dict(data, orient='index')
                    df.to_csv(filename, encoding='utf-8-sig')
                else:
                    df = pd.DataFrame([data])
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
            else:
                self.logger.error(f"❌ 不支持的数据类型: {type(data)}")
                return

            self.logger.debug(f"💾 已保存 {data_type} 数据到 {filename}")

        except Exception as e:
            self.logger.error(f"❌ 保存数据失败: {e}", exc_info=True)

    def _validate_recent_data(self):
        """验证最近的数据质量"""
        self.logger.info("🔍 验证最近的数据质量")

        try:
            # 检查最近3天的数据
            for i in range(3):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                date_dt = datetime.strptime(date, '%Y-%m-%d')

                # 跳过周末
                if date_dt.weekday() >= 5:
                    continue

                # 检查市场概览数据
                file_path = os.path.join(self.daily_data_dir, 'market_overview', f'market_overview_{date}.csv')
                if os.path.exists(file_path):
                    try:
                        df = pd.read_csv(file_path)
                        if not df.empty:
                            # 转换为字典格式
                            data = df.to_dict('records')[0] if len(df) == 1 else df.to_dict()
                            score, issues = self.validator.validate_all(data)

                            if score < 60:
                                self.logger.warning(f"⚠️ {date} 的数据质量较低: {score}分")
                                self.logger.warning(f"   问题: {', '.join(issues)}")
                            else:
                                self.logger.info(f"✅ {date} 的数据质量良好: {score}分")
                    except Exception as e:
                        self.logger.error(f"❌ 验证 {date} 的数据失败: {e}")

        except Exception as e:
            self.logger.error(f"❌ 验证数据质量失败: {e}", exc_info=True)

    def check_data_coverage(self):
        """检查数据覆盖情况"""
        self.logger.info("📊 检查数据覆盖情况")

        try:
            # 检查每日数据目录
            coverage_info = {}
            data_types = ['market_overview', 'index_data', 'sector_data', 'hot_stocks']

            for data_type in data_types:
                type_dir = os.path.join(self.daily_data_dir, data_type)
                if os.path.exists(type_dir):
                    files = os.listdir(type_dir)
                    dates = []

                    for file in files:
                        if file.startswith(f'{data_type}_') and file.endswith('.csv'):
                            date_str = file[len(f'{data_type}_'):-4]
                            try:
                                datetime.strptime(date_str, '%Y-%m-%d')
                                dates.append(date_str)
                            except ValueError:
                                continue

                    if dates:
                        dates.sort()
                        coverage_info[data_type] = {
                            'count': len(dates),
                            'first_date': dates[0],
                            'last_date': dates[-1],
                            'recent_days': len([d for d in dates if self._is_recent(d, 30)])
                        }
                        print(f"\n📈 {data_type}:")
                        print(f"   数据文件数量: {len(dates)}")
                        print(f"   最早日期: {dates[0]}")
                        print(f"   最近日期: {dates[-1]}")
                        print(f"   近30天数据量: {coverage_info[data_type]['recent_days']}")

            # 检查历史数据
            self.logger.info("\n📚 历史数据情况:")
            history_files = os.listdir(self.history_data_dir)
            stock_files = [f for f in history_files if f.startswith('stock_') and f.endswith('.csv')]
            unique_stocks = len(set(f.split('_')[1] for f in stock_files))
            print(f"   包含 {unique_stocks} 只股票的历史数据")
            print(f"   历史数据文件总数: {len(stock_files)}")

            return coverage_info

        except Exception as e:
            self.logger.error(f"❌ 检查数据覆盖情况失败: {e}", exc_info=True)
            return None

    def _is_recent(self, date_str, days):
        """检查日期是否在最近N天内"""
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            recent_date = datetime.now() - timedelta(days=days)
            return date >= recent_date
        except ValueError:
            return False


def main():
    """主函数"""
    downloader = DataDownloader()

    if len(sys.argv) < 2:
        print("📖 使用方法:")
        print("  python download_data.py daily [date]    # 更新每日数据")
        print("  python download_data.py history start end  # 下载历史数据")
        print("  python download_data.py stock symbol start end  # 下载个股历史数据")
        print("  python download_data.py all            # 更新所有数据")
        print("  python download_data.py check          # 检查数据覆盖情况")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == 'daily':
            date = sys.argv[2] if len(sys.argv) > 2 else None
            downloader.update_daily_data(date)
        elif command == 'history':
            if len(sys.argv) < 4:
                print("⚠️ 请提供开始日期和结束日期，格式: YYYY-MM-DD")
                sys.exit(1)
            start_date = sys.argv[2]
            end_date = sys.argv[3]
            downloader.download_history_data(start_date, end_date)
        elif command == 'stock':
            if len(sys.argv) < 5:
                print("⚠️ 请提供股票代码、开始日期和结束日期")
                sys.exit(1)
            symbol = sys.argv[2]
            start_date = sys.argv[3]
            end_date = sys.argv[4]
            downloader.download_stock_history(symbol, start_date, end_date)
        elif command == 'all':
            downloader.update_all_data()
        elif command == 'check':
            downloader.check_data_coverage()
        else:
            print(f"❌ 未知命令: {command}")
            sys.exit(1)

        print("🎉 操作完成")

    except KeyboardInterrupt:
        print("\n👋 用户中断操作")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        logging.error(f"❌ 执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()