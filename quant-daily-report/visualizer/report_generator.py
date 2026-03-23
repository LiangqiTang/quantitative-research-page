"""
报告生成器
负责生成HTML/Markdown格式的量化研报
"""

import markdown
from jinja2 import Template, Environment, FileSystemLoader
import datetime
from typing import Dict, List, Optional
import os
from pathlib import Path

class ReportGenerator:
    def __init__(self, template_dir: str = 'templates'):
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir)) if os.path.exists(template_dir) else None

    def generate_daily_report(self, analysis_results: Dict) -> str:
        """
        生成Markdown格式的日报
        :param analysis_results: 分析结果数据
        :return: Markdown格式的报告内容
        """
        try:
            # 获取数据
            date = analysis_results.get('date', datetime.datetime.now().strftime('%Y年%m月%d日'))
            market_overview = analysis_results.get('market_overview', {})
            market_sentiment = analysis_results.get('market_sentiment', {})
            hot_sectors = analysis_results.get('hot_sectors', [])
            stock_analysis = analysis_results.get('stock_analysis', {})
            latest_news = analysis_results.get('latest_news', [])

            # 构建报告内容
            md_content = f"# 📈 A股量化日报 - {date}\n\n"

            # 市场概况
            md_content += "## 🎮 全局指挥部\n\n"
            md_content += "### 📊 宏观情绪仪表盘\n"
            md_content += "| 指标 | 数值 | 状态 |\n"
            md_content += "|------|------|------|\n"

            # 添加情绪指标
            if market_sentiment.get('metrics'):
                metrics = market_sentiment['metrics']
                md_content += f"| 上涨家数占比 | {metrics.get('up_ratio', 0):.1%} | {self._get_sentiment_emoji(metrics.get('up_ratio', 0), 0.5)} |\n"
                md_content += f"| 市场赚钱效应 | {metrics.get('up_ratio', 0):.1%} | {self._get_profit_emoji(metrics.get('up_ratio', 0))} |\n"
                md_content += f"| 连板高度 | {metrics.get('limit_up_ratio', 0):.1f}板 | {self._get_strength_emoji(metrics.get('limit_up_ratio', 0))} |\n"
                md_content += f"| 成交额异动率 | {metrics.get('volume_ratio', 0):.1%} | {self._get_volume_emoji(metrics.get('volume_ratio', 0))} |\n"

            # 情绪阶段
            if market_sentiment.get('sentiment_stage'):
                md_content += f"\n### 🎯 情绪阶段分析\n"
                md_content += f"- **当前阶段**: {market_sentiment['sentiment_stage']}\n"
                advice = market_sentiment.get('trading_advice', {})
                md_content += f"- **操作建议**: {advice.get('short', '')}\n"
                md_content += f"- **详细策略**: {advice.get('detail', '')}\n"

            # 热点板块
            if hot_sectors:
                md_content += "\n## 🚀 最强赛道轮动\n\n"
                md_content += "| 板块名称 | 涨跌幅 | 主力净流入 | 领涨股 |\n"
                md_content += "|----------|--------|------------|--------|\n"

                for sector in hot_sectors[:10]:
                    md_content += f"| {sector.get('name', '')} | {sector.get('change_percent', 0):.2f}% | {sector.get('main_inflow', 0)/10000:.1f}亿 | {sector.get('top_stock', '')} |\n"

            # 股票分析
            if stock_analysis:
                md_content += "\n## 🐎 个股单兵终端\n\n"

                for symbol, analysis in stock_analysis.items():
                    fundamentals = analysis.get('fundamentals', {})
                    technical = analysis.get('technical', {})

                    md_content += f"### {symbol} - 个股分析\n"
                    md_content += f"#### 📋 基本信息\n"
                    md_content += f"- **综合评分**: {fundamentals.get('composite_score', 0):.1f}分\n"
                    md_content += f"- **投资评级**: {fundamentals.get('investment_rating', '')}\n"
                    md_content += f"- **技术信号**: {technical.get('trading_signal', '')}\n\n"

                    # 估值分析
                    valuation = fundamentals.get('valuation', {})
                    if valuation:
                        md_content += f"#### 📊 估值分析\n"
                        md_content += f"- **市盈率(PE)**: {valuation.get('pe', 0):.1f}\n"
                        md_content += f"- **市净率(PB)**: {valuation.get('pb', 0):.1f}\n"
                        md_content += f"- **估值结论**: {valuation.get('valuation_conclusion', '')}\n\n"

                    # 技术分析
                    if technical:
                        md_content += f"#### 📈 技术分析\n"
                        md_content += f"- **趋势方向**: {technical.get('trend', {}).get('trend_direction', '')}\n"
                        md_content += f"- **技术评分**: {technical.get('technical_score', 0):.1f}\n"
                        support_resistance = technical.get('support_resistance', {})
                        if support_resistance:
                            md_content += f"- **支撑位**: {support_resistance.get('immediate_support', '')}\n"
                            md_content += f"- **压力位**: {support_resistance.get('immediate_resistance', '')}\n"

            # 新闻资讯
            if latest_news:
                md_content += "\n## 📰 今日要闻\n\n"
                for i, news in enumerate(latest_news[:10]):
                    md_content += f"{i+1}. **{news.get('title', '')}**\n"
                    md_content += f"   {news.get('content', '')[:100]}...\n"
                    md_content += f"   *来源: {news.get('source', '')} | 时间: {news.get('time', datetime.datetime.now()).strftime('%H:%M')}*\n\n"

            # 回测结果
            backtest_result = analysis_results.get('backtest_result')
            if backtest_result:
                md_content += "\n## 🧪 量化回测实验室\n\n"
                analysis_result = backtest_result.get('analysis_result', {})

                md_content += "### 📊 回测核心指标\n"
                md_content += "| 指标 | 数值 | 说明 |\n"
                md_content += "|------|------|------|\n"
                md_content += f"| 总收益率 | {analysis_result.get('total_return', 0):.2%} | 回测期间总收益 |\n"
                md_content += f"| 年化收益率 | {analysis_result.get('annual_return', 0):.2%} | 年化收益水平 |\n"
                md_content += f"| 最大回撤 | {analysis_result.get('max_drawdown', 0):.2%} | 最大亏损幅度 |\n"
                md_content += f"| 夏普比率 | {analysis_result.get('sharpe_ratio', 0):.4f} | 风险调整后收益 |\n"
                md_content += f"| 波动率 | {analysis_result.get('volatility', 0):.2%} | 收益波动水平 |\n"
                md_content += f"| 胜率 | {analysis_result.get('win_rate', 0):.2%} | 盈利交易占比 |\n"
                md_content += f"| 盈亏比 | {analysis_result.get('profit_loss_ratio', 0):.2f} | 盈利/亏损幅度 |\n"

                # 策略评估
                md_content += "\n### 🎯 策略评估\n"
                sharpe_ratio = analysis_result.get('sharpe_ratio', 0)
                max_drawdown = analysis_result.get('max_drawdown', 0)
                annual_return = analysis_result.get('annual_return', 0)

                if sharpe_ratio > 1.5:
                    md_content += "✅ 夏普比率优秀，策略风险调整后收益出色\n"
                elif sharpe_ratio > 1.0:
                    md_content += "👍 夏普比率良好，策略风险调整后收益较好\n"
                else:
                    md_content += "⚠️ 夏普比率一般，策略风险调整后收益有待提升\n"

                if max_drawdown > -0.2:
                    md_content += "✅ 最大回撤控制良好，风险较低\n"
                elif max_drawdown > -0.3:
                    md_content += "👍 最大回撤控制一般，风险适中\n"
                else:
                    md_content += "⚠️ 最大回撤较大，风险较高\n"

                if annual_return > 0.2:
                    md_content += "✅ 年化收益率优秀，盈利能力强\n"
                elif annual_return > 0.1:
                    md_content += "👍 年化收益率良好，盈利能力较好\n"
                else:
                    md_content += "⚠️ 年化收益率一般，盈利能力有待提升\n"

                # 投资建议
                md_content += "\n### 💡 回测投资建议\n"
                if sharpe_ratio > 1.5 and max_drawdown > -0.2 and annual_return > 0.2:
                    md_content += "✅ 策略表现优秀，建议考虑实盘应用\n"
                elif sharpe_ratio > 1.0 and max_drawdown > -0.3 and annual_return > 0.1:
                    md_content += "👍 策略表现良好，建议进一步优化后考虑实盘\n"
                else:
                    md_content += "⚠️ 策略表现一般，建议进行参数优化或策略改进\n"

            # 免责声明
            md_content += "\n---\n\n"
            md_content += "**免责声明**: 本报告仅用于学习和研究目的，不构成任何投资建议。股市有风险，投资需谨慎。\n"
            md_content += f"*报告生成时间: {datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}*\n"

            return md_content

        except Exception as e:
            print(f"生成Markdown报告失败: {e}")
            return ""

    def generate_html_report(self, analysis_results: Dict) -> str:
        """
        生成HTML格式的报告
        :param analysis_results: 分析结果数据
        :return: HTML格式的报告内容
        """
        try:
            # 先生成Markdown
            md_content = self.generate_daily_report(analysis_results)

            # 如果有模板文件，使用模板渲染
            if self.env and self.env.get_template('index.html'):
                template = self.env.get_template('index.html')
                # 复制数据并移除date避免重复
                context_data = analysis_results.copy()
                if 'date' in context_data:
                    del context_data['date']
                return template.render(
                    content=markdown.markdown(md_content, extensions=['tables']),
                    date=analysis_results.get('date', datetime.datetime.now().strftime('%Y年%m月%d日')),
                    **context_data
                )
            else:
                # 使用默认模板
                html_template = """
                <!DOCTYPE html>
                <html lang="zh-CN">
                <head>
                    <meta charset="UTF-8">
                    <title>A股量化日报 - {{ date }}</title>
                    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@3.3.0/dist/tailwind.min.css">
                    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/font-awesome@6.4.0/css/all.min.css">
                    <style>
                        body {
                            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
                            color: #e0e0e0;
                        }
                        .chart-container {
                            background: rgba(26, 26, 46, 0.8);
                            border-radius: 8px;
                            padding: 20px;
                            backdrop-filter: blur(10px);
                        }
                        .table-container {
                            overflow-x: auto;
                        }
                        table {
                            border-collapse: collapse;
                            width: 100%;
                        }
                        th, td {
                            border: 1px solid rgba(255, 255, 255, 0.1);
                            padding: 8px;
                            text-align: left;
                        }
                        th {
                            background-color: rgba(255, 255, 255, 0.1);
                        }
                    </style>
                </head>
                <body class="min-h-screen">
                    <div class="container mx-auto px-4 py-8">
                        <div class="text-center mb-8">
                            <h1 class="text-4xl font-bold mb-2">📈 A股量化日报</h1>
                            <p class="text-xl">{{ date }}</p>
                        </div>

                        <div class="prose prose-invert max-w-none">
                            {{ content | safe }}
                        </div>
                    </div>
                </body>
                </html>
                """

                # 替换变量
                html_content = html_template.replace('{{ date }}', analysis_results.get('date', datetime.datetime.now().strftime('%Y年%m月%d日')))
                html_content = html_content.replace('{{ content | safe }}', markdown.markdown(md_content, extensions=['tables']))

                return html_content

        except Exception as e:
            print(f"生成HTML报告失败: {e}")
            return ""

    def save_report(self, content: str, filename: str):
        """
        保存报告文件
        :param content: 报告内容
        :param filename: 保存路径
        """
        try:
            # 创建目录
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # 写入文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"报告已成功保存至: {filename}")
            return True

        except Exception as e:
            print(f"保存报告失败: {e}")
            return False

    def generate_stock_report(self, symbol: str, analysis_results: Dict) -> str:
        """
        生成个股分析报告
        :param symbol: 股票代码
        :param analysis_results: 个股分析结果
        :return: Markdown格式的报告
        """
        try:
            md_content = f"# 🐎 {symbol} 个股深度分析报告\n\n"
            md_content += f"*报告生成时间: {datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}*\n\n"

            # 基本信息
            md_content += "## 📋 基本信息\n"
            md_content += f"- **股票代码**: {symbol}\n"
            md_content += f"- **综合评分**: {analysis_results.get('composite_score', 0):.1f}分\n"
            md_content += f"- **投资评级**: {analysis_results.get('investment_rating', '')}\n\n"

            # 估值分析
            valuation = analysis_results.get('valuation', {})
            if valuation:
                md_content += "## 📊 估值分析\n"
                md_content += f"- **市盈率(PE)**: {valuation.get('pe', 0):.1f} (行业平均: {valuation.get('industry_pe', 0):.1f})\n"
                md_content += f"- **市净率(PB)**: {valuation.get('pb', 0):.1f} (行业平均: {valuation.get('industry_pb', 0):.1f})\n"
                md_content += f"- **估值结论**: {valuation.get('valuation_conclusion', '')}\n\n"

            # 财务分析
            financial_health = analysis_results.get('financial_health', {})
            if financial_health:
                md_content += "## 🏥 财务健康分析\n"
                md_content += f"- **资产负债率**: {financial_health.get('debt_ratio', 0):.1f}%\n"
                md_content += f"- **流动比率**: {financial_health.get('current_ratio', 0):.2f}\n"
                md_content += f"- **财务健康**: {financial_health.get('health_conclusion', '')}\n\n"

            # 成长能力
            growth_ability = analysis_results.get('growth_ability', {})
            if growth_ability:
                md_content += "## 🚀 成长能力分析\n"
                md_content += f"- **营收增长率**: {growth_ability.get('revenue_growth', 0):.1f}%\n"
                md_content += f"- **净利润增长率**: {growth_ability.get('profit_growth', 0):.1f}%\n"
                md_content += f"- **成长能力**: {growth_ability.get('growth_conclusion', '')}\n\n"

            # 技术分析
            technical = analysis_results.get('technical', {})
            if technical:
                md_content += "## 📈 技术面分析\n"
                md_content += f"- **趋势方向**: {technical.get('trend', {}).get('trend_direction', '')}\n"
                md_content += f"- **技术评分**: {technical.get('technical_score', 0):.1f}\n"
                md_content += f"- **交易信号**: {technical.get('trading_signal', '')}\n\n"

                support_resistance = technical.get('support_resistance', {})
                if support_resistance:
                    md_content += "### 🎯 支撑阻力分析\n"
                    md_content += f"- **第一支撑位**: {support_resistance.get('immediate_support', '')}\n"
                    md_content += f"- **第二支撑位**: {support_resistance.get('support_levels', [''])[0] if support_resistance.get('support_levels') else ''}\n"
                    md_content += f"- **第一压力位**: {support_resistance.get('immediate_resistance', '')}\n"
                    md_content += f"- **第二压力位**: {support_resistance.get('resistance_levels', [''])[0] if support_resistance.get('resistance_levels') else ''}\n\n"

            # 操作建议
            md_content += "## 🎮 操作建议\n"
            md_content += f"- **仓位建议**: {self._get_position_suggestion(analysis_results.get('composite_score', 0))}\n"
            md_content += f"- **入场时机**: {self._get_entry_suggestion(analysis_results.get('technical', {}).get('trading_signal', ''))}\n"
            md_content += f"- **止损点位**: {self._get_stop_loss_suggestion(technical.get('support_resistance', {}))}\n"

            return md_content

        except Exception as e:
            print(f"生成个股报告失败: {e}")
            return ""

    # 辅助方法
    def _get_sentiment_emoji(self, value, threshold=0.5):
        """获取情绪表情"""
        if value > threshold + 0.2:
            return "🟢 情绪高涨"
        elif value > threshold:
            return "🟡 情绪温和"
        elif value < threshold - 0.2:
            return "🔴 情绪低迷"
        else:
            return "⚪ 情绪中性"

    def _get_profit_emoji(self, up_ratio):
        """获取赚钱效应表情"""
        if up_ratio > 0.7:
            return "🟢 赚钱效应极好"
        elif up_ratio > 0.5:
            return "🟡 赚钱效应较好"
        elif up_ratio < 0.3:
            return "🔴 赚钱效应较差"
        else:
            return "⚪ 赚钱效应一般"

    def _get_strength_emoji(self, limit_up_ratio):
        """获取强度表情"""
        if limit_up_ratio > 5:
            return "🚀 强势行情"
        elif limit_up_ratio > 2:
            return "🟢 强度较高"
        elif limit_up_ratio < 1:
            return "🔴 强度较弱"
        else:
            return "⚪ 强度一般"

    def _get_volume_emoji(self, volume_ratio):
        """获取量能表情"""
        if volume_ratio > 1.5:
            return "📈 放量上涨"
        elif volume_ratio > 1.2:
            return "🟢 量能放大"
        elif volume_ratio < 0.8:
            return "📉 缩量下跌"
        else:
            return "⚪ 量能正常"

    def _get_position_suggestion(self, score):
        """获取仓位建议"""
        if score >= 80:
            return "80%-100% 重仓"
        elif score >= 60:
            return "50%-70% 中仓"
        elif score >= 40:
            return "20%-40% 轻仓"
        else:
            return "0%-10% 观望"

    def _get_entry_suggestion(self, trading_signal):
        """获取入场建议"""
        if "买入" in trading_signal:
            return "立即入场"
        elif "卖出" in trading_signal:
            return "等待机会"
        else:
            return "逢低吸纳"

    def _get_stop_loss_suggestion(self, support_resistance):
        """获取止损建议"""
        if support_resistance:
            return support_resistance.get('immediate_support', '根据技术形态设置')
        else:
            return '根据技术形态设置'

if __name__ == "__main__":
    # 测试代码
    generator = ReportGenerator()

    # 模拟数据
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

    # 生成报告
    md_report = generator.generate_daily_report(test_data)
    html_report = generator.generate_html_report(test_data)

    # 保存报告
    generator.save_report(md_report, 'test_daily_report.md')
    generator.save_report(html_report, 'test_daily_report.html')