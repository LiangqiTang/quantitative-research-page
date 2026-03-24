#!/usr/bin/env python3
"""
测试因子挖掘功能集成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta

def test_factor_mining_import():
    """测试因子挖掘模块导入"""
    print("📦 测试因子挖掘模块导入...")
    try:
        from factor_mining import FactorMiningEngine, RDAgentFactorMiner, get_factor_miner
        print("✅ 因子挖掘模块导入成功")

        # 测试获取因子挖掘器
        miner = get_factor_miner('builtin')
        print(f"✅ 获取内置因子挖掘器成功: {type(miner).__name__}")

        return True
    except Exception as e:
        print(f"❌ 因子挖掘模块导入失败: {e}")
        return False

def test_factor_miner_initialization():
    """测试因子挖掘器初始化"""
    print("\n🔧 测试因子挖掘器初始化...")
    try:
        from factor_mining import FactorMiningEngine

        engine = FactorMiningEngine()
        print(f"✅ 因子挖掘引擎初始化成功")
        print(f"   可用的因子挖掘器: {engine.available_miners}")

        # 测试每个可用的挖掘器
        for miner_name in engine.available_miners:
            print(f"\n📊 测试{miner_name}挖掘器:")
            print(f"   ✅ {miner_name}挖掘器可用")

            # 检查是否有因子挖掘方法
            miner = engine.miners[miner_name]
            if hasattr(miner, 'mine_factors'):
                print(f"   ✅ {miner_name}有mine_factors方法")
            if hasattr(miner, 'validate_factors'):
                print(f"   ✅ {miner_name}有validate_factors方法")
            if hasattr(miner, 'backtest_factors'):
                print(f"   ✅ {miner_name}有backtest_factors方法")

        return True
    except Exception as e:
        print(f"❌ 因子挖掘器初始化失败: {e}")
        return False

def test_factor_mining_flow():
    """测试因子挖掘流程"""
    print("\n🔄 测试因子挖掘流程...")
    try:
        from factor_mining import FactorMiningEngine

        engine = FactorMiningEngine()

        # 模拟数据
        mock_data = {
            'price_data': None,
            'financial_data': None,
            'technical_data': None,
            'start_date': (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'symbols': ['000001', '600036', '600519', '002415', '300750']
        }

        print(f"📅 回测周期: {mock_data['start_date']} 至 {mock_data['end_date']}")
        print(f"📊 测试股票池: {mock_data['symbols']}")

        # 测试因子挖掘
        if engine.available_miners:
            miner_name = engine.available_miners[0]
            print(f"\n⏳ 使用{miner_name}进行因子挖掘...")

            factors = engine.mine_factors(
                mock_data,
                factor_types=['price', 'volume', 'momentum', 'volatility', 'trend'],
                max_factors=10
            )

            print(f"✅ 因子挖掘完成，共挖掘出{len(factors)}个因子")

            if factors:
                # 显示部分因子
                print("\n🧬 部分因子信息:")
                for i, factor in enumerate(factors[:5]):
                    factor_name = factor.get('name', f'因子{i+1}')
                    factor_type = factor.get('type', 'unknown')
                    quality_score = factor.get('quality_score', 0)

                    print(f"   {i+1}. {factor_name} ({factor_type})")
                    print(f"      质量得分: {quality_score:.2f}")

                    # 显示因子质量指标
                    if 'ic' in factor:
                        ic_value = factor['ic'].get('value', 0)
                        p_value = factor['ic'].get('p_value', 0)
                        significant = factor['ic'].get('significant', False)
                        print(f"      IC值: {ic_value:.4f} ({'显著' if significant else '不显著'})")

            return True
        else:
            print("⚠️ 没有可用的因子挖掘器")
            return False

    except Exception as e:
        print(f"❌ 因子挖掘流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_factor_validation_backtest():
    """测试因子验证和回测"""
    print("\n📊 测试因子验证和回测...")
    try:
        from factor_mining import FactorMiningEngine

        engine = FactorMiningEngine()

        # 模拟数据
        mock_data = {
            'start_date': (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'symbols': ['000001', '600036']
        }

        # 模拟因子列表
        mock_factors = [
            {
                'name': 'Momentum20',
                'type': 'momentum',
                'description': '20日动量因子',
                'ic': {'value': 0.25, 'p_value': 0.02, 'significant': True},
                'quality_score': 25.0
            },
            {
                'name': 'RSI14',
                'type': 'momentum',
                'description': '14日RSI因子',
                'ic': {'value': 0.18, 'p_value': 0.04, 'significant': True},
                'quality_score': 18.0
            },
            {
                'name': 'VolumeRatio',
                'type': 'volume',
                'description': '成交量比率因子',
                'ic': {'value': 0.12, 'p_value': 0.08, 'significant': False},
                'quality_score': 12.0
            }
        ]

        # 测试因子验证
        print("\n🔬 测试因子验证...")
        validated_factors = engine.validate_factors(mock_data, mock_factors)
        print(f"✅ 因子验证完成，共验证{len(validated_factors)}个因子")

        # 测试因子回测
        print("\n⏳ 测试因子回测...")
        backtest_result = engine.backtest_factors(mock_data, mock_factors)
        print(f"✅ 因子回测完成，获得{len(backtest_result)}组回测结果")

        # 显示回测结果
        if backtest_result:
            for miner_name, result in backtest_result.items():
                print(f"\n📈 {miner_name}回测结果:")
                if 'factor_performance' in result:
                    perf_count = len(result['factor_performance'])
                    print(f"   共回测{perf_count}个因子表现")
                    if perf_count > 0:
                        avg_return = result.get('summary', {}).get('avg_annual_return', 0)
                        print(f"   平均年化收益率: {avg_return:.2%}")
                        avg_sharpe = result.get('summary', {}).get('avg_sharpe_ratio', 0)
                        print(f"   平均夏普比率: {avg_sharpe:.2f}")

        return True

    except Exception as e:
        print(f"❌ 因子验证和回测测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_report_generation():
    """测试报告生成"""
    print("\n📝 测试报告生成...")
    try:
        from factor_mining import FactorMiningEngine

        engine = FactorMiningEngine()

        # 模拟一些因子挖掘结果
        engine.results = {
            'builtin': {
                'factors': [
                    {'name': 'Momentum20', 'type': 'momentum', 'description': '20日动量因子'},
                    {'name': 'RSI14', 'type': 'momentum', 'description': '14日RSI因子'},
                    {'name': 'VolumeRatio', 'type': 'volume', 'description': '成交量比率因子'}
                ],
                'miner_type': 'builtin',
                'timestamp': datetime.now(),
                'params': {'factor_types': ['price', 'volume', 'momentum']}
            }
        }

        # 生成报告
        report_path = engine.generate_report(output_dir='temp_output')
        print(f"✅ 报告生成成功")
        if report_path:
            print(f"   报告路径: {report_path}")

            # 读取并显示部分报告内容
            if os.path.exists(report_path):
                with open(report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print("\n📋 报告预览:")
                    print(content[:1000] + ("..." if len(content) > 1000 else ""))

        return True

    except Exception as e:
        print(f"❌ 报告生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_integration():
    """测试主程序集成"""
    print("\n🔗 测试主程序集成...")
    try:
        # 检查main.py是否包含因子挖掘代码
        main_path = os.path.join(os.path.dirname(__file__), 'main.py')
        if os.path.exists(main_path):
            with open(main_path, 'r', encoding='utf-8') as f:
                main_content = f.read()

            if 'factor_mining' in main_content:
                print("✅ 主程序已集成因子挖掘模块")

                # 检查关键部分
                if 'FactorMiningEngine' in main_content:
                    print("✅ 主程序中使用了FactorMiningEngine")
                if 'factor_miner' in main_content:
                    print("✅ 主程序中定义了factor_miner变量")
                if 'factor_mining_enabled' in main_content:
                    print("✅ 主程序中检查了factor_mining_enabled配置")
                if 'factor_result' in main_content:
                    print("✅ 主程序中保存了factor_result结果")
                if 'factor_result' in main_content and 'report_data' in main_content:
                    print("✅ 主程序中已将因子结果添加到报告数据")

                return True
            else:
                print("❌ 主程序未集成因子挖掘模块")
                return False
        else:
            print("❌ 未找到main.py文件")
            return False

    except Exception as e:
        print(f"❌ 主程序集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 A股量化日报系统 - 因子挖掘功能测试")
    print("=" * 60)

    # 创建临时目录
    os.makedirs('temp_output', exist_ok=True)

    test_results = []

    # 运行所有测试
    test_results.append(("因子挖掘模块导入", test_factor_mining_import()))
    test_results.append(("因子挖掘器初始化", test_factor_miner_initialization()))
    test_results.append(("因子挖掘流程", test_factor_mining_flow()))
    test_results.append(("因子验证和回测", test_factor_validation_backtest()))
    test_results.append(("报告生成", test_report_generation()))
    test_results.append(("主程序集成", test_main_integration()))

    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in test_results:
        if result:
            print(f"✅ {test_name}: 通过")
            passed += 1
        else:
            print(f"❌ {test_name}: 失败")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📈 测试统计: 通过{passed}/{len(test_results)}，失败{failed}/{len(test_results)}")

    if failed == 0:
        print("🎉 所有测试通过！因子挖掘功能已成功集成")
        print("\n📖 使用说明:")
        print("1. 确保config.yaml中factor_mining.enabled设置为true")
        print("2. 运行main.py即可自动执行因子挖掘")
        print("3. 因子挖掘结果将保存在output/factor_mining_report.md")
        print("4. 因子指标将显示在每日量化报告中")
        print("\n🛠️ 扩展说明:")
        print("- 如果要使用RD-Agent进行因子挖掘，请安装RD-Agent并设置rd_agent_miner_enabled: true")
        print("- 可以在config.yaml中配置要挖掘的因子类型")
        print("- 因子挖掘结果可用于策略开发和优化")
    else:
        print("⚠️ 部分测试失败，请检查错误信息并修复问题")

    return failed == 0

if __name__ == "__main__":
    success = main()

    # 清理临时文件
    import shutil
    if os.path.exists('temp_output'):
        shutil.rmtree('temp_output')

    sys.exit(0 if success else 1)