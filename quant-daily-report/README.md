# 个人量化系统 v2.0.0

## 概述

这是一个完整可用的个人量化交易系统，基于成熟量化框架（Qlib、Backtrader等）的设计经验构建。

## 系统架构

```
quant_system/
├── __init__.py          # 包初始化
├── data_module.py       # 数据管理模块
├── factor_module.py     # 因子计算模块（30+因子）
├── backtest_module.py   # 回测引擎模块
└── report_module.py     # 报告生成模块
```

## 核心功能

### 1. 数据层 (data_module.py)
- **多源数据支持**: Tushare + Baostock双源
- **智能缓存**: MD5哈希缓存，支持过期时间
- **数据类型**: 股票列表、日线行情、指数行情
- **模拟数据**: 真实数据不可用时生成高质量模拟数据

### 2. 因子层 (factor_module.py) - 30+因子库
- **价格类因子**: MA5/10/20/60, ROC5/10/20
- **动量类因子**: MOM5/10/20, RSI6/14/28
- **波动率类因子**: VOL10/20/60, ATR14/20, BBWIDTH
- **成交量类因子**: VOL_MA5/10, VOL_RATIO, OBV, AD
- **趋势类因子**: MACD_DIF/DEA/HIST, BOLL_UPPER/LOWER/MID

### 3. 回测层 (backtest_module.py) - 事件驱动引擎
- **策略基类**: Strategy基类，支持自定义策略
- **内置策略**: EqualWeightStrategy（等权重）、FactorStrategy（因子策略）
- **组合管理**: Portfolio类，完整持仓追踪
- **绩效指标**: 总收益率、年化收益率、波动率、夏普比率、最大回撤、卡尔马比率

### 4. 报告层 (report_module.py) - 可视化报告
- **Markdown报告**: 因子分析报告、回测分析报告
- **HTML报告**: 完整可视化综合报告
- **报告内容**: 因子排名、因子类型分布、策略绩效、风险分析等

## 快速开始

### 运行完整系统

```bash
# 使用conda Python（已安装所有依赖）
/opt/miniconda3/bin/python main_quant_system.py
```

### 手动使用各模块

```python
from quant_system import (
    DataManager,
    FactorManager,
    BacktestEngine,
    ReportGenerator
)

# 1. 初始化数据管理器
data_manager = DataManager(
    token="your_tushare_token",
    cache_dir="quant_cache"
)

# 2. 计算因子
factor_manager = FactorManager(data_manager)
factor_results = factor_manager.calculate_factors(stock_list)
factor_eval = factor_manager.evaluate_factors(factor_results)

# 3. 运行回测
backtester = BacktestEngine(
    data_manager=data_manager,
    initial_capital=1000000.0,
    start_date="20240101",
    end_date="20241231"
)
backtest_results = backtester.run(stock_list)

# 4. 生成报告
report_generator = ReportGenerator(output_dir="quant_output")
summary = report_generator.generate_summary_report(
    factor_eval, backtest_results, factor_results
)
```

## 输出文件

运行 `main_quant_system.py` 后会在 `quant_output/` 目录生成：

1. **factor_analysis_report.md** - 因子分析详细报告
2. **backtest_report.md** - 回测分析详细报告
3. **quant_report.html** - HTML可视化综合报告
4. **SUMMARY.md** - 综合总结

## 技术栈

- **数据处理**: Pandas, NumPy
- **数据源**: Tushare, Baostock
- **报告生成**: Markdown, HTML, Jinja2

## 注意事项

1. **Tushare Token**: 如需真实数据，请配置有效的Tushare token
2. **模拟数据**: Token无效时系统会自动生成高质量模拟数据
3. **缓存机制**: 数据默认缓存24小时，可手动删除 `quant_cache/` 刷新

## 系统特点

✅ **稳定可靠**: 多源数据 + 智能缓存 + 模拟数据兜底
✅ **完整功能**: 数据获取 → 因子计算 → 策略回测 → 报告生成
✅ **易扩展**: 模块化设计，支持自定义策略和因子
✅ **可视化**: 完整的Markdown和HTML报告
✅ **生产级**: 参考Qlib等成熟框架设计
