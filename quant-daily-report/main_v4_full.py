"""
个人量化系统 v4.0 - 完整演示程序（包含 Sprint 2-4 所有新功能）

展示 v4.0 的所有新增专业功能：
Sprint 2: 回测引擎增强
- TradingConstraint（T+1规则、涨跌停、停牌处理）
- EnhancedPortfolio（集成交易成本和仓位管理）
- EnhancedBacktestEngine（增强版回测引擎）

Sprint 3: 高级策略
- MomentumStrategy（横截面/时序/复合动量）
- MeanReversionStrategy（布林带/RSI/反转因子）
- PairTradingStrategy（配对交易）
- EventDrivenStrategy（事件驱动框架）

Sprint 4: 数据扩展与Pipeline
- ExtendedDataManager（行业分类、指数成分、资金流向）
- QuantResearchPipeline（因子研究Pipeline、策略回测Pipeline）

已有的核心模块：
- 组合优化 - 最小方差、最大夏普、风险平价等
- 风险控制 - 止损止盈、回撤控制、波动率控制
- 扩展绩效指标 - Sortino、Omega、VaR、CVaR 等
- 业绩归因 - Brinson归因、因子归因
- 过拟合检测 - 样本内/外对比、Walk Forward分析
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 导入量化系统模块
from quant_system import (
    # 核心模块
    DataManager,
    FactorManager,
    FactorCalculator,
    BacktestEngine,
    Strategy,
    EqualWeightStrategy,
    FactorStrategy,
    Portfolio,
    PerformanceMetrics,
    ReportGenerator,

    # 因子评价
    FactorEvaluator,
    prepare_factor_panel,
    prepare_returns_panel,

    # 因子中性化
    FactorNeutralizer,

    # Alpha因子库
    AlphaFactorCalculator,

    # 交易成本
    TransactionCostModel,
    get_average_cost_model,
    get_conservative_cost_model,

    # 仓位管理
    PositionManager,
    PositionMethod,
    get_simple_position_manager,
    get_institutional_position_manager,

    # Sprint 2: 回测引擎增强
    TradingConstraint,
    EnhancedPortfolio,
    EnhancedBacktestEngine,

    # Sprint 3: 高级策略
    MomentumStrategy,
    MeanReversionStrategy,
    PairTradingStrategy,
    EventDrivenStrategy,
    MomentumType,

    # Sprint 4: 数据扩展与Pipeline
    ExtendedDataManager,
    QuantResearchPipeline,

    # 组合优化
    PortfolioOptimizer,
    OptimizationMethod,
    compare_optimization_results,

    # 风险控制
    RiskController,
    get_conservative_risk_controller,

    # 扩展绩效指标
    ExtendedPerformanceMetrics,

    # 业绩归因
    BrinsonAttribution,
    calculate_brinson_attribution,
    calculate_factor_attribution,

    # 过拟合检测
    OverfittingDetector,
)


def generate_mock_price_data(stock_list: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
    """
    生成模拟价格数据（用于演示）

    Args:
        stock_list: 股票列表
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        Dict: ts_code -> DataFrame 格式的价格数据
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    n_days = len(dates)

    data_dict = {}
    np.random.seed(42)

    for i, ts_code in enumerate(stock_list):
        # 生成具有不同特性的价格序列
        base_price = 10 + np.random.rand() * 40
        drift = np.random.uniform(-0.0005, 0.0015)
        vol = np.random.uniform(0.015, 0.03)

        # 生成对数收益率
        log_returns = np.random.normal(drift, vol, n_days)
        price_path = base_price * np.exp(np.cumsum(log_returns))

        # 生成OHLC数据
        high = price_path * (1 + np.random.uniform(0, 0.02, n_days))
        low = price_path * (1 - np.random.uniform(0, 0.02, n_days))
        open_price = np.concatenate([[base_price], price_path[:-1]])
        close = price_path
        volume = np.random.randint(100000, 10000000, n_days)

        df = pd.DataFrame({
            'trade_date': dates.strftime('%Y%m%d'),
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'amount': close * volume * 0.1
        })

        data_dict[ts_code] = df

    return data_dict


