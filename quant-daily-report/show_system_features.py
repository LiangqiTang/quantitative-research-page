"""
个人量化系统 v4.0 - 功能展示
展示系统的所有模块和功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def show_file_structure():
    """展示文件结构"""
    print("="*80)
    print("📁 个人量化系统 v4.0 - 文件结构".center(80))
    print("="*80)

    structure = """
quant-daily-report/
├── quant_system/                    # 核心量化系统包
│   ├── __init__.py                  # 模块导出（v4.0.0）
│   │
│   ├── 第一阶段：基础模块
│   ├── data_module.py                # 数据管理（Tushare/Baostock/缓存）
│   ├── factor_module.py              # 基础因子库（30+因子）
│   ├── backtest_module.py            # 事件驱动回测引擎
│   ├── report_module.py              # 报告生成
│   │
│   ├── 第一阶段：因子体系专业化（已完成）
│   ├── alpha_factors.py              # Alpha因子库（60+因子，Alpha101风格）
│   ├── factor_evaluator.py           # 因子评价引擎（IC/IR/分组回测/因子衰减）
│   ├── factor_neutralizer.py         # 因子中性化（市值/行业/Barra/正交化）
│   ├── transaction_cost.py           # 交易成本模型（佣金/滑点/冲击成本/涨跌停）
│   ├── position_manager.py           # 仓位管理（等权重/风险预算/市值权重）
│   │
│   ├── 第二阶段：策略与回测引擎增强（已完成）
│   ├── portfolio_optimizer.py        # 组合优化器（5种优化算法）
│   ├── risk_controller.py            # 风险控制器（止损/止盈/回撤控制）
│   ├── metrics_extended.py           # 扩展绩效指标（20+专业指标）
│   ├── performance_attribution.py    # 业绩归因（Brinson/因子归因）
│   └── overfitting_detector.py      # 过拟合检测（样本外/Walk Forward）
│
├── 主程序和演示
├── main_quant_system.py             # v3.0 主程序
├── demo_enhanced_system.py          # 第一阶段模块演示
├── main_v4.py                       # v4.0 完整演示程序 ⭐
└── show_system_features.py          # 本文件 - 系统功能展示
    """
    print(structure)


def show_core_modules():
    """展示核心模块"""
    print("\n" + "="*80)
    print("🎯 核心模块功能概览".center(80))
    print("="*80)

    modules = [
        {
            "name": "📊 data_module.py",
            "features": [
                "DataManager - 统一数据管理器",
                "Tushare + Baostock 双数据源",
                "本地缓存系统（避免重复请求）",
                "自动重试和错误处理"
            ]
        },
        {
            "name": "📈 factor_module.py",
            "features": [
                "FactorCalculator - 30+基础因子计算",
                "技术指标类：MA、MACD、RSI、KDJ、BOLL",
                "价量类：VROCP、VR、OBV",
                "风格类：市值、Beta、动量、波动率"
            ]
        },
        {
            "name": "🔄 backtest_module.py",
            "features": [
                "BacktestEngine - 事件驱动回测引擎",
                "Strategy 基类，支持自定义策略",
                "Portfolio - 组合管理",
                "PerformanceMetrics - 基础绩效指标"
            ]
        },
        {
            "name": "📋 report_module.py",
            "features": [
                "ReportGenerator - 报告生成器",
                "HTML格式报告输出",
                "Matplotlib可视化图表",
                "因子分析报告"
            ]
        }
    ]

    for module in modules:
        print(f"\n{module['name']}")
        for feature in module['features']:
            print(f"  ✓ {feature}")


def show_factor_system():
    """展示因子体系"""
    print("\n" + "="*80)
    print("🔬 因子体系专业化（第一阶段）".center(80))
    print("="*80)

    factor_modules = [
        {
            "name": "🧪 alpha_factors.py",
            "features": [
                "AlphaFactorCalculator - 60+专业Alpha因子",
                "Alpha101风格价量因子",
                "技术指标增强因子",
                "动量、反转、波动率类因子",
                "资金流向类因子"
            ]
        },
        {
            "name": "📊 factor_evaluator.py",
            "features": [
                "FactorEvaluator - 专业因子评价引擎",
                "IC/IR计算（Spearman/Pearson）",
                "分组回测（Layered Backtest）",
                "因子衰减分析（Factor Decay）",
                "多头/空头/多空组合评价"
            ]
        },
        {
            "name": "⚖️ factor_neutralizer.py",
            "features": [
                "FactorNeutralizer - 因子中性化",
                "市值中性化",
                "行业中性化",
                "Barra风格中性化",
                "因子正交化"
            ]
        },
        {
            "name": "💰 transaction_cost.py",
            "features": [
                "TransactionCostModel - 交易成本模型",
                "佣金、印花税、过户费",
                "滑点模型（固定/比例/成交量比例）",
                "冲击成本（Almgren-Chriss）",
                "涨跌停/停牌处理"
            ]
        },
        {
            "name": "🎯 position_manager.py",
            "features": [
                "PositionManager - 仓位管理",
                "等权重配置",
                "市值权重配置",
                "风险预算配置（Risk Budgeting）",
                "主动风险预算（Active Risk）"
            ]
        }
    ]

    for module in factor_modules:
        print(f"\n{module['name']}")
        for feature in module['features']:
            print(f"  ✓ {feature}")


def show_strategy_enhancement():
    """展示策略与回测引擎增强"""
    print("\n" + "="*80)
    print("🚀 策略与回测引擎增强（第二阶段）".center(80))
    print("="*80)

    enhancement_modules = [
        {
            "name": "📊 portfolio_optimizer.py",
            "features": [
                "PortfolioOptimizer - 组合优化器",
                "最小方差组合（Min Variance）",
                "最大夏普比率组合（Max Sharpe）",
                "风险平价组合（Risk Parity）",
                "最大分散化组合（MDP）",
                "均值方差优化（Markowitz）",
                "有效前沿计算"
            ]
        },
        {
            "name": "🛡️ risk_controller.py",
            "features": [
                "RiskController - 风险控制器",
                "单笔止损止盈（固定/移动）",
                "组合最大回撤控制",
                "单股/行业仓位限制",
                "目标波动率策略（Volatility Targeting）",
                "杠杆控制"
            ]
        },
        {
            "name": "📈 metrics_extended.py",
            "features": [
                "ExtendedPerformanceMetrics - 扩展绩效指标",
                "风险调整收益：Sortino、Omega、Calmar、Sterling",
                "收益分布：偏度、峰度",
                "风险价值：VaR（历史/参数）、CVaR",
                "交易统计：胜率、盈亏比、平均持仓时间",
                "基准比较：IR、TE、CAPM Alpha/Beta"
            ]
        },
        {
            "name": "🎯 performance_attribution.py",
            "features": [
                "BrinsonAttribution - Brinson业绩归因",
                "资产配置收益（Allocation）",
                "个股选择收益（Selection）",
                "交互收益（Interaction）",
                "FactorAttribution - 因子归因",
                "多期归因聚合"
            ]
        },
        {
            "name": "🔍 overfitting_detector.py",
            "features": [
                "OverfittingDetector - 过拟合检测器",
                "样本内 vs 样本外对比",
                "Walk Forward Analysis（滚动窗口验证）",
                "参数敏感性分析",
                "策略退化检测"
            ]
        }
    ]

    for module in enhancement_modules:
        print(f"\n{module['name']}")
        for feature in module['features']:
            print(f"  ✓ {feature}")


def show_usage_examples():
    """展示使用示例"""
    print("\n" + "="*80)
    print("💡 快速使用示例".center(80))
    print("="*80)

    examples = [
        {
            "title": "1️⃣  导入系统",
            "code": """
