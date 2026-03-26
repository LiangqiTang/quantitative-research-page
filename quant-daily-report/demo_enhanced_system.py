"""
个人量化系统 v3.0 - 增强版演示脚本

展示新增的专业模块：
1. 因子评价引擎（IC/IR/分组回测）
2. 因子中性化模块（市值/行业/Barra）
3. Alpha因子库（Alpha101风格）
4. 交易成本模型（佣金/滑点/冲击成本）
5. 仓位管理（等权重/风险预算）
"""
import sys
from pathlib import Path

# 添加项目路径
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 导入核心模块
from quant_system import DataManager

# 导入新增专业模块
from quant_system import (
    # 因子评价
    FactorEvaluator,
    ICMethod,
    prepare_factor_panel,
    prepare_returns_panel,

    # 因子中性化
    FactorNeutralizer,
    NeutralizationMethod,

    # Alpha因子库
    AlphaFactorCalculator,

    # 交易成本
    TransactionCostModel,
    PriceLimitHandler,
    SlippageModel,
    OrderDirection,
    get_average_cost_model,
    get_conservative_cost_model,
    get_aggressive_cost_model,

    # 仓位管理
    PositionManager,
    PositionMethod,
    get_simple_position_manager,
    get_institutional_position_manager
)


def demo_factor_evaluator():
    """演示因子评价引擎"""
    print("\n" + "="*80)
    print("📊 第一部分：因子评价引擎演示")
    print("="*80)

    # 1. 初始化数据管理器
    print("\n1. 初始化数据管理器...")
    data_manager = DataManager(cache_dir="quant_cache/demo")

    # 获取股票列表和数据
    stocks = data_manager.get_stock_list(count=10)
    stock_list = [s['ts_code'] for s in stocks]

    # 准备数据
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

    print(f"\n2. 准备因子数据 (时间范围: {start_date} ~ {end_date})...")
    data_dict = data_manager.prepare_factor_data(
        stock_list,
        start_date=start_date,
        end_date=end_date
    )

    if not data_dict:
        print("❌ 数据准备失败")
        return

    print(f"   成功加载 {len(data_dict)} 只股票数据")

    # 3. 计算简单因子
    print("\n3. 计算示例因子...")
    factor_dict = {}

    for ts_code, df in data_dict.items():
        # 计算几个简单因子用于演示
        factors = {}
        factors['roc_5'] = df['close'].pct_change(5)
        factors['roc_20'] = df['close'].pct_change(20)
        factors['volatility'] = df['close'].pct_change().rolling(20).std()
        factors['ma_diff'] = df['close'].rolling(5).mean() - df['close'].rolling(20).mean()

        factor_dict[ts_code] = pd.DataFrame(factors, index=df.index)

    # 4. 构建因子面板
    print("\n4. 构建因子面板数据...")

    # 准备因子面板
    dfs = []
    for ts_code, df in factor_dict.items():
        if 'trade_date' in data_dict[ts_code].columns:
            df = df.copy()
            df['date'] = pd.to_datetime(data_dict[ts_code]['trade_date'])
            df['ts_code'] = ts_code
            dfs.append(df)

    if dfs:
        factor_panel = pd.concat(dfs, axis=0)
        factor_panel = factor_panel.set_index(['date', 'ts_code'])
        print(f"   因子面板形状: {factor_panel.shape}")

        # 准备收益率面板
        returns_dfs = []
        for ts_code, df in data_dict.items():
            df = df.copy()
            df = df.sort_values('trade_date').reset_index(drop=True)
            df['future_return'] = df['close'].pct_change(5).shift(-5)
            df['date'] = pd.to_datetime(df['trade_date'])
            df['ts_code'] = ts_code
            returns_dfs.append(df)

        returns_panel = pd.concat(returns_dfs, axis=0)
        returns_panel = returns_panel.set_index(['date', 'ts_code'])
        returns_series = returns_panel['future_return'].dropna()
        print(f"   收益率面板形状: {returns_series.shape}")

        # 5. 初始化因子评价引擎
        print("\n5. 初始化因子评价引擎...")
        evaluator = FactorEvaluator(
            factor_data=factor_panel,
            returns_data=returns_series,
            group_count=5,
            forward_period=5
        )

        # 6. 评价单个因子
        print("\n6. 评价单个因子 (roc_5)...")
        result = evaluator.evaluate_factor('roc_5', run_decay=True)

        print(f"\n{'='*60}")
        print(f"📊 因子评价结果: {result.factor_name}")
        print(f"{'='*60}")
        print(f"  IC均值:    {result.ic_stats.mean:+.4f}")
        print(f"  IC标准差:  {result.ic_stats.std:.4f}")
        print(f"  IC_IR:     {result.ic_stats.ir:.4f}")
        print(f"  t统计量:   {result.ic_stats.t_stat:.4f}")
        print(f"  IC正值率:  {result.ic_stats.positive_rate:.2%}")
        print(f"  综合得分:   {result.overall_score:.2f}")

        # 7. 批量评价多个因子
        print("\n7. 批量评价多个因子...")
        factor_names = [col for col in factor_panel.columns if col in ['roc_5', 'roc_20', 'volatility', 'ma_diff']]
        eval_df = evaluator.evaluate_multiple_factors(factor_names)

        if not eval_df.empty:
            print("\n   因子评价汇总:")
            print(eval_df.to_string(index=False))


