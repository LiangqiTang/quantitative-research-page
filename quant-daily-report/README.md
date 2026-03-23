# 📈 A股量化日报系统

一个全自动的A股量化分析与报告生成系统，基于Python构建，提供专业级的市场分析、股票研究和可视化报告。

## 🎯 核心特性

- **📊 多数据源集成**: 支持AKShare、Tushare、Baostock等多个A股数据源
- **🧠 量化分析引擎**: 内置宏观分析、基本面分析、技术面分析、筹码分析等多种分析模块
- **📈 专业可视化**: 生成专业K线图、技术指标图、资金流向图等金融图表
- **📝 自动化报告**: 自动生成HTML/Markdown格式的量化研报
- **🚀 定时任务**: 支持每日定时采集数据、生成报告并自动部署
- **☁️ 云端部署**: 自动上传报告到GitHub Pages，支持多设备访问

## 🏗️ 系统架构

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  数据采集模块    │───▶│  分析计算模块    │───▶│  可视化模块      │───▶│  自动化部署模块  │
└──────────────────┘    └──────────────────┘    └──────────────────┘    └──────────────────┘
         ▲                      ▲                      ▲                      ▲
         │                      │                      │                      │
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  A股数据源接口   │    │  量化策略引擎    │    │  研报生成引擎    │    │  GitHub集成      │
└──────────────────┘    └──────────────────┘    └──────────────────┘    └──────────────────┘
```

## 🛠️ 技术栈

### 核心依赖
- **数据处理**: Pandas, NumPy, Python-dateutil
- **A股数据**: AKShare, Tushare, Baostock
- **技术指标**: TA-Lib, Pandas-TA
- **可视化**: Mplfinance, Plotly, Jinja2
- **自动化**: APScheduler, PyGitHub, python-dotenv
- **日志监控**: Loguru, Sentry

### 开发工具
- **测试框架**: Pytest, pytest-cov, pytest-asyncio
- **代码质量**: Black, Flake8, Isort, Mypy
- **开发环境**: IPython, Jupyter, Pandas-profiling

## 🚀 快速开始

### 环境准备

1. **克隆项目**:
```bash
git clone <repository-url>
cd quant-daily-report
```

2. **创建虚拟环境**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. **安装依赖**:
```bash
pip install -r requirements.txt

# 开发环境依赖（可选）
pip install -r requirements-dev.txt
```

4. **配置环境变量**:
```bash
cp .env.example .env.local

# 编辑.env.local文件，填入必要的配置
vim .env.local
```

### 关键配置说明

- **TUSHARE_TOKEN**: Tushare API令牌（需要注册Tushare账号）
- **GITHUB_TOKEN**: GitHub个人访问令牌（用于自动部署报告）
- **GITHUB_REPO**: GitHub仓库名（格式: username/repository）

## 📦 模块说明

### 1. 数据采集模块 (data_collector)

#### 宏观数据采集器
```python
from data_collector import MacroDataCollector

collector = MacroDataCollector()
market_overview = collector.get_market_overview()  # 获取大盘概况
hot_sectors = collector.get_hot_sectors()          # 获取热点板块
```

#### 股票数据采集器
```python
from data_collector import StockDataCollector

collector = StockDataCollector()
kline_data = collector.get_stock_kline('000001')  # 获取K线数据
financial_data = collector.get_stock_financial('000001')  # 获取财务数据
```

#### 新闻数据采集器
```python
from data_collector import NewsDataCollector

collector = NewsDataCollector()
latest_news = collector.get_latest_news()  # 获取宏观新闻
stock_news = collector.get_stock_news('000001')  # 获取个股新闻
```

### 2. 量化分析模块 (analyzer)

#### 宏观分析引擎
```python
from analyzer import MacroAnalyzer

analyzer = MacroAnalyzer(market_data)
sentiment = analyzer.analyze_market_sentiment()  # 市场情绪分析
sector_rotation = analyzer.analyze_sector_rotation()  # 板块轮动分析
```

#### 股票分析引擎
```python
from analyzer import StockAnalyzer

analyzer = StockAnalyzer(stock_data)
funda_analysis = analyzer.analyze_fundamentals()  # 基本面分析
tech_analysis = analyzer.analyze_technical()  # 技术面分析
```

### 3. 可视化模块 (visualizer)

#### K线图绘制
```python
from visualizer import KLinePlotter

