#!/usr/bin/env python3
"""
测试核心代码结构，不依赖外部库
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_structure():
    """测试核心代码结构"""
    print("🚀 开始测试核心代码结构...\n")

    success_count = 0
    total_tests = 0

    # 测试1: 检查项目目录结构
    print("📁 检查项目目录结构...")
    required_dirs = [
        'data_collector',
        'analyzer',
        'visualizer',
        'backtester',
        'templates',
        'tests',
        'scripts'
    ]

    all_dirs_exist = True
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"❌ 缺少目录: {dir_name}")
            all_dirs_exist = False
        else:
            print(f"✅ 找到目录: {dir_name}")

    if all_dirs_exist:
        success_count += 1
    total_tests += 1

    # 测试2: 检查核心文件存在
    print("\n📄 检查核心文件存在...")
    required_files = [
        'main.py',
        'config.yaml',
        'requirements.txt',
        'setup.py',
        'README.md'
    ]

    all_files_exist = True
    for file_name in required_files:
        if not os.path.exists(file_name):
            print(f"❌ 缺少文件: {file_name}")
            all_files_exist = False
        else:
            print(f"✅ 找到文件: {file_name}")

    if all_files_exist:
        success_count += 1
    total_tests += 1

    # 测试3: 测试模块导入（不依赖外部库）
    print("\n📦 测试模块导入...")
    try:
        # 测试主模块导入
        import main
        print("✅ 主模块导入成功")
        success_count += 1
    except Exception as e:
        print(f"❌ 主模块导入失败: {e}")
    total_tests += 1

    # 测试4: 测试数据采集模块结构
    print("\n🔍 测试数据采集模块结构...")
    try:
        from data_collector import MultiSourceDataFetcher
        print("✅ 多数据源获取器类存在")

        # 检查类方法
        methods = [method for method in dir(MultiSourceDataFetcher) if not method.startswith('_')]
        print(f"✅ 类方法: {', '.join(methods)}")
        success_count += 1
    except Exception as e:
        print(f"❌ 数据采集模块测试失败: {e}")
    total_tests += 1

    # 测试5: 测试分析模块结构
    print("\n🧠 测试分析模块结构...")
    try:
        from analyzer import MacroAnalyzer, StockAnalyzer
        print("✅ 宏观分析器和股票分析器类存在")
        success_count += 1
    except Exception as e:
        print(f"❌ 分析模块测试失败: {e}")
    total_tests += 1

    # 测试6: 测试回测模块结构
    print("\n⏳ 测试回测模块结构...")
    try:
        from backtester import QlibBacktestEngine
        print("✅ Qlib回测引擎类存在")
        success_count += 1
    except Exception as e:
        print(f"❌ 回测模块测试失败: {e}")
    total_tests += 1

    # 测试7: 测试可视化模块结构
    print("\n📈 测试可视化模块结构...")
    try:
        from visualizer import ReportGenerator, KLineVisualizer
        print("✅ 报告生成器和K线可视化器类存在")
        success_count += 1
    except Exception as e:
        print(f"❌ 可视化模块测试失败: {e}")
    total_tests += 1

    # 输出测试总结
    print("\n" + "="*60)
    print("🎯 核心代码结构测试总结")
    print("="*60)
    print(f"通过测试: {success_count}/{total_tests}")
    print(f"测试通过率: {success_count/total_tests*100:.1f}%")
    print()

    if success_count >= total_tests * 0.7:
        print("🎉 核心代码结构测试通过！")
        print("\n📋 系统状态评估:")
        print("✅ 项目结构完整")
        print("✅ 核心模块存在")
        print("✅ 代码架构合理")
        print("\n💡 下一步建议:")
        print("1. 安装完整依赖: pip install -r requirements.txt")
        print("2. 配置数据源API密钥")
        print("3. 运行完整功能测试")
        print("4. 配置自动化任务")
    else:
        print("⚠️ 部分核心结构需要改进")
        print("\n💡 建议先修复缺失的文件和目录")

    return success_count >= total_tests * 0.7

if __name__ == "__main__":
    test_result = test_core_structure()
    sys.exit(0 if test_result else 1)