"""
个人量化系统 v4.0 - 完整演示程序

展示 v4.0 新增的专业功能：
1. 组合优化 - 最小方差、最大夏普、风险平价等
2. 风险控制 - 止损止盈、回撤控制、波动率控制
3. 扩展绩效指标 - Sortino、Omega、VaR、CVaR 等
4. 业绩归因 - Brinson归因、因子归因
5. 过拟合检测 - 样本内/外对比、Walk Forward分析
"""

import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 导入量化系统模块
from quant_system import (
    # 核心模块
    DataManager,

    # v4.0 新增专业模块
    PortfolioOptimizer,
    OptimizationMethod,
    compare_optimization_results,
    get_simple_optimizer,

    RiskController,
    get_simple_risk_controller,
    get_conservative_risk_controller,

    ExtendedPerformanceMetrics,
    calculate_performance_summary,

    BrinsonAttribution,
    FactorAttribution,
    calculate_brinson_attribution,
    calculate_factor_attribution,

    OverfittingDetector,
    detect_overfitting,
    walk_forward_validation,
)


def generate_sample_returns(n_assets: int = 10, n_days: int = 500) -> pd.DataFrame:
    """
    生成模拟收益率数据（用于演示）

    Args:
        n_assets: 资产数量
        n_days: 天数

    Returns:
        收益率DataFrame
    """
    np.random.seed(42)

    # 生成具有不同特性的收益率
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')

    # 生成协方差矩阵（具有一定相关性）
    corr_matrix = np.random.rand(n_assets, n_assets)
    corr_matrix = (corr_matrix + corr_matrix.T) / 2  # 对称
    np.fill_diagonal(corr_matrix, 1.0)

    # 生成波动率
    vols = np.random.uniform(0.01, 0.03, n_assets)
    cov_matrix = np.outer(vols, vols) * corr_matrix

    # 生成收益率
    returns = np.random.multivariate_normal(
        mean=np.random.uniform(-0.0005, 0.001, n_assets),
        cov=cov_matrix,
        size=n_days
    )

    asset_names = [f'STOCK_{i:02d}' for i in range(n_assets)]
    return pd.DataFrame(returns, index=dates, columns=asset_names)


def demo_portfolio_optimization():
    """演示组合优化模块"""
    print("\n" + "="*80)
    print("📊 组合优化模块演示".center(80))
    print("="*80)

    # 生成模拟数据
    print("\n1️⃣  生成模拟收益率数据...")
    returns = generate_sample_returns(n_assets=8, n_days=500)
    print(f"   数据形状: {returns.shape}")
    print(f"   时间范围: {returns.index[0].date()} 至 {returns.index[-1].date()}")

    # 创建优化器
    print("\n2️⃣  创建组合优化器...")
    optimizer = PortfolioOptimizer(
        returns=returns,
        risk_free_rate=0.03,
        frequency=252
    )
    print("   ✅ 优化器创建完成")

    # 运行所有优化方法
    print("\n3️⃣  运行所有优化方法...")
    results = optimizer.optimize_all(min_weight=0.05, max_weight=0.3)

    # 对比结果
    print("\n4️⃣  优化结果对比:")
    comparison = compare_optimization_results(results)
    print(comparison.round(4))

    # 详细展示某个方法的结果
    print("\n5️⃣  风险平价组合详情:")
    rp_result = results[OptimizationMethod.RISK_PARITY]
    print(f"   预期年化收益: {rp_result.expected_return:.2%}")
    print(f"   预期年化波动: {rp_result.expected_volatility:.2%}")
    print(f"   夏普比率: {rp_result.sharpe_ratio:.3f}")
    print(f"\n   资产权重:")
    for asset, weight in rp_result.weights.items():
        print(f"     {asset}: {weight:.2%}")

    print("\n   ✅ 组合优化演示完成!")