def demo_sprint2_enhanced_backtest():
    """演示 Sprint 2: 增强回测引擎"""
    print("\n" + "="*80)
    print("🚀 Sprint 2: 增强回测引擎演示".center(80))
    print("="*80)

    # 1. 创建数据管理器
    print("\n1️⃣  准备数据...")
    data_manager = DataManager()
    stock_list = [f"{i:06d}.SZ" if i % 2 == 0 else f"{i:06d}.SH" for i in range(1, 31)]

    # 生成模拟数据并注入到数据管理器
    mock_data = generate_mock_price_data(
        stock_list,
        start_date='2024-01-01',
        end_date='2024-12-31'
    )

    # 临时替换数据管理器的获取方法（演示用）
    data_manager._cache = {'factor_data_20240101_20241231': mock_data}
    original_prepare = data_manager.prepare_factor_data

    def mock_prepare(stock_list, start_date, end_date):
        return mock_data

    data_manager.prepare_factor_data = mock_prepare

    print(f"   股票数量: {len(stock_list)}")
    print(f"   时间范围: 2024-01-01 至 2024-12-31")

    # 2. 创建交易约束
    print("\n2️⃣  配置交易约束（T+1、涨跌停、停牌）...")
    trading_constraint = TradingConstraint()
    print("   ✅ T+1交易规则: 已启用")
    print("   ✅ 涨跌停限制: 可配置")
    print("   ✅ 停牌处理: 已启用")

    # 3. 创建交易成本模型
    print("\n3️⃣  创建交易成本模型...")
    cost_model = get_average_cost_model()
    print(f"   佣金费率: {cost_model.commission_rate:.2%}")
    print(f"   滑点模型: {type(cost_model.slippage_model).__name__}")
    print(f"   冲击成本: 已启用")

    # 4. 创建仓位管理器
    print("\n4️⃣  创建仓位管理器...")
    position_manager = PositionManager(
        total_capital=1000000.0,
        max_single_position=0.1,
        max_industry_position=0.3,
        min_position_weight=0.01,
        lot_size=100
    )
    print(f"   单股最大仓位: {position_manager.max_single_position:.0%}")
    print(f"   单行业最大仓位: {position_manager.max_industry_position:.0%}")
    print(f"   最小持仓权重: {position_manager.min_position_weight:.0%}")
    print(f"   一手股数: {position_manager.lot_size}股")

    # 5. 创建策略
    print("\n5️⃣  创建动量策略...")
    strategy = MomentumStrategy(
        name='A股动量策略',
        momentum_type='cross_sectional',
        lookback_period=20,
        hold_period=5,
        top_n=10
    )
    print(f"   策略名称: {strategy.name}")
    print(f"   动量类型: 横截面动量")
    print(f"   回看周期: {strategy.lookback_period}天")
    print(f"   持仓周期: {strategy.hold_period}天")
    print(f"   选股数量: {strategy.top_n}只")

    # 6. 创建增强回测引擎
    print("\n6️⃣  创建增强回测引擎...")
    engine = EnhancedBacktestEngine(
        data_manager=data_manager,
        initial_capital=1000000.0,
        start_date='2024-01-01',
        end_date='2024-12-31',
        cost_model=cost_model,
        position_manager=position_manager
    )
    engine.set_strategy(strategy)
    print("   ✅ 增强回测引擎创建完成")

    # 7. 运行回测（演示模式 - 跳过实际回测，展示功能）
    print("\n7️⃣  运行增强回测...")
    print("   📊 增强回测引擎功能:")
    print("      - 集成交易成本模型（佣金/印花税/滑点/冲击成本）")
    print("      - 集成仓位管理器（等权重/风险预算/仓位限制）")
    print("      - 支持过滤ST股票、科创板、北交所")
    print("      - 支持过滤停牌股票")
    print("      - T+1交易规则处理")
    print("      - 涨跌停价格限制")
    print("   ⚠️  实际回测需要完整的数据支持")

    print("\n   ✅ Sprint 2 演示完成!")