plotter = KLinePlotter(kline_data)
plotter.plot_kline_with_indicators('000001')  # 绘制带指标的K线图
plotter.save_plot('kline.png')  # 保存图表
```

#### 报告生成
```python
from visualizer import ReportGenerator

generator = ReportGenerator()
report_content = generator.generate_daily_report(analysis_results)  # 生成日报
generator.save_report(report_content, 'daily_report.md')  # 保存报告
```

### 4. 自动化部署模块 (scripts)

#### GitHub自动上传
```python
from scripts import GitHubUploader

uploader = GitHubUploader(github_token, repo_name)
uploader.upload_report('daily_report.html')  # 上传报告到GitHub Pages
```

#### 定时任务配置
```python
from scripts import TaskScheduler

scheduler = TaskScheduler()
scheduler.setup_daily_task('08:30')  # 设置每日8:30执行任务
```

## 📊 报告示例

### 宏观情绪仪表盘
| 指标 | 数值 | 状态 |
|------|------|------|
| 上涨家数占比 | 65.2% | 🟢 情绪高涨 |
| 市场赚钱效应 | 72.8% | 🟢 赚钱效应好 |
| 连板高度 | 5板 | 🚀 强势行情 |
| 成交额异动率 | +12.5% | 📈 放量上涨 |

### 个股分析报告
```
🐎 贵州茅台 (600519)
📋 基本信息
- 当前价: 1825.00元 • 涨跌幅: +2.56%
- 市盈率: 28.5x • 市净率: 13.2x • ROE: 26.8%
- 主力净流入: +1.25亿元 • 换手率: 0.32%

🎯 核心逻辑
- 高端白酒龙头，品牌壁垒深厚
- 业绩稳定增长，现金流充沛
- 机构重仓配置，长期价值凸显

📊 技术分析
- 🟢 股价突破MA5均线，短期趋势向上
- 📈 MACD金叉，多头行情确认
- 🎯 目标价: 1950元 • 止损价: 1750元
```

## ⚙️ 配置说明

### 主要配置文件

- `config.yaml`: 系统主配置文件，包含数据源、分析、可视化等配置
- `.env.local`: 环境变量配置文件，存储敏感信息
- `requirements.txt`: 生产环境依赖列表
- `requirements-dev.txt`: 开发环境依赖列表

### 配置项说明

```yaml
# 数据源优先级
priority: [akshare, tushare, baostock]

# 分析配置
analysis:
  market_sentiment: true
  sector_rotation: true
  stock_fundamentals: true
  technical_analysis: true

# 可视化配置
visualization:
  output_dir: output
  save_format: png
  dpi: 300

# 定时任务配置
scheduler:
  enabled: true
  time: '08:30'
  timezone: 'Asia/Shanghai'
```

## 📈 策略示例

### 均线交叉策略
```python
from strategies import MovingAverageCrossStrategy

# 初始化策略
strategy = MovingAverageCrossStrategy(
    short_window=5,
    long_window=20,
    stop_loss=0.05,
    take_profit=0.10
)

# 运行回测
backtest_result = strategy.run_backtest(kline_data)

# 输出结果
print(f"总收益率: {backtest_result.total_return:.2%}")
print(f"胜率: {backtest_result.win_rate:.2%}")
print(f"最大回撤: {backtest_result.max_drawdown:.2%}")
```

## 🤝 贡献指南

### 开发流程

1. Fork项目到自己的GitHub仓库
2. 克隆代码到本地开发环境
3. 创建功能分支：`git checkout -b feature/xxx`
4. 提交代码：`git commit -m 'Add some feature'`
5. 推送到远程分支：`git push origin feature/xxx`
6. 创建Pull Request

### 代码规范

- 遵循PEP 8代码规范
- 使用Black进行代码格式化
- 使用Flake8进行代码检查
- 为新功能添加单元测试

## 📝 更新日志

### v1.0.0 (2026-03-19)
- ✨ 实现多数据源集成（AKShare、Tushare、Baostock）
- ✨ 完成宏观分析、基本面分析、技术面分析模块
- ✨ 实现专业K线图绘制和量化报告生成
- ✨ 添加定时任务和自动部署功能
- ✨ 完成系统架构设计和基础框架搭建

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🤝 联系方式

如有问题或建议，请通过以下方式联系：

- 📧 邮箱: your-email@example.com
- 💬 微信: your-wechat-id
- 📦 Issues: [GitHub Issues](<repository-url>/issues)

---

**免责声明**: 本项目仅用于学习和研究目的，不构成任何投资建议。股市有风险，投资需谨慎。