def demo_risk_control():
    """演示风险控制模块"""
    print("\n" + "="*80)
    print("🛡️  风险控制模块演示".center(80))
    print("="*80)

    # 创建风险控制器
    print("\n1️⃣  创建保守型风险控制器...")
    risk_controller = get_conservative_risk_controller()
    print(f"   最大回撤容忍度: {risk_controller.max_drawdown:.1%}")
    print(f"   单笔止损: {risk_controller.stop_loss_pct:.1%}")
    print(f"   目标波动率: {risk_controller.target_volatility:.1%}")
    print(f"   单股最大仓位: {risk_controller.max_single_position:.1%}")

    # 登记持仓
    print("\n2️⃣  登记模拟持仓...")
    risk_controller.register_position(
        ts_code='STOCK_00',
        quantity=1000,
        price=10.0,
        date='2024-01-01'
    )
    risk_controller.register_position(
        ts_code='STOCK_01',
        quantity=500,
        price=20.0,
        date='2024-01-01'
    )
    print(f"   ✅ 已登记 {len(risk_controller.position_entries)} 个持仓")

    # 更新价格
    print("\n3️⃣  更新持仓价格（模拟下跌）...")
    risk_controller.update_position_prices({
        'STOCK_00': 8.5,  # 下跌15%，触发止损
        'STOCK_01': 21.0
    })

    # 检查止损
    print("\n4️⃣  检查止损止盈...")
    for ts_code in ['STOCK_00', 'STOCK_01']:
        triggered, result = risk_controller.check_position_stop(ts_code)
        status = "⚠️ 触发" if triggered else "✅ 正常"
        print(f"   {ts_code}: {status} ({result.value})")

    # 记录组合净值
    print("\n5️⃣  记录组合净值历史（用于回撤计算）...")
    np.random.seed(123)
    values = 1000000 * (1 + np.random.normal(0, 0.01, 100)).cumprod()
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    for date, value in zip(dates, values):
        risk_controller.record_portfolio_value(value, date.strftime('%Y-%m-%d'))

    # 计算当前回撤
    current_dd = risk_controller.calculate_current_drawdown()
    print(f"   当前回撤: {current_dd:.2%}")

    # 风险概览
    print("\n6️⃣  风险概览:")
    summary = risk_controller.get_risk_summary()
    for key, value in summary.items():
        if key != 'positions':
            print(f"   {key}: {value}")

    print("\n   ✅ 风险控制演示完成!")


def demo_extended_metrics():
    """演示扩展绩效指标模块"""
    print("\n" + "="*80)
    print("📈 扩展绩效指标演示".center(80))
    print("="*80)

    # 生成模拟收益率
    print("\n1️⃣  生成模拟收益率...")
    np.random.seed(42)
    n_days = 500
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')

    # 策略收益率（具有正偏度和肥尾）
    strategy_returns = pd.Series(
        np.random.normal(0.0005, 0.015, n_days) +
        np.random.standard_t(3, n_days) * 0.005,
        index=dates
    )

    # 基准收益率
    benchmark_returns = pd.Series(
        np.random.normal(0.0003, 0.012, n_days),
        index=dates
    )

    # 创建绩效计算器
    print("\n2️⃣  创建扩展绩效指标计算器...")
    metrics_calc = ExtendedPerformanceMetrics(
        returns=strategy_returns,
        benchmark_returns=benchmark_returns,
        risk_free_rate=0.03,
        frequency=252
    )

    # 计算所有指标
    print("\n3️⃣  计算所有绩效指标...")
    all_metrics = metrics_calc.calculate_all()

    # 分类显示
    print("\n4️⃣  绩效指标详情:")

    print("\n   📊 基础收益指标:")
    print(f"      总收益率: {all_metrics['total_return']:.2%}")
    print(f"      年化收益率: {all_metrics['annual_return']:.2%}")
    print(f"      波动率: {all_metrics['volatility']:.2%}")
    print(f"      最大回撤: {all_metrics['max_drawdown']:.2%}")

    print("\n   🎯 风险调整收益指标:")
    print(f"      夏普比率: {all_metrics['sharpe_ratio']:.3f}")
    print(f"      Sortino比率: {all_metrics['sortino_ratio']:.3f}")
    print(f"      Omega比率: {all_metrics['omega_ratio']:.3f}")
    print(f"      Calmar比率: {all_metrics['calmar_ratio']:.3f}")

    print("\n   📈 收益分布指标:")
    print(f"      偏度: {all_metrics['skewness']:.3f}")
    print(f"      峰度: {all_metrics['kurtosis']:.3f}")
    print(f"      历史VaR (95%): {all_metrics['var_historical_95']:.2%}")
    print(f"      CVaR (95%): {all_metrics['cvar_95']:.2%}")

    print("\n   🔄 连续盈亏:")
    print(f"      最大连续亏损天数: {all_metrics['max_consecutive_losses']}")
    print(f"      最大连续盈利天数: {all_metrics['max_consecutive_wins']}")

    if 'capm_alpha' in all_metrics:
        print("\n   📊 基准比较指标:")
        print(f"      超额收益率: {all_metrics['excess_return']:.2%}")
        print(f"      信息比率: {all_metrics['information_ratio']:.3f}")
        print(f"      跟踪误差: {all_metrics['tracking_error']:.2%}")
        print(f"      CAPM Alpha: {all_metrics['capm_alpha']:.2%}")
        print(f"      CAPM Beta: {all_metrics['capm_beta']:.3f}")

    print("\n   ✅ 扩展绩效指标演示完成!")