def demo_sprint3_advanced_strategies():
    """演示 Sprint 3: 高级策略"""
    print("\n" + "="*80)
    print("📈 Sprint 3: 高级策略演示".center(80))
    print("="*80)

    # 1. 动量策略详解
    print("\n1️⃣  动量策略族详解:")
    print("\n   📊 横截面动量:")
    cs_mom = MomentumStrategy(
        name='横截面动量',
        momentum_type='cross_sectional',
        lookback_period=20,
        hold_period=5,
        top_n=10
    )
    print(f"      - 每个调仓日选择过去{cs_mom.lookback_period}天收益率最高的{cs_mom.top_n}只股票")
    print(f"      - 适合: 趋势较强的市场，板块轮动明显")

    print("\n   📈 时序动量:")
    ts_mom = MomentumStrategy(
        name='时序动量',
        momentum_type='time_series',
        lookback_period=20,
        hold_period=5
    )
    print(f"      - 单股票自身过去{ts_mom.lookback_period}天收益率为正则持有")
    print(f"      - 适合: 个股趋势持续性强的市场")

    print("\n   🔄 复合动量:")
    comp_mom = MomentumStrategy(
        name='复合动量',
        momentum_type='composite',
        lookback_period=20,
        hold_period=5,
        top_n=10
    )
    print(f"      - 结合横截面和时序动量信号")
    print(f"      - 适合: 需要更稳健动量信号的场景")

    # 2. 均值回归策略
    print("\n2️⃣  均值回归策略详解:")
    print("\n   🎯 布林带策略:")
    bb_rev = MeanReversionStrategy(
        name='布林带均值回归',
        strategy_type='bollinger',
        bollinger_period=20,
        bollinger_std=2.0
    )
    print(f"      - 价格跌破下轨（{bb_rev.bollinger_std}σ）时买入")
    print(f"      - 价格回归中轨时卖出")
    print(f"      - 适合: 震荡市，波动率适中的股票")

    print("\n   📊 RSI策略:")
    rsi_rev = MeanReversionStrategy(
        name='RSI超买超卖',
        strategy_type='rsi',
        rsi_period=14,
        rsi_oversold=30,
        rsi_overbought=70
    )
    print(f"      - RSI < {rsi_rev.rsi_oversold}（超卖）时买入")
    print(f"      - RSI > {rsi_rev.rsi_overbought}（超买）时卖出")
    print(f"      - 适合: 有明显均值回归特性的股票")

    print("\n   🔄 反转因子策略:")
    rev_rev = MeanReversionStrategy(
        name='短期反转',
        strategy_type='reversal',
        reversal_period=5,
        top_n=10
    )
    print(f"      - 选择过去{rev_rev.reversal_period}天收益率最低的{rev_rev.top_n}只股票")
    print(f"      - 适合: 存在短期反转效应的市场")

    # 3. 配对交易策略
    print("\n3️⃣  配对交易策略详解:")
    print("\n   💹 配对交易原理:")
    print("      - 选择历史价格高度相关的两只股票")
    print("      - 当价差偏离均衡水平时进行套利")
    print("      - 做多相对低估的，做空相对高估的")
    print("      - 价差回归均衡时平仓获利")

    print("\n   🔧 关键参数:")
    print("      - 协整检验: 确认长期均衡关系")
    print("      - 价差标准差: 确定开平仓阈值")
    print("      - 止损阈值: 控制配对关系破裂的风险")

    # 4. 事件驱动策略框架
    print("\n4️⃣  事件驱动策略框架:")
    print("\n   📋 支持的事件类型:")
    print("      - 财报超预期: 业绩预告/正式财报超出市场预期")
    print("      - 股东增减持: 重要股东的增持/减持行为")
    print("      - 指数成分调整: 指数纳入/剔除个股")
    print("      - 分析师评级调整: 分析师上调/下调评级")
    print("      - 重大资产重组: 并购、重组等重大事件")

    print("\n   🎯 策略逻辑:")
    print("      - 事件发生前: 预判布局（如预期财报超预期）")
    print("      - 事件发生时: 快速响应（如指数调整日）")
    print("      - 事件发生后: 持有至效应消退（如分析师上调后持有5天）")

    print("\n   ⚠️  注意事项:")
    print("      - 需要高质量的事件数据源")
    print("      - 注意事件的事前泄露和事后过度反应")
    print("      - 需要严格的风控措施")

    print("\n   ✅ Sprint 3 演示完成!")


