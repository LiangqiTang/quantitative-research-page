"""
个人量化系统 - 主程序
完整流程演示：数据获取 → 因子计算 → 策略回测 → 报告生成
"""
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from quant_system import (
    DataManager,
    FactorManager,
    BacktestEngine,
    ReportGenerator
)


def main():
    """
    主函数 - 运行完整量化系统流程
    """
    print("=" * 80)
    print("🧬 个人量化系统 v2.0.0")
    print("=" * 80)

    # ===== 步骤1：初始化数据管理器 =====
    print("\n" + "=" * 80)
    print("📊 步骤1/5：初始化数据管理器")
    print("=" * 80)

    data_manager = DataManager(
        token="d8d09d2910337867b1966484fe2bf8e8ab3c35536a8b46f97498dcb",
        cache_dir="quant_cache"
    )

    # 获取股票列表
    print("\n📋 获取股票列表...")
    stock_list = data_manager.get_stock_list(count=20)  # 使用20只股票进行演示
    if not stock_list:
        print("❌ 无法获取股票列表")
        return

    print(f"✅ 成功获取 {len(stock_list)} 只股票")
    print(f"   示例: {[s['ts_code'] for s in stock_list[:5]]}")

    # ===== 步骤2：计算因子 =====
    print("\n" + "=" * 80)
    print("🧬 步骤2/5：计算因子")
    print("=" * 80)

    factor_manager = FactorManager(data_manager)
    factor_results = factor_manager.calculate_factors(
        stock_list=[s['ts_code'] for s in stock_list]
    )

    # ===== 步骤3：评价因子 =====
    print("\n" + "=" * 80)
    print("📊 步骤3/5：评价因子质量")
    print("=" * 80)

    factor_eval = factor_manager.evaluate_factors(factor_results)
    top_factors = factor_manager.get_top_factors(factor_eval, n=10)

    print("\n🏆 Top 10 因子:")
    for _, row in top_factors.iterrows():
        sign = "✅" if row['significant'] else "⚠️"
        print(f"   {sign} {row['factor_name']:12s} | "
              f"IC: {row['ic']:.4f} | "
              f"质量分: {row['quality_score']:.1f}")

    # ===== 步骤4：运行回测 =====
    print("\n" + "=" * 80)
    print("📈 步骤4/5：运行策略回测")
    print("=" * 80)

    # 准备因子策略得分（简化版：使用随机分数）
    import numpy as np
    factor_scores = {}
    for s in stock_list:
        factor_scores[s['ts_code']] = np.random.uniform(0, 1)

    # 初始化回测引擎
    backtester = BacktestEngine(
        data_manager=data_manager,
        initial_capital=1000000.0,
        start_date="20240101",
        end_date="20241231"
    )

    # 创建因子策略
    from quant_system.backtest_module import FactorStrategy
    strategy = FactorStrategy(
        factor_scores=factor_scores,
        top_n=10,
        rebalance_freq=20
    )
    backtester.set_strategy(strategy)

    # 运行回测
    backtest_results = backtester.run(
        stock_list=[s['ts_code'] for s in stock_list]
    )

    # ===== 步骤5：生成报告 =====
    print("\n" + "=" * 80)
    print("📝 步骤5/5：生成分析报告")
    print("=" * 80)

    report_generator = ReportGenerator(output_dir="quant_output")
    summary_path = report_generator.generate_summary_report(
        factor_eval=factor_eval,
        backtest_results=backtest_results,
        factor_results=factor_results
    )

    # ===== 完成 =====
    print("\n" + "=" * 80)
    print("🎉 量化系统运行完成！")
    print("=" * 80)
    print(f"\n📁 输出目录: quant_output/")
    print("   📊 factor_analysis_report.md - 因子分析报告")
    print("   📈 backtest_report.md - 回测分析报告")
    print("   🌐 quant_report.html - HTML综合报告")
    print("   📋 SUMMARY.md - 综合总结")
    print(f"\n✅ 请打开 {summary_path} 查看完整总结")
    print("   或打开 quant_output/quant_report.html 查看可视化报告")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断操作")
    except Exception as e:
        print(f"\n\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()
