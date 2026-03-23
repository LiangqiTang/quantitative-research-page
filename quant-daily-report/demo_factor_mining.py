#!/usr/bin/env python3
"""
因子挖掘模块使用示例
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from factor_mining import FactorMiningEngine
from datetime import datetime, timedelta

def demo_basic_usage():
    """基础使用示例"""
    print("=" * 60)
    print("🧬 因子挖掘模块基础使用示例")
    print("=" * 60)

    # 初始化因子挖掘引擎
    engine = FactorMiningEngine()
    print(f"\n📊 可用的因子挖掘器: {engine.available_miners}")

    # 准备模拟数据
    mock_data = {
        'price_data': None,
        'financial_data': None,
        'technical_data': None,
        'start_date': (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
        'end_date': datetime.now().strftime('%Y-%m-%d'),
        'symbols': ['000001', '600036', '600519', '002415', '300750']
    }

    print(f"\n📅 回测周期: {mock_data['start_date']} 至 {mock_data['end_date']}")
    print(f"📊 测试股票池: {mock_data['symbols']}")

    # 运行因子挖掘
    print("\n🔍 开始因子挖掘...")
    factors = engine.mine_factors(
        mock_data,
        factor_types=['price', 'momentum', 'volatility'],
        max_factors=10
    )

    print(f"\n🎉 因子挖掘完成，共挖掘出{len(factors)}个因子")

    # 显示因子信息
    if factors:
        print("\n🧬 因子质量排名:")
        print("| 排名 | 因子名称 | 因子类型 | 质量得分 | IC值 | 显著性 |")
        print("|------|----------|----------|----------|------|----------|")

        # 按质量得分排序
        sorted_factors = sorted(factors, key=lambda x: x.get('quality_score', 0), reverse=True)

        for i, factor in enumerate(sorted_factors[:10], 1):
            factor_name = factor.get('name', f'因子{i}')
            factor_type = factor.get('type', 'unknown')
            quality_score = factor.get('quality_score', 0)
            ic_value = factor.get('ic', {}).get('value', 0)
            significant = factor.get('ic', {}).get('significant', False)

            print(f"| {i:2d} | {factor_name} | {factor_type} | {quality_score:6.2f} | {ic_value:4.4f} | {'显著' if significant else '不显著'} |")

        # 保存优质因子
        top_factors = sorted_factors[:5]
        print(f"\n💎 已选出{len(top_factors)}个优质因子")

        # 验证因子
        print("\n📊 验证因子有效性...")
        validated_factors = engine.validate_factors(mock_data, top_factors)
        print(f"✅ 因子验证完成，共验证{len(validated_factors)}个因子")

        # 回测因子
        print("\n⏳ 回测因子表现...")
        backtest_result = engine.backtest_factors(mock_data, validated_factors)
        print(f"✅ 因子回测完成，获得{len(backtest_result)}组回测结果")

        # 生成报告
        print("\n📝 生成因子挖掘报告...")
        report_path = engine.generate_report()
        if report_path:
            print(f"💾 因子挖掘报告已保存到: {report_path}")

def demo_factor_types():
    """各种因子类型演示"""
    print("\n" + "=" * 60)
    print("🎨 各种因子类型演示")
    print("=" * 60)

    # 初始化因子挖掘引擎
    from factor_mining import get_factor_miner
    miner = get_factor_miner('builtin')

    print("\n📁 可用的因子类型:")
    for factor_type in miner.available_factor_types:
        print(f"   ▶️ {factor_type}")

    # 展示每种因子类型包含的因子
    print("\n📋 各类因子详细列表:")

    # 模拟数据
    mock_data = {
        'start_date': '2023-01-01',
        'end_date': '2024-01-01',
        'symbols': ['000001']
    }

    # 计算各类因子
    for factor_type in ['price', 'volume', 'momentum', 'volatility']:
        print(f"\n🧮 {factor_type}类因子:")

        # 使用模拟数据计算因子
        calculator = miner.factor_calculators[factor_type]
        factors = calculator(mock_data)

        for i, factor in enumerate(factors[:3], 1):
            factor_name = factor.get('name', f'因子{i}')
            description = factor.get('description', '无描述')
            print(f"   {i}. {factor_name}: {description}")

def demo_config_usage():
    """配置文件使用演示"""
    print("\n" + "=" * 60)
    print("⚙️ 配置文件使用演示")
    print("=" * 60)

    config_example = """
# 因子挖掘配置示例
factor_mining:
  enabled: true
  max_factors: 20
  min_significance: 0.05
  factor_types:
    - price       # 价格类因子（MA5, MA10, MA20等）
    - momentum    # 动量类因子（RSI, Momentum等）
    - volatility  # 波动率类因子（ATR, Volatility等）
    - volume      # 成交量类因子（VolumeRatio等）
    - trend       # 趋势类因子（MACD, Bollinger等）
  validation_enabled: true  # 启用因子验证
  backtest_enabled: true    # 启用因子回测
  built_in_miner_enabled: true  # 启用内置挖掘器
  rd_agent_miner_enabled: false # 禁用RD-Agent挖掘器
"""

    print(config_example)
    print("📖 配置说明:")
    print("  • enabled: 是否启用因子挖掘功能")
    print("  • max_factors: 最大输出因子数量")
    print("  • min_significance: 因子显著性阈值")
    print("  • factor_types: 要计算的因子类型列表")
    print("  • validation_enabled: 是否验证因子有效性")
    print("  • backtest_enabled: 是否回测因子表现")
    print("  • built_in_miner_enabled: 是否使用内置挖掘器")
    print("  • rd_agent_miner_enabled: 是否使用RD-Agent挖掘器")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🧬 A股量化交易系统 - 因子挖掘模块使用演示")
    print("=" * 80)

    try:
        # 运行各个演示
        demo_basic_usage()
        demo_factor_types()
        demo_config_usage()

        print("\n" + "=" * 80)
        print("🎉 演示完成！因子挖掘模块已成功集成到系统中")
        print("=" * 80)
        print("\n📖 使用建议:")
        print("1. 先使用内置因子挖掘器熟悉系统")
        print("2. 安装RD-Agent以获得更强大的因子挖掘能力")
        print("3. 将优质因子应用到量化策略开发中")
        print("4. 定期更新因子库以适应市场变化")

    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️ 请确保所有依赖包已正确安装")
        print("   pip install pandas numpy scipy")