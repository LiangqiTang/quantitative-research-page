# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**个人量化系统 v4.0** - 专业的量化交易分析系统（黑金科技风格）

这是一个完整的A股量化研究平台，包含数据获取、因子挖掘、策略构建、回测引擎、绩效分析等完整功能。

## Repository Structure

```
quantitative-research-page/
├── index.html                          # GitHub Pages 展示页面
├── quant-daily-report/                 # 主项目目录
│   ├── data_modules/                   # 数据模块
│   │   ├── data_module.py             # 基础数据管理器
│   │   └── data_extended.py          # 扩展数据管理器
│   ├── factor_modules/                 # 因子模块
│   │   ├── factor_module.py           # 基础因子库（30+）
│   │   ├── alpha_factors.py          # Alpha101风格因子（60+）
│   │   ├── factor_evaluator.py       # 因子评价引擎
│   │   └── factor_neutralizer.py     # 因子中性化
│   ├── strategy_modules/               # 策略模块
│   │   ├── portfolio_optimizer.py    # 组合优化器
│   │   ├── risk_controller.py        # 风险控制器
│   │   └── advanced_strategies.py    # 高级策略
│   ├── backtest_modules/               # 回测模块
│   │   ├── backtest_module.py        # 事件驱动回测引擎
│   │   ├── transaction_cost.py       # 交易成本模型
│   │   └── position_manager.py       # 仓位管理
│   ├── analysis_modules/               # 分析模块
│   │   ├── metrics_extended.py       # 扩展绩效指标
│   │   ├── performance_attribution.py # 业绩归因
│   │   └── overfitting_detector.py   # 过拟合检测
│   ├── report_modules/                 # 报告模块
│   │   ├── report_module.py          # 报告生成
│   │   └── pipeline.py               # 研究Pipeline
│   └── quant_system/                   # 向后兼容层
│       └── __init__.py               # 重新导出所有模块
```

## Key Architecture Principles

### 1. 模块化设计
系统按功能划分为独立模块，每个模块有清晰的职责边界：
- **数据层** (`data_modules/`): 数据获取、缓存、标准化
- **因子层** (`factor_modules/`): 因子计算、评价、中性化
- **策略层** (`strategy_modules/`): 策略实现、组合优化、风险控制
- **回测层** (`backtest_modules/`): 事件驱动回测、交易成本、仓位管理
- **分析层** (`analysis_modules/`): 绩效指标、业绩归因、过拟合检测
- **报告层** (`report_modules/`): 可视化、报告生成、研究Pipeline

### 2. 向后兼容性
`quant_system/` 目录作为兼容层存在，从新模块目录重新导出所有内容：
```python
# 旧代码仍然可用
from quant_system import DataManager, BacktestEngine

# 新代码推荐使用
from data_modules import DataManager
from backtest_modules import BacktestEngine
```

### 3. 导入约定
- 优先使用 `from xxx_modules import ClassName` 格式
- 每个模块的 `__init__.py` 定义了公开API
- 避免直接导入模块内部的子文件

## Common Commands

### 运行测试和验证
```bash
# 检查模块兼容性
cd quant-daily-report
python test_compatibility.py

# 运行系统功能演示
python show_system_features.py

# 运行完整v4演示
python main_v4.py
```

### 开发工作流
```bash
# 安装依赖
pip install -r requirements.txt

# Git操作（在仓库根目录执行）
cd /Users/bytedance/quantitative-research-page
git status
git add .
git commit -m "message"
git push origin main
```

## Module Reference Guide

### 数据模块 (data_modules)
```python
from data_modules import DataManager, ExtendedDataManager

# DataManager: 基础数据管理（日线、财务、指数）
# ExtendedDataManager: 扩展数据（行业分类、指数成分、交易日历）
```

### 因子模块 (factor_modules)
```python
from factor_modules import (
    FactorManager,           # 基础因子计算
    AlphaFactorCalculator,   # Alpha101风格因子
    FactorEvaluator,         # IC/IR/分组回测
    FactorNeutralizer        # 市值/行业/Barra中性化
)
```

### 回测模块 (backtest_modules)
```python
from backtest_modules import (
    BacktestEngine,          # 基础回测引擎
    EnhancedBacktestEngine,  # 增强版（含交易成本和仓位管理）
    TransactionCostModel,    # 交易成本模型
    PositionManager          # 仓位管理
)
```

### 策略模块 (strategy_modules)
```python
from strategy_modules import (
    PortfolioOptimizer,      # 5种优化算法
    RiskController,          # 止损/回撤/波动率控制
    MomentumStrategy,        # 动量策略
    MeanReversionStrategy,   # 均值回归策略
    PairTradingStrategy      # 配对交易策略
)
```

### 分析模块 (analysis_modules)
```python
from analysis_modules import (
    ExtendedPerformanceMetrics,  # Sortino/Omega/Calmar/VaR/CVaR
    BrinsonAttribution,          # Brinson业绩归因
    FactorAttribution,           # 因子归因
    OverfittingDetector          # 过拟合检测
)
```

### 报告模块 (report_modules)
```python
from report_modules import (
    ReportGenerator,        # 报告生成
    QuantResearchPipeline   # 完整研究Pipeline
)
```

## Important Notes

### Git 工作目录
**注意**：Git 仓库在 `/Users/bytedance/quantitative-research-page/`，不在子目录中。所有 git 操作需要在根目录执行。

### GitHub Pages
- 根目录的 `index.html` 是 GitHub Pages 的入口页面
- 项目说明和展示在该页面中
- 提交到 main 分支后会自动部署

### 依赖管理
- `requirements.txt` 只包含核心依赖
- 注释掉的数据源依赖（tushare/baostock/akshare）是可选的
- 系统包含模拟数据，可以不依赖真实数据源运行

### 代码风格
- 遵循 PEP 8
- 使用类型提示
- 模块间通过公开 API 交互，避免耦合

## When Working on This Project

1. **修改模块时**：更新对应 `xxx_modules/__init__.py` 中的导出
2. **保持向后兼容**：更新 `quant_system/__init__.py` 以保持旧代码可用
3. **测试兼容性**：运行 `test_compatibility.py` 验证导入
4. **提交前**：在根目录执行 git 操作
