#!/usr/bin/env python3
"""
📈 A股量化日报系统 - 主程序

这是一个全自动的A股量化分析与报告生成系统，支持数据采集、量化分析、
可视化报告生成、自动化部署等功能。
"""

import os
import sys
import logging
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
        stock_collector = StockDataCollector()

        for stock in stock_pool:
            symbol = stock['symbol']
            market = stock['market']
            try:
                kline = stock_collector.get_stock_kline(symbol, market)
                financial = stock_collector.get_stock_financial(symbol)
                stock_data[symbol] = {
                    'kline': kline,
                    'financial': financial
                }
                logger.info(f"✅ {symbol} 数据采集完成")
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

        # 4. 可视化报告生成
        logger.info("\n📈 开始生成可视化报告...")

        # 创建输出目录
        output_dir = project_root / 'output'
        output_dir.mkdir(exist_ok=True)

        # 生成K线图
        plotter = KLineVisualizer(None)
        for symbol, data in stock_data.items():
            try:
                plotter.data = data['kline']
                plot_path = output_dir / f'{symbol}_kline.png'
                plotter.plot_kline_with_indicators(symbol)
                plotter.save_plot(str(plot_path))
                logger.info(f"✅ {symbol} K线图已保存: {plot_path}")
            except Exception as e:
                logger.error(f"❌ {symbol} K线图生成失败: {e}")
                continue

        # 生成日报
        report_generator = ReportGenerator()
        report_data = {
            'date': datetime.now().strftime('%Y年%m月%d日'),
            'market_overview': market_overview,
            'market_sentiment': market_sentiment,
            'hot_sectors': hot_sectors,
            'stock_analysis': stock_analysis_results,
            'latest_news': latest_news
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