#!/usr/bin/env python3
"""
v4.0 目录结构兼容性检查脚本

验证模块目录结构是否正常工作：
- data_modules/, factor_modules/, strategy_modules/ 等
- quant_system/ 向后兼容性测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🔍 个人量化系统 v4.0 - 兼容性检查".center(80))
print("=" * 80)

all_passed = True


def test_import(label, import_func):
    """测试导入"""
    global all_passed
    try:
        result = import_func()
        print(f"✅ {label}: PASSED")
        return result
    except Exception as e:
        print(f"❌ {label}: FAILED - {e}")
        all_passed = False
        return None


print("\n" + "-" * 80)
print("📦 1. 测试模块目录导入".center(80))
print("-" * 80)

# 测试 data_modules
print("\n[data_modules] 数据模块...")
test_import("data_modules.DataManager", lambda: __import__('data_modules', fromlist=['DataManager']).DataManager)
test_import("data_modules.ExtendedDataManager", lambda: __import__('data_modules', fromlist=['ExtendedDataManager']).ExtendedDataManager)

# 测试 factor_modules
print("\n[factor_modules] 因子模块...")
test_import("factor_modules.FactorManager", lambda: __import__('factor_modules', fromlist=['FactorManager']).FactorManager)
test_import("factor_modules.AlphaFactorCalculator", lambda: __import__('factor_modules', fromlist=['AlphaFactorCalculator']).AlphaFactorCalculator)
test_import("factor_modules.FactorEvaluator", lambda: __import__('factor_modules', fromlist=['FactorEvaluator']).FactorEvaluator)
test_import("factor_modules.FactorNeutralizer", lambda: __import__('factor_modules', fromlist=['FactorNeutralizer']).FactorNeutralizer)

# 测试 strategy_modules
print("\n[strategy_modules] 策略模块...")
test_import("strategy_modules.PortfolioOptimizer", lambda: __import__('strategy_modules', fromlist=['PortfolioOptimizer']).PortfolioOptimizer)
test_import("strategy_modules.RiskController", lambda: __import__('strategy_modules', fromlist=['RiskController']).RiskController)
test_import("strategy_modules.MomentumStrategy", lambda: __import__('strategy_modules', fromlist=['MomentumStrategy']).MomentumStrategy)
test_import("strategy_modules.MeanReversionStrategy", lambda: __import__('strategy_modules', fromlist=['MeanReversionStrategy']).MeanReversionStrategy)
test_import("strategy_modules.PairTradingStrategy", lambda: __import__('strategy_modules', fromlist=['PairTradingStrategy']).PairTradingStrategy)

# 测试 backtest_modules
print("\n[backtest_modules] 回测模块...")
test_import("backtest_modules.BacktestEngine", lambda: __import__('backtest_modules', fromlist=['BacktestEngine']).BacktestEngine)
test_import("backtest_modules.EnhancedBacktestEngine", lambda: __import__('backtest_modules', fromlist=['EnhancedBacktestEngine']).EnhancedBacktestEngine)
test_import("backtest_modules.TransactionCostModel", lambda: __import__('backtest_modules', fromlist=['TransactionCostModel']).TransactionCostModel)
test_import("backtest_modules.PositionManager", lambda: __import__('backtest_modules', fromlist=['PositionManager']).PositionManager)

# 测试 analysis_modules
print("\n[analysis_modules] 分析模块...")
test_import("analysis_modules.ExtendedPerformanceMetrics", lambda: __import__('analysis_modules', fromlist=['ExtendedPerformanceMetrics']).ExtendedPerformanceMetrics)
test_import("analysis_modules.BrinsonAttribution", lambda: __import__('analysis_modules', fromlist=['BrinsonAttribution']).BrinsonAttribution)
test_import("analysis_modules.FactorAttribution", lambda: __import__('analysis_modules', fromlist=['FactorAttribution']).FactorAttribution)
test_import("analysis_modules.OverfittingDetector", lambda: __import__('analysis_modules', fromlist=['OverfittingDetector']).OverfittingDetector)

# 测试 report_modules
print("\n[report_modules] 报告模块...")
test_import("report_modules.ReportGenerator", lambda: __import__('report_modules', fromlist=['ReportGenerator']).ReportGenerator)
test_import("report_modules.QuantResearchPipeline", lambda: __import__('report_modules', fromlist=['QuantResearchPipeline']).QuantResearchPipeline)

print("\n" + "-" * 80)
print("🔗 2. 测试向后兼容性 (quant_system)".center(80))
print("-" * 80)

# 测试向后兼容性
print("\n[quant_system] 向后兼容性...")
test_import("quant_system.DataManager", lambda: __import__('quant_system', fromlist=['DataManager']).DataManager)
test_import("quant_system.BacktestEngine", lambda: __import__('quant_system', fromlist=['BacktestEngine']).BacktestEngine)
test_import("quant_system.ReportGenerator", lambda: __import__('quant_system', fromlist=['ReportGenerator']).ReportGenerator)
test_import("quant_system.FactorEvaluator", lambda: __import__('quant_system', fromlist=['FactorEvaluator']).FactorEvaluator)
test_import("quant_system.MomentumStrategy", lambda: __import__('quant_system', fromlist=['MomentumStrategy']).MomentumStrategy)

print("\n" + "-" * 80)
print("📁 3. 验证目录结构".center(80))
print("-" * 80)

# 模块目录
module_dirs = [
    ("data_modules", "数据模块"),
    ("factor_modules", "因子模块"),
    ("strategy_modules", "策略模块"),
    ("backtest_modules", "回测模块"),
    ("analysis_modules", "分析模块"),
    ("report_modules", "报告模块"),
]

# 其他目录
other_dirs = [
    ("docs", "文档目录"),
    ("quant_system", "向后兼容层"),
]

print("\n💻 模块目录（存放代码）:")
for dir_name, description in module_dirs:
    dir_path = project_root / dir_name
    if dir_path.exists() and dir_path.is_dir():
        py_files = list(dir_path.glob("*.py"))
        init_file = dir_path / "__init__.py"
        msg = f"  ✅ {dir_name}/: {description}"
        extras = []
        if init_file.exists():
            extras.append("__init__.py")
        extras.append(f"{len(py_files)} 个 .py 文件")
        if extras:
            msg += f" [{', '.join(extras)}]"
        print(msg)
    else:
        print(f"  ❌ {dir_name}/: 目录不存在")
        all_passed = False

print("\n📂 其他目录:")
for dir_name, description in other_dirs:
    dir_path = project_root / dir_name
    if dir_path.exists() and dir_path.is_dir():
        print(f"  ✅ {dir_name}/: {description}")
    else:
        print(f"  ❌ {dir_name}/: 目录不存在")
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("🎉 所有检查通过!".center(80))
else:
    print("⚠️  部分检查失败，请检查错误信息".center(80))
print("=" * 80)

print(f"\n📂 项目根目录: {project_root}")
print("\n💡 最终目录结构说明:")
print("  - 模块目录 data_modules/ ~ report_modules/: 存放实际的 .py 代码文件")
print("  - 新代码推荐: from data_modules import DataManager, from factor_modules import FactorEvaluator, ...")
print("  - 旧代码兼容: from quant_system import DataManager, FactorEvaluator, ... 仍然可用")
print("\n")