from quant_system import (
    # 核心模块
    DataManager, FactorManager, BacktestEngine,

    # 因子体系
    AlphaFactorCalculator, FactorEvaluator, FactorNeutralizer,

    # 交易执行
    TransactionCostModel, PositionManager,

    # v4.0 新模块
    PortfolioOptimizer, RiskController,
    ExtendedPerformanceMetrics,
    BrinsonAttribution, OverfittingDetector
)
"""
        },
        {
            "title": "2️⃣  运行完整演示",
            "code": """
# 运行 v4.0 完整演示
python main_v4.py

# 运行第一阶段演示
python demo_enhanced_system.py
"""
        },
        {
            "title": "3️⃣  组合优化示例",
            "code": """
from quant_system import PortfolioOptimizer, get_simple_optimizer

# 创建优化器
optimizer = PortfolioOptimizer(returns=returns_df, risk_free_rate=0.03)

# 运行所有优化方法
results = optimizer.optimize_all(min_weight=0.05, max_weight=0.3)

# 获取风险平价组合
rp_result = results[OptimizationMethod.RISK_PARITY]
print(rp_result.weights)
"""
        },
        {
            "title": "4️⃣  风险控制示例",
            "code": """
from quant_system import get_conservative_risk_controller

# 创建风险控制器
risk_ctrl = get_conservative_risk_controller()

# 登记持仓
risk_ctrl.register_position('000001.SZ', 1000, 10.0, '2024-01-01')

# 更新价格并检查止损
risk_ctrl.update_position_prices({'000001.SZ': 9.0})
triggered, result = risk_ctrl.check_stop_loss('000001.SZ')
"""
        },
        {
            "title": "5️⃣  过拟合检测示例",
            "code": """
from quant_system import detect_overfitting, walk_forward_validation

# 样本内/外对比
result = detect_overfitting(returns, train_ratio=0.7)
print(f"是否过拟合: {result.is_overfitting}")
print(f"警告: {result.warning_signs}")

# Walk Forward 验证
wf_result = walk_forward_validation(returns, window_size=252, step_size=60)
"""
        }
    ]

    for example in examples:
        print(f"\n{example['title']}")
        print("-" * 60)
        print(example['code'])


def show_statistics():
    """展示统计信息"""
    print("\n" + "="*80)
    print("📊 系统统计".center(80))
    print("="*80)

    stats = {
        "版本": "v4.0.0",
        "核心模块": "4个",
        "因子相关模块": "5个",
        "策略增强模块": "5个",
        "总模块数": "14个",
        "因子数量": "90+",
        "绩效指标": "25+",
        "优化算法": "5种",
        "演示程序": "3个"
    }

    for key, value in stats.items():
        print(f"  {key:<15s}: {value}")


def main():
    """主程序"""
    print("\n" + "="*80)
    print("🚀 个人量化系统 v4.0 - 功能展示".center(80))
    print("="*80)

    # 文件结构
    show_file_structure()

    # 核心模块
    show_core_modules()

    # 因子体系
    show_factor_system()

    # 策略增强
    show_strategy_enhancement()

    # 使用示例
    show_usage_examples()

    # 统计信息
    show_statistics()

    print("\n" + "="*80)
    print("🎉 系统功能展示完成!".center(80))
    print("="*80)
    print("\n💡 下一步:")
    print("  运行 'python main_v4.py' 查看完整演示")
    print("  运行 'python demo_enhanced_system.py' 查看第一阶段演示")


if __name__ == '__main__':
    main()