def demo_sprint4_data_extended():
    """演示 Sprint 4: 数据扩展与Pipeline"""
    print("\n" + "="*80)
    print("📊 Sprint 4: 数据扩展与Pipeline演示".center(80))
    print("="*80)

    # 1. 创建扩展数据管理器
    print("\n1️⃣  创建扩展数据管理器...")
    ext_data_manager = ExtendedDataManager()
    print("   ✅ 扩展数据管理器创建完成")

    # 2. 行业分类
    print("\n2️⃣  获取行业分类（申万一级）...")
    stock_list = [f"{i:06d}.SZ" if i % 2 == 0 else f"{i:06d}.SH" for i in range(1, 21)]
    industry_class = ext_data_manager.get_industry_classification(stock_list)

    print(f"   股票数量: {len(industry_class)}")
    print(f"   行业分布:")
    industry_counts = industry_class.value_counts()
    for industry, count in industry_counts.head(5).items():
        print(f"      {industry}: {count}只")

    # 3. 指数成分股
    print("\n3️⃣  获取指数成分股...")
    hs300_components = ext_data_manager.get_index_components('000300.SH')
    zz500_components = ext_data_manager.get_index_components('000905.SH')
    zz1000_components = ext_data_manager.get_index_components('000852.SH')

    print(f"   沪深300: {len(hs300_components)}只成分股")
    print(f"   中证500: {len(zz500_components)}只成分股")
    print(f"   中证1000: {len(zz1000_components)}只成分股")

    # 4. 股票池筛选
    print("\n4️⃣  获取股票池（可筛选）...")
    stock_pool = ext_data_manager.get_stock_universe(
        exclude_st=True,
        exclude_star=True,
        exclude_suspended=True,
        index_filter='hs300'
    )
    print(f"   沪深300成分股（排除ST/科创板/北交所）: {len(stock_pool)}只")

    # 5. 财务指标
    print("\n5️⃣  获取财务指标...")
    financial_data = ext_data_manager.get_financial_indicators(stock_list[:5])
    print(f"   指标包含: PE, PB, ROE, EPS, 市值")
    print(f"   示例（前2只）:")
    for _, row in financial_data.head(2).iterrows():
        print(f"      {row['ts_code']}: PE={row['pe']:.1f}, PB={row['pb']:.1f}, ROE={row['roe']:.1f}%")

    # 6. 资金流向
    print("\n6️⃣  获取资金流向数据...")
    money_flow = ext_data_manager.get_money_flow(stock_list[:5])
    print(f"   指标包含: 大单净流入、超大单净流入、主力净流入")
    print(f"   示例（前2只）:")
    for _, row in money_flow.head(2).iterrows():
        print(f"      {row['ts_code']}: 主力净流入={row['net_inflow_main']:.0f}万元")

    # 7. 研究Pipeline
    print("\n7️⃣  创建量化研究Pipeline...")
    data_manager = DataManager()

    # 注入模拟数据
    mock_data = generate_mock_price_data(
        stock_list[:20],
        start_date='2024-01-01',
        end_date='2024-12-31'
    )

    def mock_prepare(stock_list, start_date, end_date):
        return mock_data

    data_manager.prepare_factor_data = mock_prepare

    pipeline = QuantResearchPipeline(
        data_manager=data_manager,
        extended_data_manager=ext_data_manager
    )
    print("   ✅ QuantResearchPipeline创建完成")

    print("\n   🔬 Pipeline功能:")
    print("      - run_factor_research(): 因子研究全流程")
    print("        数据获取 → 因子计算 → 因子评价 → 中性化 → 生成报告")
    print("      - run_strategy_backtest(): 策略回测全流程")
    print("        数据获取 → 策略回测 → 绩效分析 → 归因分析 → 过拟合检测")
    print("      - run_full_pipeline(): 完整Pipeline（从配置到最终报告）")

    print("\n   ✅ Sprint 4 演示完成!")


def demo_core_features():
    """演示核心模块功能（组合优化、风险控制等）"""
    print("\n" + "="*80)
    print("📊 核心模块快速演示".center(80))
    print("="*80)

    # 1. 组合优化快速演示
    print("\n1️⃣  组合优化...")
    np.random.seed(42)
    n_assets = 8
    n_days = 252

    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')
    returns = pd.DataFrame(
        np.random.normal(0.0005, 0.02, (n_days, n_assets)),
        index=dates,
        columns=[f'STOCK_{i:02d}' for i in range(n_assets)]
    )

    optimizer = PortfolioOptimizer(returns=returns, risk_free_rate=0.03)
    results = optimizer.optimize_all(min_weight=0.05, max_weight=0.3)
    comparison = compare_optimization_results(results)

    print(f"   已优化 {len(results)} 种组合")
    print(f"   最佳夏普比率: {comparison['sharpe_ratio'].max():.3f}")
    print(f"   最低波动率: {comparison['expected_volatility'].min():.2%}")

    # 2. 风险控制快速演示
    print("\n2️⃣  风险控制...")
    risk_controller = get_conservative_risk_controller()
    print(f"   最大回撤容忍度: {risk_controller.max_drawdown:.1%}")
    print(f"   单笔止损: {risk_controller.stop_loss_pct:.1%}")
    print(f"   目标波动率: {risk_controller.target_volatility:.1%}")

    # 3. 扩展绩效指标快速演示
    print("\n3️⃣  扩展绩效指标...")
    strategy_returns = pd.Series(
        np.random.normal(0.0005, 0.015, 500),
        index=pd.date_range(end=datetime.now(), periods=500, freq='D')
    )

    metrics_calc = ExtendedPerformanceMetrics(
        returns=strategy_returns,
        risk_free_rate=0.03
    )

    all_metrics = metrics_calc.calculate_all()
    print(f"   夏普比率: {all_metrics['sharpe_ratio']:.3f}")
    print(f"   Sortino比率: {all_metrics['sortino_ratio']:.3f}")
    print(f"   最大回撤: {all_metrics['max_drawdown']:.2%}")
    print(f"   历史VaR (95%): {all_metrics['var_historical_95']:.2%}")

    print("\n   ✅ 核心模块快速演示完成!")


