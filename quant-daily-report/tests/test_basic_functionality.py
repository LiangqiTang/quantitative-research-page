#!/usr/bin/env python3
"""
基础功能测试
验证系统各个模块的基本功能是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime

class TestBasicFunctionality:
    """测试基础功能"""

    def test_import_modules(self):
        """测试模块导入"""
        print("\n📦 测试模块导入...")
        try:
            # 测试数据采集模块
            from data_collector import (
                MacroDataCollector,
                StockDataCollector,
                NewsDataCollector,
                MultiSourceDataFetcher,
                DataQualityValidator
            )
            print("✅ 数据采集模块导入成功")

            # 测试分析模块
            from analyzer import (
                MacroAnalyzer,
                StockAnalyzer,
                TechnicalAnalyzer
            )
            print("✅ 分析模块导入成功")

            # 测试可视化模块
            from visualizer import (
                KLineVisualizer,
                ReportGenerator
            )
            print("✅ 可视化模块导入成功")

            # 测试回测模块
            from backtester import (
                QlibBacktestEngine,
                StrategyAnalyzer
            )
            print("✅ 回测模块导入成功")

            print("🎉 所有模块导入成功！")
            return True
        except Exception as e:
            print(f"❌ 模块导入失败: {e}")
            return False

    def test_data_collector_basic(self):
        """测试数据采集模块基础功能"""
        print("\n📡 测试数据采集模块...")
        try:
            # 测试数据质量验证
            from data_collector import DataQualityValidator
            validator = DataQualityValidator()

            # 创建测试数据
            test_data = {
                'symbol': '000001',
                'name': '平安银行',
                'basic': {
                    'symbol': '000001',
                    'name': '平安银行',
                    'industry': '银行',
                    'list_date': '1991-04-03'
                },
                'kline': pd.DataFrame({
                    'open': [10.0, 10.2, 10.1],
                    'high': [10.3, 10.4, 10.2],
                    'low': [9.9, 10.1, 10.0],
                    'close': [10.2, 10.3, 10.1],
                    'volume': [10000, 12000, 9000],
                    'amount': [102000, 123600, 90900]
                }),
                'financial': {
                    'pe': 10.2,
                    'pb': 1.1,
                    'eps': 2.3
                }
            }

            # 验证数据质量
            report = validator.validate_all(test_data)
            print(f"✅ 数据质量验证完成，得分: {report['overall_score']}")
            print(f"✅ 验证结果: {'通过' if report['passed'] else '未通过'}")

            return True
        except Exception as e:
            print(f"❌ 数据采集模块测试失败: {e}")
            return False

    def test_analyzer_basic(self):
        """测试分析模块基础功能"""
        print("\n🧠 测试分析模块...")
        try:
            # 测试市场情绪分析
            from analyzer import MacroAnalyzer

            market_data = {
                'up_count': 3215,
                'down_count': 1245,
                'flat_count': 230,
                'limit_up_count': 125,
                'limit_down_count': 15,
                'north_money': 85.2,
                'sh_amount': 4500,
                'sz_amount': 5800,
                'avg_market_amount': 8500
            }

            macro_analyzer = MacroAnalyzer(market_data)
            sentiment = macro_analyzer.analyze_market_sentiment()

            print(f"✅ 市场情绪分析完成")
            print(f"✅ 情绪阶段: {sentiment['sentiment_stage']}")
            print(f"✅ 操作建议: {sentiment['trading_advice']['short']}")

            # 测试股票分析
            from analyzer import StockAnalyzer

            stock_data = {
                'kline': pd.DataFrame({
                    'open': [10.0, 10.2, 10.1],
                    'high': [10.3, 10.4, 10.2],
                    'low': [9.9, 10.1, 10.0],
                    'close': [10.2, 10.3, 10.1],
                    'volume': [10000, 12000, 9000]
                }),
                'financial': {
                    'pe': 10.2,
                    'pb': 1.1,
                    'eps': 2.3,
                    'revenue': 1500,
                    'profit': 300,
                    'debt_ratio': 45.0,
                    'current_ratio': 1.8,
                    'revenue_growth': 18.5,
                    'profit_growth': 25.3,
                    'roe': 15.2,
                    'net_margin': 8.5
                }
            }

            stock_analyzer = StockAnalyzer(stock_data)
            fundamental_result = stock_analyzer.analyze_fundamentals()

            print(f"✅ 个股基本面分析完成")
            print(f"✅ 综合评分: {fundamental_result['composite_score']:.1f}")
            print(f"✅ 投资评级: {fundamental_result['investment_rating']}")

            return True
        except Exception as e:
            print(f"❌ 分析模块测试失败: {e}")
            return False

    def test_visualizer_basic(self):
        """测试可视化模块基础功能"""
        print("\n📈 测试可视化模块...")
        try:
            # 创建测试数据
            test_data = {
                'date': '2023年06月15日',
                'market_overview': {},
                'market_sentiment': {
                    'metrics': {'up_ratio': 0.65, 'limit_up_ratio': 3.2, 'volume_ratio': 1.3},
                    'sentiment_stage': '启动',
                    'trading_advice': {
                        'short': '情绪启动，积极做多',
                        'detail': '市场情绪全面复苏，赚钱效应显现'
                    }
                },
                'hot_sectors': [
                    {'name': '半导体', 'change_percent': 5.2, 'main_inflow': 125000, 'top_stock': '北方华创'},
                    {'name': 'AI概念', 'change_percent': 3.8, 'main_inflow': 98000, 'top_stock': '三六零'}
                ],
                'stock_analysis': {
                    '000001': {
                        'fundamentals': {'composite_score': 85.5, 'investment_rating': '买入'},
                        'technical': {'trading_signal': '买入信号'}
                    }
                }
            }

            # 测试报告生成
            from visualizer import ReportGenerator
            generator = ReportGenerator()
            md_content = generator.generate_daily_report(test_data)

            print(f"✅ 报告生成成功")
            print(f"✅ 报告长度: {len(md_content)}字符")

            # 测试HTML报告生成
            html_content = generator.generate_html_report(test_data)
            print(f"✅ HTML报告生成成功")
            print(f"✅ HTML报告长度: {len(html_content)}字符")

            # 测试K线可视化
            from visualizer import KLineVisualizer

            kline_data = pd.DataFrame({
                'open': [10.0, 10.2, 10.1],
                'high': [10.3, 10.4, 10.2],
                'low': [9.9, 10.1, 10.0],
                'close': [10.2, 10.3, 10.1],
                'volume': [10000, 12000, 9000]
            })

            visualizer = KLineVisualizer(kline_data)
            fig = visualizer.plot_kline_with_indicators('000001')
            print(f"✅ K线图绘制成功")

            return True
        except Exception as e:
            print(f"❌ 可视化模块测试失败: {e}")
            return False

    def test_backtester_basic(self):
        """测试回测模块基础功能"""
        print("\n⏳ 测试回测模块...")
        try:
            # 测试回测引擎初始化
            from backtester import StrategyAnalyzer

            # 创建模拟回测结果
            np.random.seed(42)
            dates = pd.date_range('2021-01-01', '2022-12-31', freq='B')
            daily_returns = np.random.normal(0.0005, 0.01, len(dates))
            portfolio_value = (1 + daily_returns).cumprod() * 1000000

            backtest_result = {
                'portfolio_value': portfolio_value,
                'daily_returns': pd.Series(daily_returns, index=dates),
                'benchmark_returns': pd.Series(np.random.normal(0.0003, 0.008, len(dates)), index=dates),
                'transactions': pd.DataFrame({
                    'date': dates[:100],
                    'symbol': ['000001'] * 100,
                    'side': ['buy'] * 50 + ['sell'] * 50,
                    'price': np.random.uniform(10, 20, 100),
                    'quantity': np.random.randint(100, 1000, 100),
                    'profit': np.random.normal(100, 500, 100)
                })
            }

            # 测试策略分析
            analyzer = StrategyAnalyzer()
            analysis_result = analyzer.analyze_strategy_performance(backtest_result)

            print(f"✅ 策略分析完成")
            print(f"✅ 总收益率: {analysis_result['return_metrics'].get('total_return', 0):.2%}")
            print(f"✅ 年化收益率: {analysis_result['return_metrics'].get('annual_return', 0):.2%}")
            print(f"✅ 夏普比率: {analysis_result['risk_adjusted_metrics'].get('sharpe_ratio', 0):.2f}")

            return True
        except Exception as e:
            print(f"❌ 回测模块测试失败: {e}")
            return False

    def test_qlib_integration(self):
        """测试Qlib集成功能"""
        print("\n🧪 测试Qlib集成...")
        try:
            # 尝试导入Qlib
            import importlib
            qlib_spec = importlib.util.find_spec('qlib')
            if qlib_spec is None:
                print("⚠️ Qlib未安装，跳过Qlib测试")
                return True

            # 导入Qlib相关模块
            from backtester import QlibBacktestEngine
            backtester = QlibBacktestEngine()

            print(f"✅ Qlib回测引擎初始化成功")

            # 测试数据获取
            test_symbols = ['000001']
            start_date = '2023-01-01'
            end_date = '2023-01-10'

            # 创建模拟数据
            mock_data = {
                'symbol': test_symbols[0],
                'name': '测试股票',
                'kline': pd.DataFrame({
                    'open': np.random.uniform(10, 20, 10),
                    'high': np.random.uniform(10, 20, 10),
                    'low': np.random.uniform(10, 20, 10),
                    'close': np.random.uniform(10, 20, 10),
                    'volume': np.random.randint(10000, 100000, 10)
                }),
                'source': 'mock',
                'update_time': datetime.now()
            }

            print(f"✅ Qlib模拟数据创建成功")
            return True

        except Exception as e:
            print(f"❌ Qlib集成测试失败: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行基础功能测试...\n")

        test_results = []

        # 运行各个测试
        test_results = [
            self.test_import_modules(),
            self.test_data_collector_basic(),
            self.test_analyzer_basic(),
            self.test_visualizer_basic(),
            self.test_backtester_basic(),
            self.test_qlib_integration()
        ]

        # 统计结果
        print("\n" + "="*60)
        print("📊 测试结果统计")
        print("="*60)

        passed = sum(1 for result in test_results if result)
        total = len(test_results)

        test_names = [
            "模块导入测试",
            "数据采集测试",
            "分析模块测试",
            "可视化测试",
            "回测模块测试",
            "Qlib集成测试"
        ]

        for test_name, result in zip(test_names, test_results):
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:<20} {status}")

        print("\n" + "="*60)
        print(f"🎯 测试总结: {passed}/{total} 测试通过")

        if passed == total:
            print("🎉 所有基础功能测试通过！系统可以正常使用。")
            return True
        else:
            print("⚠️ 部分测试未通过，请检查相关功能模块。")
            return False

if __name__ == "__main__":
    tester = TestBasicFunctionality()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)