def demo_factor_neutralizer():
    """演示因子中性化模块"""
    print("\n" + "="*80)
    print("🔧 第二部分：因子中性化模块演示")
    print("="*80)

    # 初始化中性化器
    print("\n1. 初始化因子中性化器...")
    neutralizer = FactorNeutralizer()

    # 生成模拟数据
    print("\n2. 生成模拟因子和市值数据...")
    n_dates = 100
    n_stocks = 50

    dates = pd.date_range(start='2024-01-01', periods=n_dates, freq='D')
    stocks = [f'{i:06d}.SH' for i in range(1, n_stocks+1)]

    index = pd.MultiIndex.from_product([dates, stocks], names=['date', 'ts_code'])

    # 原始因子（与市值有正相关性）
    np.random.seed(42)
    market_cap = np.exp(np.random.normal(10, 1, len(index)))
    factor = 0.3 * np.log(market_cap) + np.random.normal(0, 1, len(index))

    factor_series = pd.Series(factor, index=index, name='raw_factor')
    market_cap_series = pd.Series(market_cap, index=index, name='market_cap')

    # 生成行业分类
    industries = ['金融', '消费', '科技', '医药', '周期'] * (n_stocks // 5 + 1)
    industries = industries[:n_stocks]
    industry_series = pd.Series(
        np.tile(industries, n_dates),
        index=index,
        name='industry'
    )

    print(f"   原始因子与市值相关性: {factor_series.corr(market_cap_series):.4f}")

    # 3. 市值中性化
    print("\n3. 市值中性化...")
    result = neutralizer.neutralize_by_market_cap(
        factor_series,
        market_cap_series,
        method=NeutralizationMethod.RESIDUAL,
        use_log=True
    )

    print(f"   中性化前相关性: {result.correlation_before:.4f}")
    print(f"   中性化后相关性: {result.correlation_after:.4f}")
    print(f"   回归R²: {result.r_squared:.4f}")

    # 4. 行业中性化
    print("\n4. 行业中性化...")
    result_ind = neutralizer.neutralize_by_industry(
        factor_series,
        industry_series,
        method=NeutralizationMethod.RESIDUAL
    )

    print(f"   行业中性化完成")

    # 5. 因子正交化
    print("\n5. 多因子正交化...")
    factor_df = pd.DataFrame({
        'factor1': factor_series,
        'factor2': factor_series + np.random.normal(0, 0.5, len(factor_series)),
        'factor3': -factor_series + np.random.normal(0, 0.5, len(factor_series))
    })

    orthogonal_df = neutralizer.orthogonalize_factors(
        factor_df,
        reference_factor='factor1'
    )

    print("   正交化后因子相关性矩阵:")
    print(orthogonal_df.corr().round(4))


def demo_alpha_factors():
    """演示Alpha因子库"""
    print("\n" + "="*80)
    print("🧬 第三部分：Alpha因子库演示")
    print("="*80)

    # 1. 初始化Alpha因子计算器
    print("\n1. 初始化Alpha因子计算器...")
    alpha_calc = AlphaFactorCalculator()

    print(f"\n   可用因子数量: {len(alpha_calc.get_available_factors())}")
    print(f"\n   因子类别:")

    # 按类别统计
    categories = {}
    for name in alpha_calc.get_available_factors():
        info = alpha_calc.get_factor_info(name)
        if info:
            cat = info.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(name)

    for cat, factors in categories.items():
        print(f"     {cat}: {len(factors)}个因子")

    # 2. 生成模拟数据
    print("\n2. 生成模拟价格数据...")
    np.random.seed(42)
    n_days = 200

    # 价格随机游走
    base_price = 50
    returns = np.random.normal(0.001, 0.02, n_days)
    close = base_price * (1 + returns).cumprod()

    # OHLC数据
    high = close * (1 + np.random.uniform(0, 0.02, n_days))
    low = close * (1 - np.random.uniform(0, 0.02, n_days))
    open_p = low + np.random.uniform(0, 1, n_days) * (high - low)
    volume = np.random.randint(1000000, 10000000, n_days)

    df = pd.DataFrame({
        'open': open_p,
        'high': high,
        'low': low,
        'close': close,
        'vol': volume
    }, index=pd.date_range(start='2024-01-01', periods=n_days, freq='D'))

    print(f"   数据形状: {df.shape}")

    # 3. 计算单个因子
    print("\n3. 计算单个Alpha因子...")

    test_factors = ['roc_5', 'roc_20', 'kdj_k', 'kdj_d', 'atr_14', 'cci_14', 'wr_14']

    for factor_name in test_factors[:5]:
        factor = alpha_calc.calculate_factor(df, factor_name)
        if factor is not None and not factor.isna().all():
            info = alpha_calc.get_factor_info(factor_name)
            print(f"     {factor_name}: {info.description if info else ''}")
            print(f"       有效值: {factor.count()}, 均值: {factor.mean():.4f}, 标准差: {factor.std():.4f}")

    # 4. 批量计算多个因子
    print("\n4. 批量计算多个因子...")
    results = alpha_calc.calculate_all_factors(df, factor_names=test_factors)
    print(f"   成功计算 {len(results)} 个因子")


def demo_transaction_cost():
    """演示交易成本模型"""
    print("\n" + "="*80)
    print("💰 第四部分：交易成本模型演示")
    print("="*80)

    # 1. 初始化不同成本模型
    print("\n1. 初始化交易成本模型...")

    avg_model = get_average_cost_model()
    cons_model = get_conservative_cost_model()
    agg_model = get_aggressive_cost_model()

    # 2. 计算单笔交易成本
    print("\n2. 计算单笔交易成本...")

    test_cases = [
        ('买入平安银行', '000001.SZ', 10000, 10.5, OrderDirection.BUY),
        ('卖出贵州茅台', '600519.SH', 100, 1800.0, OrderDirection.SELL),
        ('买入浦发银行', '600000.SH', 5000, 8.5, OrderDirection.BUY),
    ]

    print(f"\n   {'交易描述':<20} {'股票代码':<12} {'数量':>8} {'价格':>10} {'总成本':>12} {'成本占比':>10}")
    print("-" * 80)

    for desc, ts_code, quantity, price, direction in test_cases:
        cost = avg_model.calculate_cost(
            quantity=quantity,
            price=price,
            direction=direction,
            ts_code=ts_code
        )
        print(f"   {desc:<20} {ts_code:<12} {quantity:>8,} {price:>10.2f} {cost.total_cost:>12.2f} {cost.cost_ratio:>10.2%}")
        print(f"     明细: 佣金{cost.commission:.2f} + 印花税{cost.stamp_duty:.2f} + 过户费{cost.transfer_fee:.2f} + 滑点{cost.slippage_cost:.2f}")

    # 3. 比较不同成本模型
    print("\n3. 比较不同成本模型...")

    quantity = 10000
    price = 10.0
    ts_code = '600000.SH'

    print(f"\n   交易: 买入 {quantity:,} 股 {ts_code}, 单价 {price:.2f}")
    print(f"\n   {'模型':<15} {'佣金':>10} {'印花税':>10} {'过户费':>10} {'滑点':>10} {'总成本':>12} {'成本占比':>10}")
    print("-" * 95)

    models = [
        ('激进模型', agg_model),
        ('平均模型', avg_model),
        ('保守模型', cons_model),
    ]

    for name, model in models:
        cost = model.calculate_cost(quantity, price, OrderDirection.BUY, ts_code)
        print(f"   {name:<15} {cost.commission:>10.2f} {cost.stamp_duty:>10.2f} {cost.transfer_fee:>10.2f} "
              f"{cost.slippage_cost:>10.2f} {cost.total_cost:>12.2f} {cost.cost_ratio:>10.2%}")

    # 4. 涨跌停处理
    print("\n4. 涨跌停处理...")

    limit_handler = PriceLimitHandler(
        st_limit_rate=0.1,
        st_st_limit_rate=0.05
    )

    prev_close = 10.0
    limit_down, limit_up = limit_handler.calculate_limit_prices(prev_close)

    print(f"   前收盘价: {prev_close:.2f}")
    print(f"   跌停价: {limit_down:.2f}")
    print(f"   涨停价: {limit_up:.2f}")

    # 测试不同价格
    test_prices = [9.0, 9.5, 10.0, 10.5, 11.0]

    print(f"\n   {'当前价格':>10} {'交易方向':>10} {'可否交易':>10} {'原因':<20}")
    print("-" * 60)

    for price in test_prices:
        for direction in [OrderDirection.BUY, OrderDirection.SELL]:
            check = limit_handler.check_tradable(
                current_price=price,
                limit_down=limit_down,
                limit_up=limit_up,
                direction=direction,
                volume=1000000
            )
            dir_str = "买入" if direction == OrderDirection.BUY else "卖出"
            can_trade = "✅ 可以" if check.can_trade else "❌ 不可"
            print(f"   {price:>10.2f} {dir_str:>10} {can_trade:>10} {check.reason:<20}")


def demo_position_manager():
    """演示仓位管理模块"""
    print("\n" + "="*80)
    print("📦 第五部分：仓位管理模块演示")
    print("="*80)

    # 1. 初始化仓位管理器
    print("\n1. 初始化仓位管理器...")

    total_capital = 1000000.0

    simple_manager = get_simple_position_manager(total_capital)
    inst_manager = get_institutional_position_manager(total_capital)

    print(f"   总资金: {total_capital:,.2f}")

    # 2. 准备数据
    print("\n2. 准备目标股票和价格...")

    target_stocks = ['000001.SZ', '000002.SZ', '600000.SH', '600519.SH', '601318.SH',
                     '600036.SH', '000858.SZ', '002415.SZ', '601888.SH', '600887.SH']

    np.random.seed(42)
    prices = {
        stock: round(10 + np.random.uniform(0, 500), 2)
        for stock in target_stocks
    }

    # 给茅台定个高价
    prices['600519.SH'] = 1800.0

    print(f"   目标股票数量: {len(target_stocks)}")
    print(f"   股票价格: {prices}")

    # 3. 等权重分配
    print("\n3. 等权重分配...")

    allocation = simple_manager.calculate_equal_weight(
        target_stocks=target_stocks,
        prices=prices
    )

    print(f"\n   分配方法: {allocation.method.value}")
    print(f"   已用资金: {allocation.used_capital:,.2f}")
    print(f"   剩余资金: {allocation.remaining_capital:,.2f}")

    print(f"\n   {'股票代码':<12} {'目标权重':>10} {'目标数量':>10} {'价格':>10} {'市值':>12}")
    print("-" * 70)

    for target in allocation.targets:
        market_value = target.target_quantity * target.price
        print(f"   {target.ts_code:<12} {target.target_weight:>10.2%} {target.target_quantity:>10,} "
              f"{target.price:>10.2f} {market_value:>12,.2f}")

    # 4. 风险预算分配
    print("\n4. 风险预算分配...")

    # 模拟波动率
    volatilities = {stock: np.random.uniform(0.1, 0.4) for stock in target_stocks}

    allocation_rb = simple_manager.calculate_risk_budget(
        target_stocks=target_stocks,
        prices=prices,
        volatilities=volatilities
    )

    print(f"\n   分配方法: {allocation_rb.method.value}")
    print(f"   已用资金: {allocation_rb.used_capital:,.2f}")
    print(f"   剩余资金: {allocation_rb.remaining_capital:,.2f}")

    print(f"\n   {'股票代码':<12} {'波动率':>10} {'目标权重':>10} {'目标数量':>10} {'价格':>10}")
    print("-" * 75)

    for target in allocation_rb.targets:
        vol = volatilities.get(target.ts_code, 0)
        print(f"   {target.ts_code:<12} {vol:>10.2%} {target.target_weight:>10.2%} "
              f"{target.target_quantity:>10,} {target.price:>10.2f}")

    # 5. 生成交易清单
    print("\n5. 生成交易清单...")

    # 模拟当前持仓
    current_positions = {
        '000001.SZ': 5000,
        '600000.SH': 3000,
        '600519.SH': 50
    }

    trades = simple_manager.generate_trades(allocation, current_positions)

    print(f"\n   当前持仓: {current_positions}")
    print(f"\n   交易清单:")
    print(f"   {'股票代码':<12} {'方向':>6} {'数量':>10} {'原因':<10}")
    print("-" * 55)

    for trade in trades:
        dir_str = "买入" if trade['direction'] == 'buy' else "卖出"
        print(f"   {trade['ts_code']:<12} {dir_str:>6} {trade['quantity']:>10,} {trade['reason']:<10}")

    # 6. 计算换手率
    print("\n6. 计算换手率...")

    turnover = simple_manager.calculate_turnover(allocation, current_positions, prices)
    print(f"   换手率: {turnover:.2%}")


def main():
    """主函数 - 运行所有演示"""
    print("\n" + "="*80)
    print("🚀 个人量化系统 v3.0 - 增强版演示")
    print("="*80)
    print("\n本演示将展示以下新增专业模块：")
    print("  1. 因子评价引擎（IC/IR/分组回测）")
    print("  2. 因子中性化模块（市值/行业/Barra）")
    print("  3. Alpha因子库（Alpha101风格）")
    print("  4. 交易成本模型（佣金/滑点/冲击成本）")
    print("  5. 仓位管理（等权重/风险预算）")

    # 运行演示
    try:
        demo_factor_evaluator()
        demo_factor_neutralizer()
        demo_alpha_factors()
        demo_transaction_cost()
        demo_position_manager()
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("✅ 增强版演示完成！")
    print("="*80)
    print("\n使用提示：")
    print("  - 所有模块均已在 quant_system/__init__.py 中导出")
    print("  - 可以直接 from quant_system import FactorEvaluator 等使用")
    print("  - 详细API请参考各模块的文档字符串")


if __name__ == "__main__":
    main()