def demo_performance_attribution():
    """演示业绩归因模块"""
    print("\n" + "="*80)
    print("🎯 业绩归因模块演示".center(80))
    print("="*80)

    # 生成模拟数据
    print("\n1️⃣  生成模拟归因数据...")
    np.random.seed(42)
    n_stocks = 10

    # 股票列表
    stocks = [f'STOCK_{i:02d}' for i in range(n_stocks)]

    # 行业分类
    industries = ['金融', '科技', '消费', '医药', '周期']
    industry_class = pd.Series(
        np.random.choice(industries, n_stocks),
        index=stocks
    )

    # 组合权重
    port_weights = pd.Series(np.random.dirichlet(np.ones(n_stocks)), index=stocks)

    # 基准权重（市值加权）
    bench_weights = pd.Series(np.random.dirichlet(np.ones(n_stocks) * 2), index=stocks)

    # 股票收益率
    stock_returns = pd.Series(np.random.uniform(-0.1, 0.15, n_stocks), index=stocks)

    print(f"   股票数量: {n_stocks}")
    print(f"   行业分布: {industry_class.value_counts().to_dict()}")

    # Brinson归因
    print("\n2️⃣  计算Brinson归因...")
    brinson_result = calculate_brinson_attribution(
        portfolio_weights=port_weights,
        benchmark_weights=bench_weights,
        stock_returns=stock_returns,
        industry_classification=industry_class,
        period='2024-01'
    )

    print("\n3️⃣  Brinson归因结果:")
    print(f"   总超额收益: {brinson_result.total_excess_return:.2%}")
    print(f"   资产配置收益: {brinson_result.allocation_return:.2%}")
    print(f"   个股选择收益: {brinson_result.selection_return:.2%}")
    print(f"   交互收益: {brinson_result.interaction_return:.2%}")

    if not brinson_result.industry_details.empty:
        print("\n   行业详情:")
        print(brinson_result.industry_details[
            ['portfolio_weight', 'benchmark_weight', 'allocation', 'selection']
        ].round(4))

    # 因子归因演示
    print("\n4️⃣  因子归因演示...")

    # 模拟因子暴露（3个因子）
    factor_exposures = pd.DataFrame(
        np.random.normal(0, 1, (n_stocks, 3)),
        index=stocks,
        columns=['MKT', 'SMB', 'HML']
    )

    # 因子收益率
    factor_returns = pd.Series([0.02, 0.01, -0.005], index=['MKT', 'SMB', 'HML'])

    # 计算因子归因
    factor_result = calculate_factor_attribution(
        factor_exposures=factor_exposures,
        factor_returns=factor_returns,
        portfolio_weights=port_weights,
        period='2024-01'
    )

    print("\n5️⃣  因子归因结果:")
    print("   因子贡献:")
    for factor, contrib in factor_result.factor_contributions.items():
        print(f"     {factor}: {contrib:.2%}")
    print(f"   特异贡献: {factor_result.specific_contribution:.2%}")
    print(f"   总收益: {factor_result.total_return:.2%}")

    print("\n   ✅ 业绩归因演示完成!")


