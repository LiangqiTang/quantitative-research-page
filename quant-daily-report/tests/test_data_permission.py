"""
数据权限管理测试
测试多源数据获取器的权限管理、优先级切换和告警功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data_collector import MultiSourceFetcher
from utils.config_utils import config_loader

def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("📋 测试配置加载功能")
    print("=" * 60)

    # 加载配置
    config = config_loader.load_config()
    print(f"\n📊 配置内容:")
    print(f"  数据源配置: {list(config.get('data_sources', {}).keys())}")

    # 检查Tushare配置
    tushare_config = config.get('data_sources', {}).get('tushare', {})
    print(f"\n🔑 Tushare配置:")
    print(f"    启用状态: {tushare_config.get('enabled', False)}")
    print(f"    优先级: {tushare_config.get('priority', 999)}")
    print(f"    Token已配置: {'是' if tushare_config.get('token') else '否'}")

    return config

def test_priority_management():
    """测试数据源优先级管理"""
    print("\n" + "=" * 60)
    print("🎯 测试数据源优先级管理")
    print("=" * 60)

    # 创建多源数据获取器
    fetcher = MultiSourceFetcher()

    # 获取优先级排序的数据源
    prioritized_providers = fetcher._get_prioritized_providers()
    print(f"\n📋 按优先级排序的数据源:")
    for i, provider in enumerate(prioritized_providers, 1):
        priority = fetcher.provider_priority.get(provider, 999)
        print(f"    {i}. {provider} (优先级: {priority})")

def test_data_fetch_with_fallback():
    """测试数据获取和故障转移"""
    print("\n" + "=" * 60)
    print("🔄 测试数据获取和故障转移")
    print("=" * 60)

    # 创建多源数据获取器
    fetcher = MultiSourceFetcher()

    # 测试获取股票数据
    test_symbol = '000001'
    print(f"\n📡 开始获取股票 {test_symbol} 数据...")

    try:
        data = fetcher.fetch_stock_data(test_symbol, force_refresh=True)

        print(f"\n✅ 数据获取成功!")
        print(f"    数据源: {data.get('source', 'unknown')}")
        print(f"    股票名称: {data.get('name', test_symbol)}")
        print(f"    K线数据行数: {len(data.get('kline', []))}")
        print(f"    财务数据: {'有' if data.get('financial') else '无'}")
        print(f"    基本信息: {'有' if data.get('basic') else '无'}")

    except Exception as e:
        print(f"\n❌ 数据获取失败: {e}")

def test_tushare_permission():
    """测试Tushare权限配置"""
    print("\n" + "=" * 60)
    print("🔐 测试Tushare权限配置")
    print("=" * 60)

    # 检查Tushare是否启用
    config = config_loader.load_config()
    tushare_enabled = config.get('data_sources', {}).get('tushare', {}).get('enabled', False)

    if not tushare_enabled:
        print("\n⚠️ Tushare当前未启用，请在config.yaml中启用并配置token")
        print("  示例配置:")
        print("  tushare:")
        print("    enabled: true")
        print("    priority: 2")
        print("    token: 'your_tushare_token_here'")
        return

    # 创建多源数据获取器
    fetcher = MultiSourceFetcher(config=config)

    # 尝试使用Tushare获取数据
    test_symbol = '000001'
    print(f"\n📡 尝试使用Tushare获取股票 {test_symbol} 数据...")

    try:
        # 直接调用Tushare获取函数
        data = fetcher._get_tushare_data(test_symbol)
        print(f"\n✅ Tushare数据获取成功!")
        print(f"    股票名称: {data.get('name', test_symbol)}")
        print(f"    K线数据行数: {len(data.get('kline', []))}")
    except Exception as e:
        print(f"\n❌ Tushare数据获取失败: {e}")
        print("\n🔍 可能的原因:")
        print("    1. Tushare Token无效或未配置")
        print("    2. Tushare API权限不足")
        print("    3. 网络连接问题")
        print("    4. 股票代码格式不正确")

def test_alert_mechanism():
    """测试告警机制"""
    print("\n" + "=" * 60)
    print("📧 测试告警机制")
    print("=" * 60)

    # 创建测试用的获取器
    fetcher = MultiSourceFetcher()

    # 模拟连续失败
    print(f"\n🔄 模拟数据源连续失败...")
    for i in range(4):
        fetcher._check_alert('test_source', '000001')
        fetcher.failure_count['test_source'] = i + 1

    print(f"\n✅ 告警机制测试完成")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🔐 A股量化交易系统 - 数据权限管理测试")
    print("=" * 80)

    try:
        # 运行所有测试
        test_config = test_config_loading()
        test_priority_management()
        test_data_fetch_with_fallback()
        test_tushare_permission()
        test_alert_mechanism()

        print("\n" + "=" * 80)
        print("🎉 所有测试完成!")
        print("=" * 80)
        print("\n📖 使用说明:")
        print("  1. 在config.yaml中配置数据源优先级和权限")
        print("  2. 系统会自动按优先级尝试数据源")
        print("  3. 当数据源连续失败时会自动发送告警")
        print("  4. Tushare需要配置有效的token才能使用")

    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
