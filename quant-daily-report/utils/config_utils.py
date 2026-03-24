"""
配置工具模块
负责加载和管理系统配置
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = None
        self.config_path = config_path or 'config.yaml'

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            config_path = Path(self.config_path)
            if not config_path.exists():
                print(f"⚠️ 配置文件不存在: {self.config_path}")
                return self._get_default_config()

            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 环境变量替换
            config = self._replace_env_vars(config)

            self.config = config
            print("✅ 配置文件加载成功")
            return config

        except Exception as e:
            print(f"⚠️ 配置文件加载失败: {e}")
            return self._get_default_config()

    def _replace_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """替换配置中的环境变量"""
        def replace_value(value):
            if isinstance(value, str) and '${' in value and '}' in value:
                # 提取环境变量名
                var_name = value[2:-1]
                env_value = os.getenv(var_name, value)
                return env_value
            elif isinstance(value, dict):
                return {k: replace_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_value(item) for item in value]
            else:
                return value

        return replace_value(config)

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'data_sources': {
                'akshare': {
                    'enabled': True,
                    'priority': 1
                },
                'tushare': {
                    'enabled': False,
                    'priority': 2,
                    'token': ''
                },
                'baostock': {
                    'enabled': True,
                    'priority': 3
                }
            }
        }

    def get_data_source_config(self, source_name: str) -> Dict[str, Any]:
        """获取数据源配置"""
        if not self.config:
            self.load_config()

        return self.config.get('data_sources', {}).get(source_name, {})

    def get_enabled_data_sources(self) -> Dict[str, Dict[str, Any]]:
        """获取启用的数据源，按优先级排序"""
        if not self.config:
            self.load_config()

        data_sources = self.config.get('data_sources', {})
        enabled_sources = {}

        for name, config in data_sources.items():
            if config.get('enabled', True):
                enabled_sources[name] = config

        # 按优先级排序
        sorted_sources = dict(sorted(enabled_sources.items(),
                                    key=lambda x: x[1].get('priority', 999)))

        return sorted_sources

# 全局配置加载器
config_loader = ConfigLoader()
"""
ConfigLoader使用示例:

from utils.config_utils import config_loader

# 加载配置
config = config_loader.load_config()

# 获取启用的数据源（按优先级排序）
enabled_sources = config_loader.get_enabled_data_sources()

# 获取特定数据源配置
tushare_config = config_loader.get_data_source_config('tushare')
"""