def demo_overfitting_detection():
    """演示过拟合检测模块"""
    print("\n" + "="*80)
    print("🔍 过拟合检测模块演示".center(80))
    print("="*80)

    # 生成模拟收益率
    print("\n1️⃣  生成模拟策略收益率...")
    np.random.seed(42)
    n_days = 600
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')

    # 策略1：样本内表现好，样本外衰减（过拟合）
    np.random.seed(42)
    returns_1 = np.concatenate([
        np.random.normal(0.001, 0.01, n_days//2),   # 样本内：好
        np.random.normal(-0.0002, 0.015, n_days//2)  # 样本外：差
    ])
    returns_1 = pd.Series(returns_1, index=dates)

    # 创建检测器
    print("\n2️⃣  创建过拟合检测器...")
    detector = OverfittingDetector(returns=returns_1)

    # 样本内/外对比
    print("\n3️⃣  样本内 vs 样本外对比...")
    tt_result = detector.in_sample_vs_out_sample(train_ratio=0.5)

    print(f"\n   状态: {tt_result.status.value}")
    print(f"   是否过拟合: {'⚠️ 是' if tt_result.is_overfitting else '✅ 否'}")

    print(f"\n   样本内指标:")
    for key, value in tt_result.in_sample_metrics.items():
        if isinstance(value, float):
            print(f"     {key}: {value:.4f}")

    print(f"\n   样本外指标:")
    for key, value in tt_result.out_sample_metrics.items():
        if isinstance(value, float):
            print(f"     {key}: {value:.4f}")

    if tt_result.warning_signs:
        print(f"\n   ⚠️  警告迹象:")
        for warning in tt_result.warning_signs:
            print(f"     - {warning}")

    # Walk Forward分析
    print("\n4️⃣  Walk Forward分析...")
    wf_result = detector.walk_forward_analysis(
        window_size=120,
        step_size=30
    )

    if not wf_result.period_results.empty:
        print(f"\n   滚动窗口期数: {len(wf_result.period_results)}")
        print(f"   平均样本外收益率: {wf_result.aggregate_metrics.get('avg_out_sample_return', 0):.4f}")
        print(f"   正收益期数比例: {wf_result.aggregate_metrics.get('positive_periods', 0):.1%}")
        print(f"   稳定性评分: {wf_result.stability_score:.3f}")
        print(f"   一致性评分: {wf_result.consistency_score:.3f}")

    # 策略退化检测
    print("\n5️⃣  策略退化检测...")
    deg_result = detector.strategy_degradation_detection(
        recent_periods=60,
        lookback_periods=180
    )

    print(f"\n   是否退化: {'⚠️ 是' if deg_result.get('is_degrading', False) else '✅ 否'}")

    if deg_result.get('degradation_signs'):
        print(f"\n   退化迹象:")
        for sign in deg_result['degradation_signs']:
            print(f"     - {sign}")

    print("\n   ✅ 过拟合检测演示完成!")


def main():
    """主程序"""
    print("\n" + "="*80)
    print("🚀 个人量化系统 v4.0 - 完整演示".center(80))
    print("="*80)
    print(f"\n📅 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 1. 组合优化
        demo_portfolio_optimization()

        # 2. 风险控制
        demo_risk_control()

        # 3. 扩展绩效指标
        demo_extended_metrics()

        # 4. 业绩归因
        demo_performance_attribution()

        # 5. 过拟合检测
        demo_overfitting_detection()

    except ImportError as e:
        print(f"\n⚠️  缺少依赖库: {e}")
        print("   请安装: pip install scipy")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("✨ 演示完成!".center(80))
    print("="*80)
    print("\n📚 v4.0 新功能总结:")
    print("   ✅ 组合优化 - 5种专业优化算法")
    print("   ✅ 风险控制 - 止损/回撤/波动率控制")
    print("   ✅ 扩展绩效 - 15+专业绩效指标")
    print("   ✅ 业绩归因 - Brinson和因子归因")
    print("   ✅ 过拟合检测 - 样本外/Walk Forward")


if __name__ == '__main__':
    main()