def main():
    """主程序"""
    print("\n" + "="*80)
    print("🚀 个人量化系统 v4.0 - 完整演示（Sprint 2-4）".center(80))
    print("="*80)
    print(f"\n📅 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n" + "="*80)
    print("📋 功能清单".center(80))
    print("="*80)

    print("\n📦 Sprint 2: 回测引擎增强")
    print("   ✅ TradingConstraint - T+1交易规则、涨跌停限制、停牌处理")
    print("   ✅ EnhancedPortfolio - 集成交易成本和仓位管理")
    print("   ✅ EnhancedBacktestEngine - 增强版回测引擎")

    print("\n🎯 Sprint 3: 高级策略")
    print("   ✅ MomentumStrategy - 横截面/时序/复合动量")
    print("   ✅ MeanReversionStrategy - 布林带/RSI/反转因子")
    print("   ✅ PairTradingStrategy - 配对交易（协整检验）")
    print("   ✅ EventDrivenStrategy - 事件驱动策略框架")

    print("\n📊 Sprint 4: 数据扩展与Pipeline")
    print("   ✅ ExtendedDataManager - 行业分类、指数成分、资金流向")
    print("   ✅ QuantResearchPipeline - 因子研究Pipeline、策略回测Pipeline")

    print("\n🎛️  核心模块（v4.0早期实现）")
    print("   ✅ PortfolioOptimizer - 5种专业优化算法")
    print("   ✅ RiskController - 止损/回撤/波动率控制")
    print("   ✅ ExtendedPerformanceMetrics - 15+专业绩效指标")
    print("   ✅ BrinsonAttribution - Brinson和因子归因")
    print("   ✅ OverfittingDetector - 样本外/Walk Forward分析")

    try:
        # 核心模块快速演示
        demo_core_features()

        # Sprint 2: 增强回测引擎
        demo_sprint2_enhanced_backtest()

        # Sprint 3: 高级策略
        demo_sprint3_advanced_strategies()

        # Sprint 4: 数据扩展与Pipeline
        demo_sprint4_data_extended()

    except ImportError as e:
        print(f"\n⚠️  缺少依赖库: {e}")
        print("   请安装: pip install scipy numpy pandas")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("✨ v4.0 完整演示完成!".center(80))
    print("="*80)

    print("\n📚 系统架构总结:")
    print("   ┌─────────────────────────────────────────────────────────┐")
    print("   │  应用层: Pipeline, ReportGenerator, main_v4_full.py    │")
    print("   ├─────────────────────────────────────────────────────────┤")
    print("   │  策略层: MomentumStrategy, MeanReversionStrategy, ...  │")
    print("   ├─────────────────────────────────────────────────────────┤")
    print("   │  回测层: EnhancedBacktestEngine, TradingConstraint, ... │")
    print("   ├─────────────────────────────────────────────────────────┤")
    print("   │  因子层: FactorEvaluator, FactorNeutralizer, Alpha...  │")
    print("   ├─────────────────────────────────────────────────────────┤")
    print("   │  数据层: DataManager, ExtendedDataManager              │")
    print("   └─────────────────────────────────────────────────────────┘")

    print("\n🎯 核心特色:")
    print("   🇨🇳 A股本土化 - T+1规则、涨跌停、停牌、申万行业")
    print("   🔬 专业化 - IC/IR/分组回测、Brinson归因、过拟合检测")
    print("   🚀 完整度 - 从数据到策略到回测到报告的完整Pipeline")
    print("   📊 可扩展 - 模块化设计，易于添加新因子、新策略")

    print("\n📖 下一步:")
    print("   1. 运行 python main_v4.py 查看核心模块详细演示")
    print("   2. 运行 python show_system_features.py 查看系统功能概览")
    print("   3. 阅读 quant_system/ 下的源代码了解实现细节")
    print("   4. 参考 docs/superpowers/ 下的设计文档")


if __name__ == '__main__':
    main()
