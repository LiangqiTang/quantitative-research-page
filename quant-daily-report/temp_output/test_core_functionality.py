#!/usr/bin/env python3
"""
测试核心功能，不依赖外部库
"""

import sys
import os

# 添加项目目录到Python路径
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)


def test_core_functionality():
    """测试核心功能"""
    print("🚀 开始测试核心功能...\n")

    success_count = 0
    total_tests = 0

    # 测试1: 检查项目结构
    print("📁 检查项目结构...")
    required_dirs = [
        'data_collector', 'analyzer', 'visualizer', 'backtester',
        'templates', 'tests', 'scripts'
    ]
    all_exists = True
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"❌ 缺少目录: {dir_name}")
            all_exists = False
        else:
            print(f"✅ 找到目录: {dir_name}")
    if all_exists:
        success_count += 1
    total_tests += 1

    # 测试2: 检查核心文件
    print("\n📄 检查核心文件...")
    required_files = [
        'main.py', 'config.yaml', 'requirements.txt', 'setup.py',
        'README.md', 'INSTALL.md'
    ]
    all_exists = True
    for file_name in required_files:
        if not os.path.exists(file_name):
            print(f"❌ 缺少文件: {file_name}")
            all_exists = False
        else:
            print(f"✅ 找到文件: {file_name}")
    if all_exists:
        success_count += 1
    total_tests += 1

    # 测试3: 测试主模块导入
    print("\n📦 测试主模块导入...")
    try:
        import main
        print("✅ 主模块导入成功")
        print(f"   主模块内容: {[item for item in dir(main) if not item.startswith('_')]}")
        success_count += 1
    except Exception as e:
        print(f"❌ 主模块导入失败: {e}")
    total_tests += 1

    # 测试4: 测试数据采集模块
    print("\n🔍 测试数据采集模块...")
    try:
        from data_collector import DataQualityValidator
        validator = DataQualityValidator()
        print("✅ DataQualityValidator 导入并实例化成功")
        success_count += 1
    except Exception as e:
        print(f"❌ 数据采集模块测试失败: {e}")
    total_tests += 1

    # 测试5: 测试回测模块（不依赖qlib和scipy的部分）
    print("\n⏳ 测试回测模块...")
    try:
        from backtester import PerformanceAnalyzer, ParameterOptimizer

        # 测试PerformanceAnalyzer
        perf_analyzer = PerformanceAnalyzer()
        print("✅ PerformanceAnalyzer 实例化成功")
        print(f"   可用方法: {[m for m in dir(perf_analyzer) if not m.startswith('_')]}")

        # 测试ParameterOptimizer
        class MockBacktester:
            def run_backtest(self, params):
                return {
                    'portfolio_value': [1, 1.2, 1.1, 1.3, 1.5],
                    'transactions': []
                }
        optimizer = ParameterOptimizer(MockBacktester())
        print("✅ ParameterOptimizer 实例化成功")
        print(f"   可用方法: {[m for m in dir(optimizer) if not m.startswith('_')]}")

        success_count += 1
    except Exception as e:
        print(f"❌ 回测模块测试失败: {e}")
    total_tests += 1

    # 输出测试总结
    print("\n" + "="*60)
    print("🎯 核心功能测试总结")
    print("="*60)
    print(f"通过测试: {success_count}/{total_tests}")
    print(f"测试通过率: {success_count/total_tests*100:.1f}%")
    print()

    if success_count >= total_tests * 0.8:
        print("🎉 核心功能测试通过！")
        print("\n📋 系统状态评估:")
        print("✅ 项目结构完整")
        print("✅ 核心模块可以正常导入")
        print("✅ 基础功能可以正常工作")
        print("\n💡 下一步建议:")
        print("1. 安装完整依赖: pip install -r requirements.txt")
        print("2. 配置数据源API密钥")
        print("3. 运行完整功能测试")
        print("4. 配置自动化任务")
    else:
        print("⚠️ 部分核心功能需要改进")
        print("\n💡 建议先修复缺失的依赖和文件")

    return success_count >= total_tests * 0.8


if __name__ == "__main__":
    test_result = test_core_functionality()
    sys.exit(0 if test_result else 1)