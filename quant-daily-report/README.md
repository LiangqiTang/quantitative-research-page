# 个人量化系统 v4.0

专业的量化交易分析系统 - 黑金科技风格

## 目录结构

```
quant-daily-report/
├── 01_data/                    # 数据获取相关
├── 02_factors/                 # 因子挖掘相关
├── 03_strategy/                # 策略构架相关
├── 04_backtest/                # 回测引擎相关
├── 05_analysis/                # 分析工具相关
├── 06_report/                  # 报告生成相关
├── 07_ui/                      # 可视化界面（Next.js + FastAPI）
│   ├── apps/
│   │   └── web/               # Next.js 前端应用
│   └── packages/
│       └── api/               # FastAPI 后端
├── 08_tests/                   # 系统功能测试
├── 09_docs/                    # 功能介绍和设计文档
├── 10_demos/                   # 演示脚本
└── quant_system/               # 共享核心包（原 quant_system）
```

## 功能特性

- **数据管理**: Tushare + Baostock 双重数据源
- **因子库**: 60+ 专业因子，包括 Alpha101 风格
- **回测引擎**: 事件驱动回测，支持交易成本和仓位管理
- **组合优化**: 最小方差、最大夏普、风险平价等 5 种优化方法
- **风险控制**: 止损止盈、回撤控制、波动率目标
- **业绩归因**: Brinson 归因、因子归因
- **过拟合检测**: 样本内外对比、Walk Forward 分析

## 快速开始

### 运行演示

```bash
cd 10_demos
python3 main_v4.py
```

### 启动后端 API

```bash
cd 07_ui/packages/api
pip install -r requirements.txt
python3 main.py
```

### 启动前端

```bash
cd 07_ui/apps/web
npm install
npm run dev
```

## 技术栈

- **前端**: Next.js 14, React, TypeScript, Tailwind CSS
- **后端**: FastAPI, Python
- **可视化**: Recharts, Plotly
- **核心引擎**: 自研量化系统

## 版本

v4.0.0
