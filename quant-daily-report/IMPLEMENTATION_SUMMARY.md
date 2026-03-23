# 任务6：数据权限管理模块实现总结

## 🎯 任务目标

实现数据权限管理模块，包括：
- ✅ 为需要token的数据源（如Tushare）添加配置指引
- ✅ 实现数据源优先级管理，自动切换可用数据源
- ✅ 添加数据缺失时的告警机制
- ✅ 完善多源数据获取器的故障转移逻辑

## 🏗️ 实现架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   config.yaml   │───▶│   ConfigLoader  │───▶│ MultiSourceFetcher│
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                        │                        │
          ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   优先级管理    │    │   故障转移引擎  │    │   AlertSender   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 创建的文件

### 1. 工具模块
- `utils/config_utils.py` - 配置加载器，支持环境变量替换
- `utils/alert_utils.py` - 告警发送器，支持邮件告警
- `utils/__init__.py` - 工具包初始化

### 2. 核心模块增强
- `data_collector/multi_source_fetcher.py` - 增强多源数据获取器
  - 添加配置加载和优先级管理
  - 实现自动故障转移逻辑
  - 集成告警机制

### 3. 文档和测试
- `docs/DATA_PERMISSION_MANAGEMENT.md` - 数据权限管理文档
- `test_data_permission.py` - 数据权限管理测试
- `examples/tushare_config_example.py` - Tushare配置示例

## 🚀 核心功能实现

### 1. 数据源优先级管理

```python
def _get_prioritized_providers(self) -> List[str]:
    """获取按优先级排序的数据源列表"""
    # 先过滤掉禁用的数据源
    enabled_providers = []
    data_sources = self.config.get('data_sources', {})

    for provider_name in self.data_providers:
        source_config = data_sources.get(provider_name, {})
        if source_config.get('enabled', True):
            enabled_providers.append(provider_name)

    # 按优先级排序
    enabled_providers.sort(key=lambda x: self.provider_priority.get(x, 999))

    return enabled_providers
```

### 2. 自动故障转移

```python
def fetch_stock_data(self, symbol: str, force_refresh: bool = False) -> Dict:
    # ... 缓存检查 ...

    # 获取按优先级排序的数据源列表
    prioritized_providers = self._get_prioritized_providers()

    # 依次尝试不同数据源
    failed_providers = []
    for provider_name in prioritized_providers:
        try:
            print(f"🔍 尝试从 {provider_name} 获取 {symbol} 数据...")
            provider_func = self.data_providers[provider_name]
            data = provider_func(symbol)

            # 数据质量验证
            if self._validate_data_quality(data, provider_name):
                print(f"✅ 从 {provider_name} 获取数据成功")
                self._save_to_cache(symbol, data)
                # 重置失败计数器
                self.failure_count[provider_name] = 0
                return data
            else:
                print(f"⚠️ {provider_name} 数据质量不通过")
                failed_providers.append(provider_name)

        except Exception as e:
            print(f"❌ 从 {provider_name} 获取数据失败: {e}")
            failed_providers.append(provider_name)
            # 更新失败计数器并检查是否需要告警
            self.failure_count[provider_name] = self.failure_count.get(provider_name, 0) + 1
            self._check_alert(provider_name, symbol)
            continue

    # 最终回退方案
    print(f"⚠️ 所有可用数据源({', '.join(failed_providers)})都失败，使用回退方案")
    self._send_alert(f"所有数据源获取 {symbol} 数据失败", f"失败数据源: {', '.join(failed_providers)}")
    return self._fallback_strategy(symbol)
```

### 3. 告警机制

```python
def _check_alert(self, provider_name: str, symbol: str):
    """检查是否需要发送告警"""
    failure_count = self.failure_count.get(provider_name, 0)
    if failure_count >= self.alert_threshold:
        self._send_alert(
            f"数据源 {provider_name} 连续失败{failure_count}次",
            f"股票代码: {symbol}\n建议检查数据源配置或权限"
        )

def _send_alert(self, title: str, content: str):
    """发送告警"""
    try:
        from utils.alert_utils import AlertSender
        alert_sender = AlertSender()
        alert_sender.send_alert(title, content)
        print(f"📧 已发送告警: {title}")
    except Exception as e:
        print(f"⚠️ 告警发送失败: {e}")
```

### 4. 环境变量替换

```python
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
```

## 📋 配置示例

```yaml
# 数据源配置
data_sources:
  akshare:
    enabled: true
    priority: 1
    # AKShare免费版，无需token
  tushare:
    enabled: false
    priority: 2
    token: ${TUSHARE_TOKEN}
  baostock:
    enabled: true
    priority: 3
    # 免费的A股历史数据接口
```

## 🎉 功能亮点

1. **配置驱动**: 所有数据源配置通过config.yaml管理
2. **环境变量支持**: 敏感信息通过环境变量传递，避免硬编码
3. **自动故障转移**: 按优先级自动切换数据源
4. **智能告警**: 连续失败时自动发送告警
5. **数据质量保证**: 多层数据质量验证
6. **优雅降级**: 所有数据源失败时提供基础数据结构

## 📖 使用指南

### 基本使用

```python
from data_collector import MultiSourceFetcher
from utils.config_utils import config_loader

# 加载配置
config = config_loader.load_config()

# 创建多源数据获取器
fetcher = MultiSourceFetcher(config=config)

# 获取股票数据
stock_data = fetcher.fetch_stock_data('000001')
```

### 启用告警

```yaml
# 在config.yaml中启用告警
automation:
  alert:
    enabled: true
    email: ${ALERT_EMAIL}
    smtp_server: ${SMTP_SERVER}
    smtp_port: ${SMTP_PORT}
    smtp_username: ${SMTP_USERNAME}
    smtp_password: ${SMTP_PASSWORD}
```

## 🔧 测试结果

✅ 配置加载和优先级管理功能正常
✅ 多源数据获取和故障转移功能正常
✅ 告警机制功能正常
✅ Tushare权限配置和验证功能正常
✅ 数据质量验证功能正常

## 📊 性能优化

- **减少冗余配置**: 集中管理数据源配置
- **并行获取**: 异步批量获取支持多线程
- **智能缓存**: 避免重复获取相同数据
- **优雅降级**: 保证系统稳定性

## 🚀 未来规划

- [ ] 支持更多数据源接口
- [ ] 实现动态优先级调整
- [ ] 增强数据质量评估算法
- [ ] 支持数据源负载均衡
- [ ] 实现实时数据流监控

---
**完成时间**: 2024-01-01
**版本**: v1.0.0
**维护团队**: 量化研究团队
