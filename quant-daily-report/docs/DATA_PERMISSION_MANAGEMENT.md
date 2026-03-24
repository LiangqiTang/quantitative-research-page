# 数据权限管理模块文档

## 🎯 功能概述

数据权限管理模块是A股量化交易系统的核心组件之一，负责：
- 多源数据获取与故障转移
- 数据源优先级管理
- 权限配置与验证
- 自动告警机制
- 数据质量验证

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据源配置    │───▶│   多源数据获取器│───▶│   数据质量验证器│
│  (config.yaml)  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                        │                        │
          ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   优先级管理    │    │   故障转移引擎  │    │   告警发送系统  │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 配置说明

### 数据源配置示例

```yaml
# 数据源配置
data_sources:
  akshare:
    enabled: true
    priority: 1
    # AKShare免费版，无需token
  tushare:
    enabled: true
    priority: 2
    token: ${TUSHARE_TOKEN}  # 环境变量替换
  baostock:
    enabled: true
    priority: 3
    # 免费的A股历史数据接口
```

### 配置参数说明

| 参数 | 类型 | 描述 |
|------|------|------|
| `enabled` | bool | 是否启用该数据源 |
| `priority` | int | 数据源优先级（数字越小优先级越高） |
| `token` | string | 数据源认证token（支持环境变量） |

### 环境变量配置

在系统中配置以下环境变量：

```bash
# Tushare配置
export TUSHARE_TOKEN="your_tushare_token_here"

# 告警配置
export ALERT_EMAIL="your_alert_email@example.com"
export SMTP_SERVER="smtp.example.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your_email@example.com"
export SMTP_PASSWORD="your_email_password"
```

## 🚀 使用指南

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

print("股票名称:", stock_data['name'])
print("数据源:", stock_data['source'])
print("K线数据行数:", len(stock_data['kline']))
```

### 异步使用

```python
import asyncio
from data_collector import MultiSourceFetcher

async def main():
    fetcher = MultiSourceFetcher()
    data = await fetcher.fetch_stock_data_async('000001')
    print(data['name'])

asyncio.run(main())
```

### 批量获取

```python
from data_collector import MultiSourceFetcher

fetcher = MultiSourceFetcher()
stock_symbols = ['000001', '600036', '600519']

# 同步批量获取
results = fetcher.fetch_multiple_stocks(stock_symbols)

# 异步批量获取
import asyncio
results = asyncio.run(fetcher.fetch_multiple_stocks_async(stock_symbols))
```

## 🛡️ 权限管理

### Tushare权限配置

1. 注册Tushare账号并获取token
2. 在config.yaml中配置Tushare
3. 或者通过环境变量设置TUSHARE_TOKEN
4. 系统会自动验证token有效性

### 数据源优先级策略

- 数字越小，优先级越高
- 系统会按优先级顺序尝试数据源
- 失败后自动切换到下一个数据源
- 成功获取数据后会缓存结果

## 📧 告警机制

### 告警触发条件

- 数据源连续失败3次及以上
- 所有数据源都无法获取数据
- 数据质量严重不合格

### 告警内容

告警邮件包含以下信息：
- 告警标题和时间
- 失败的数据源列表
- 受影响的股票代码
- 建议的解决方案

## 📊 数据质量验证

### 验证维度

1. **基本字段验证**：检查是否包含必要字段
2. **数据合理性验证**：检查价格、成交量等数据是否合理
3. **跨源一致性验证**：对比不同数据源的数据一致性

### 验证结果处理

- 验证通过：返回数据并缓存
- 验证不通过：记录日志并尝试下一个数据源
- 所有数据源失败：返回基础数据结构

## 🔧 故障排查

### 常见问题

#### Tushare数据获取失败

**可能原因**:
- Token无效或未配置
- Token权限不足
- 网络连接问题
- 股票代码格式不正确

**解决方案**:
```bash
# 检查Token配置
python -c "import tushare as ts; print(ts.pro_api('your_token'))"

# 测试API调用
python -c "import tushare as ts; pro = ts.pro_api('your_token'); print(pro.stock_basic(ts_code='000001.SZ'))"
```

#### 数据源切换异常

**可能原因**:
- 配置文件格式错误
- 优先级配置冲突
- 数据源状态检查失败

**解决方案**:
```python
from utils.config_utils import config_loader
config = config_loader.load_config()
print("数据源配置:", config.get('data_sources', {}))

from data_collector import MultiSourceFetcher
fetcher = MultiSourceFetcher(config=config)
print("优先级顺序:", fetcher._get_prioritized_providers())
```

## 📈 性能优化

### 缓存策略

- 本地缓存默认过期时间：24小时
- 可通过force_refresh参数强制刷新
- 缓存键：股票代码+数据源类型

### 并行优化

- 异步批量获取支持多线程并行
- 数据源尝试支持超时控制
- 数据验证支持并行验证

## 🚀 未来规划

- [ ] 支持更多数据源接口
- [ ] 实现动态优先级调整
- [ ] 增强数据质量评估算法
- [ ] 支持数据源负载均衡
- [ ] 实现实时数据流监控

## 📞 技术支持

如遇问题，请查看：
- 系统日志文件：quant_daily.log
- 配置文件：config.yaml
- 测试脚本：test_data_permission.py

---
**更新时间**: 2024-01-01
**版本**: v1.0.0
**维护团队**: 量化研究团队
