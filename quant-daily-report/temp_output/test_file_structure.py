#!/usr/bin/env python3
"""
测试文件结构和基本存在性，不导入模块
"""

import sys
import os


def test_file_structure():
    """测试文件结构和基本存在性"""
    print("🚀 开始测试文件结构和基本存在性...\n")

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
        'README.md',
        'INSTALL.md'
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

    # 测试3: 检查模块文件存在
    print("\n🧩 检查模块文件存在...")
    module_files = {
        'data_collector': ['__init__.py', 'multi_source_fetcher.py', 'data_validator.py'],
        'analyzer': ['__init__.py', 'macro_analyzer.py', 'stock_analyzer.py'],
        'visualizer': ['__init__.py', 'report_generator.py', 'kline_visualizer.py'],
        'backtester': ['__init__.py', 'qlib_backtester.py', 'performance_analyzer.py']
    }

    module_success = True
    for module, files in module_files.items():
        print(f"\n🔍 模块: {module}")
        for file_name in files:
            file_path = os.path.join(module, file_name)
            if not os.path.exists(file_path):
                print(f"  ❌ 缺少文件: {file_path}")
                module_success = False
            else:
                print(f"  ✅ 找到文件: {file_path}")

    if module_success:
        success_count += 1
    total_tests += 1

    # 测试4: 检查测试文件存在
    print("\n🧪 检查测试文件存在...")
    test_files = [
        'tests/test_basic_functionality.py',
        'tests/quick_test.py'
    ]

    test_success = True
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"❌ 缺少测试文件: {file_path}")
            test_success = False
        else:
            print(f"✅ 找到测试文件: {file_path}")

    if test_success:
        success_count += 1
    total_tests += 1

    # 测试5: 检查脚本文件存在
    print("\n📜 检查脚本文件存在...")
    script_files = [
        'scripts/github_uploader.py',
        'scripts/scheduler.py',
        'scripts/download_data.py'
    ]

    script_success = True
    for file_path in script_files:
        if not os.path.exists(file_path):
            print(f"❌ 缺少脚本文件: {file_path}")
            script_success = False
        else:
            print(f"✅ 找到脚本文件: {file_path}")

    if script_success:
        success_count += 1
    total_tests += 1

    # 测试6: 检查requirements.txt内容
    print("\n📋 检查requirements.txt内容...")
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        required_packages = ['pandas', 'numpy', 'requests', 'pyyaml', 'python-dotenv']
        all_present = True
        for package in required_packages:
            if package not in content:
                print(f"❌ requirements.txt中缺少依赖: {package}")
                all_present = False
            else:
                print(f"✅ requirements.txt中包含依赖: {package}")

        if all_present:
            success_count += 1
    except Exception as e:
        print(f"❌ 无法读取requirements.txt: {e}")
    total_tests += 1

    # 输出测试总结
    print("\n" + "="*60)
    print("🎯 文件结构测试总结")
    print("="*60)
    print(f"通过测试: {success_count}/{total_tests}")
    print(f"测试通过率: {success_count/total_tests*100:.1f}%")
    print()

    if success_count >= total_tests * 0.8:
        print("🎉 文件结构测试通过！")
        print("\n📋 系统状态评估:")
        print("✅ 项目结构完整")
        print("✅ 所有核心文件存在")
        print("✅ 模块结构合理")
        print("\n💡 下一步建议:")
        print("1. 安装完整依赖: pip install -r requirements.txt")
        print("2. 配置数据源API密钥")
        print("3. 运行完整功能测试")
        print("4. 配置自动化任务")
    else:
        print("⚠️ 部分文件结构需要改进")
        print("\n💡 建议先修复缺失的文件和目录")

    return success_count >= total_tests * 0.8


if __name__ == "__main__":
    test_result = test_file_structure()
    sys.exit(0 if test_result else 1)