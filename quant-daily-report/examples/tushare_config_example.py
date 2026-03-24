#!/usr/bin/env python3
"""
Tushare配置示例
展示如何配置和使用Tushare数据源
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def show_config_example():
    """显示Tushare配置示例"""
    print("=" * 80)
    print("📋 Tushare配置示例")
    print("=" * 80)

    # 配置示例
    config_example = """
# 在config.yaml中添加以下配置:
data_sources:
  tushare:
    enabled: true
    priority: 2
    token: ${TUSHARE_TOKEN}  # 使用环境变量
"""

    print(config_example)

    # 环境变量设置示例
    print("=" * 80)
    print("🔧 环境变量设置示例")
    print("=" * 80)

    env_example = """
# Linux/macOS终端设置
export TUSHARE_TOKEN="your_tushare_token_here"

# Windows命令行设置
set TUSHARE_TOKEN="your_tushare_token_here"

# PowerShell设置
$env:TUSHARE_TOKEN="your_tushare_token_here"
"""

    print(env_example)

def verify_tushare_config():
    """验证Tushare配置"""
    print("\n" + "=" * 80)
    print("🔍 验证Tushare配置")
    print("=" * 80)

    try:
        # 检查Tushare是否已安装
        import tushare as ts
        print("✅ Tushare模块已安装")
    except ImportError:
        print("❌ Tushare模块未安装，请执行:")
        print("  pip install tushare")
        return False

    # 检查环境变量
    tushare_token = os.getenv('TUSHARE_TOKEN')
    if tushare_token:
        print("✅ Tushare token已从环境变量获取")

        # 尝试连接Tushare
        try:
            import tushare as ts
            pro = ts.pro_api(tushare_token)
            # 测试获取基础数据
            data = pro.stock_basic(ts_code='000001.SZ')
            if not data.empty:
                print("✅ Tushare连接成功，API调用正常")
                print(f"   测试股票: {data.iloc[0]['name']} ({data.iloc[0]['ts_code']})")
                return True
            else:
                print("❌ Tushare API调用返回空数据")
                return False
        except Exception as e:
            print(f"❌ Tushare连接失败: {e}")
            return False
    else:
        print("❌ TUSHARE_TOKEN环境变量未设置")
        return False

def show_usage_example():
    """显示Tushare使用示例"""
    print("\n" + "=" * 80)
    print("💡 Tushare使用示例")
    print("=" * 80)

    usage_example = """
from data_collector import MultiSourceFetcher
from utils.config_utils import config_loader

# 加载配置
config = config_loader.load_config()

# 创建多源数据获取器
fetcher = MultiSourceFetcher(config=config)

# 使用Tushare获取数据
stock_data = fetcher.fetch_stock_data('000001')

print("股票名称:", stock_data['name'])
print("数据源:", stock_data['source'])
print("市盈率:", stock_data['financial']['pe'])
print("行业:", stock_data['basic']['industry'])
"""

    print(usage_example)

if __name__ == "__main__":
    show_config_example()
    verify_tushare_config()
    show_usage_example()
