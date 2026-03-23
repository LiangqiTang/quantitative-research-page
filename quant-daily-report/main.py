#!/usr/bin/env python3
"""
📈 A股量化日报系统 - 主程序

这是一个全自动的A股量化分析与报告生成系统，支持数据采集、量化分析、
可视化报告生成、自动化部署等功能。
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quant_daily.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """主程序入口"""
    try:
        logger.info("=" * 60)
        logger.info(f"📊 A股量化日报系统启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        # 1. 导入核心模块
        logger.info("📦 导入核心模块...")
        from data_collector import (
            MacroDataCollector,
            StockDataCollector,
            NewsDataCollector
        )
        from analyzer import (
            MacroAnalyzer,
            StockAnalyzer,
            TechnicalAnalyzer
        )
        from visualizer import (
            KLineVisualizer,
            ReportGenerator
        )
        from scripts.github_uploader import GitHubUploader

        # 加载配置文件
        config = None
        config_path = project_root / 'config.yaml'
        try:
            import yaml
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                logger.info("✅ 配置文件加载成功")
            else:
                logger.warning("⚠️ 配置文件不存在，将使用默认配置")
        except Exception as e:
            logger.warning(f"⚠️ 配置文件加载失败: {e}")

        # 尝试导入回测模块
        backtest_engine = None
        backtest_enabled = False
        try:
            from backtester import QlibBacktestEngine

            # 检查配置
            if config:
                backtest_enabled = config.get('backtest', {}).get('enabled', False)

            if backtest_enabled:
                backtest_engine = QlibBacktestEngine()
                logger.info("✅ 回测模块加载成功")
        except ImportError as e:
            logger.warning(f"⚠️ 回测模块依赖缺失，回测功能已禁用: {e}")
        except Exception as e:
            logger.warning(f"⚠️ 回测模块初始化失败: {e}")

        # 尝试导入因子挖掘模块
        factor_miner = None
        factor_mining_enabled = False
        try:
            from factor_mining import FactorMiningEngine

            # 检查配置
            if config:
                factor_mining_enabled = config.get('factor_mining', {}).get('enabled', True)

            if factor_mining_enabled:
                factor_miner = FactorMiningEngine()
                logger.info("✅ 因子挖掘模块加载成功")
        except ImportError as e:
            logger.warning(f"⚠️ 因子挖掘模块依赖缺失，因子挖掘功能已禁用: {e}")
        except Exception as e:
            logger.warning(f"⚠️ 因子挖掘模块初始化失败: {e}")

        # 2. 数据采集
        logger.info("\n📡 开始数据采集...")

        # 宏观数据采集
        macro_collector = MacroDataCollector()
        market_overview = macro_collector.get_market_overview()
        hot_sectors = macro_collector.get_hot_sectors()
        logger.info(f"✅ 宏观数据采集完成: {len(market_overview)}个指标")

        # 股票数据采集 - 示例股票池
        stock_pool = [
            {'symbol': '000001', 'market': 'sz'},
            {'symbol': '600036', 'market': 'sh'},
            {'symbol': '600519', 'market': 'sh'},
            {'symbol': '002415', 'market': 'sz'},
            {'symbol': '300750', 'market': 'sz'}
        ]
        stock_data = {}

        # 使用多源数据获取器
        from data_collector import MultiSourceFetcher
        data_fetcher = MultiSourceFetcher(config=config)

        for stock in stock_pool:
            symbol = stock['symbol']
            try:
                # 使用多源获取器获取数据
                stock_info = data_fetcher.fetch_stock_data(symbol)

                # 提取需要的数据
                stock_data[symbol] = {
                    'kline': stock_info.get('kline', pd.DataFrame()),
                    'financial': stock_info.get('financial', {}),
                    'basic': stock_info.get('basic', {})
                }
                logger.info(f"✅ {symbol} 数据采集完成 (数据源: {stock_info.get('source', 'unknown')})")
            except Exception as e:
                logger.error(f"❌ {symbol} 数据采集失败: {e}")
                continue

        # 新闻数据采集
        news_collector = NewsDataCollector()
        latest_news = news_collector.get_latest_news()
        logger.info(f"✅ 新闻数据采集完成: {len(latest_news)}条新闻")

        # 3. 量化分析
        logger.info("\n🧠 开始量化分析...")

        # 宏观分析
        macro_analyzer = MacroAnalyzer(market_overview)
        market_sentiment = macro_analyzer.analyze_market_sentiment()
        sector_rotation = macro_analyzer.analyze_sector_rotation()
        logger.info(f"✅ 宏观分析完成: 市场情绪 -> {market_sentiment['sentiment_stage']}")

        # 个股分析
        stock_analysis_results = {}
        for symbol, data in stock_data.items():
            try:
                stock_analyzer = StockAnalyzer(data)
                fundamentals = stock_analyzer.analyze_fundamentals()
                technical = stock_analyzer.analyze_technical()

                stock_analysis_results[symbol] = {
                    'fundamentals': fundamentals,
                    'technical': technical,
                    'financial': data['financial'],
                    'kline_path': f'{symbol}_kline.png'  # 添加K线图路径
                }
                logger.info(f"✅ {symbol} 分析完成")
            except Exception as e:
                logger.error(f"❌ {symbol} 分析失败: {e}")
                continue

        # 创建输出目录
        output_dir = project_root / 'output'
        output_dir.mkdir(exist_ok=True)

        # 4. 量化回测
        backtest_result = None
        if backtest_enabled and backtest_engine and stock_data:
            logger.info("\n🔬 开始量化回测...")
            try:
                # 准备回测数据
                from datetime import timedelta

                # 使用最近1年的数据进行回测
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')

                # 提取股票代码列表
                symbols = [s['symbol'] for s in stock_pool if s['symbol'] in stock_data]

                if symbols:
                    # 获取回测数据
                    logger.info(f"📊 准备{len(symbols)}只股票的回测数据...")
                    backtest_data = backtest_engine.fetch_data(
                        symbols=symbols,
                        start_date=start_date,
                        end_date=end_date
                    )

                    # 运行回测
                    logger.info("⏳ 运行量化回测...")
                    backtest_result = backtest_engine.run_backtest(backtest_data)

                    # 生成回测报告
                    logger.info("📝 生成回测报告...")
                    backtest_report = backtest_engine.generate_report(backtest_result)

                    # 保存回测报告
                    backtest_report_path = output_dir / 'backtest_report.txt'
                    with open(backtest_report_path, 'w', encoding='utf-8') as f:
                        f.write(backtest_report)
                    logger.info(f"✅ 回测报告已保存: {backtest_report_path}")

                    logger.info("✅ 量化回测完成")
                else:
                    logger.warning("⚠️ 没有可用的股票数据，跳过回测")
            except Exception as e:
                logger.error(f"❌ 量化回测失败: {e}", exc_info=True)

        # 5. 因子挖掘
        factor_result = None
        if factor_mining_enabled and factor_miner and stock_data:
            logger.info("\n🧬 开始因子挖掘...")
            try:
                # 准备因子挖掘数据
                from datetime import timedelta

                # 使用最近2年的数据进行因子挖掘
                start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')

                # 提取股票代码列表
                symbols = [s['symbol'] for s in stock_pool if s['symbol'] in stock_data]

                if symbols:
                    # 准备因子挖掘数据
                    logger.info(f"📊 准备{len(symbols)}只股票的因子挖掘数据...")

                    # 创建模拟数据结构（实际应用中应该使用真实数据）
                    factor_data = {
                        'price_data': None,
                        'financial_data': None,
                        'technical_data': None,
                        'start_date': start_date,
                        'end_date': end_date,
                        'symbols': symbols
                    }

                    # 运行因子挖掘
                    logger.info("🔍 运行因子挖掘...")
                    factors = factor_miner.mine_factors(
                        factor_data,
                        factor_types=['price', 'volume', 'momentum', 'volatility', 'trend'],
                        max_factors=20
                    )

                    if factors:
                        # 验证因子
                        logger.info("📊 验证因子有效性...")
                        validated_factors = factor_miner.validate_factors(factor_data, factors)

                        # 回测因子
                        logger.info("⏳ 回测因子表现...")
                        factor_backtest_result = factor_miner.backtest_factors(factor_data, validated_factors)

                        # 生成因子报告
                        logger.info("📝 生成因子挖掘报告...")
                        factor_report_path = factor_miner.generate_report()

                        if factor_report_path:
                            logger.info(f"✅ 因子挖掘报告已保存: {factor_report_path}")

                        # 保存因子结果
                        factor_result = {
                            'factors': factors,
                            'validated_factors': validated_factors,
                            'backtest_result': factor_backtest_result,
                            'total_factors': len(factors),
                            'validated_count': len(validated_factors)
                        }

                        logger.info(f"✅ 因子挖掘完成，共挖掘{len(factors)}个因子，其中{len(validated_factors)}个有效因子")
                    else:
                        logger.warning("⚠️ 没有挖掘出任何因子")
                else:
                    logger.warning("⚠️ 没有可用的股票数据，跳过因子挖掘")
            except Exception as e:
                logger.error(f"❌ 因子挖掘失败: {e}", exc_info=True)

        # 6. 可视化报告生成
        logger.info("\n📈 开始生成可视化报告...")

        # 生成日报
        report_generator = ReportGenerator()
        report_data = {
            'date': datetime.now().strftime('%Y年%m月%d日'),
            'market_overview': market_overview,
            'market_sentiment': market_sentiment,
            'hot_sectors': hot_sectors,
            'stock_analysis': stock_analysis_results,
            'latest_news': latest_news,
            'backtest_result': backtest_result,
            'factor_result': factor_result
        }

        # 生成Markdown报告
        md_report_content = report_generator.generate_daily_report(report_data)
        md_report_path = output_dir / 'daily_report.md'
        report_generator.save_report(md_report_content, str(md_report_path))
        logger.info(f"✅ Markdown报告已保存: {md_report_path}")

        # 生成HTML报告
        html_report_content = report_generator.generate_html_report(report_data)
        html_report_path = output_dir / 'index.html'
        report_generator.save_report(html_report_content, str(html_report_path))
        logger.info(f"✅ HTML报告已保存: {html_report_path}")

        # 5. 自动化部署（可选）
        logger.info("\n☁️ 开始自动化部署...")

        try:
            # 从环境变量读取配置
            github_token = os.getenv('GITHUB_TOKEN')
            github_repo = os.getenv('GITHUB_REPO')

            if github_token and github_repo:
                uploader = GitHubUploader(github_token, github_repo)
                uploader.upload_report(str(html_report_path))
                logger.info("✅ 报告已成功上传到GitHub Pages")
            else:
                logger.warning("⚠️ GitHub配置未设置，跳过自动部署")
        except Exception as e:
            logger.error(f"❌ 报告上传失败: {e}")

        logger.info("\n" + "=" * 60)
        logger.info("🎉 全部任务完成！")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.info("\n⏹️ 用户中断程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ 程序运行出错: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()