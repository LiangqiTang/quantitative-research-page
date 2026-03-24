# A股量化日报系统 - 快速开始指南

## 🚀 本地体验快速开始

### 1. 环境准备

#### 1.1 安装依赖
```bash
# 进入项目目录
cd quantitative-research-page/quant-daily-report

# 安装核心依赖
pip install -r requirements.txt

# （可选）安装Qlib回测框架（如需使用回测功能）
pip install qlib==0.8.6
```

#### 1.2 配置数据源
系统已默认配置为使用免费的AKShare数据源，无需额外配置。如需修改数据源配置，编辑 `config.yaml` 文件：

```yaml
# 数据源配置
# 已默认启用AKShare和Baostock，禁用Tushare
data_sources:
  akshare:
    enabled: true
    priority: 1
    # AKShare免费版，无需token
  tushare:
    enabled: false  # 禁用Tushare，使用免费的AKShare
    priority: 2
    token: ${TUSHARE_TOKEN}
  baostock:
    enabled: true
    priority: 3
```

#### 1.3 环境变量配置
复制并编辑环境变量模板文件：
```bash
cp .env.example .env
```

无需修改任何配置即可运行基础功能。如需使用高级功能（如邮件告警、GitHub部署等），再根据需求填写相应配置项。

### 2. 启动系统

#### 2.1 运行主程序
```bash
python main.py
```

#### 2.2 功能体验
程序启动后，您可以体验以下核心功能：

##### 🔍 数据采集
- 自动采集A股市场概览数据
- 获取板块热点和资金流向
- 采集个股基本面和技术面数据

##### 📊 量化分析
- 市场情绪指标计算
- 板块轮动分析
- 个股估值和财务指标分析
- 技术指标计算（MA、MACD、RSI、KDJ等）

##### 📈 可视化报告
- 生成专业K线图分析
- 绘制技术指标图表
- 生成完整的量化日报

### 3. 核心功能演示

#### 3.1 运行快速演示
```bash
python quick_demo.py
```

该演示程序将展示：
- 系统架构说明
- 数据源配置示例
- 量化分析能力展示
- 可视化报告输出

#### 3.2 手动执行数据更新
```bash
# 更新今日数据
python scripts/download_data.py daily

# 更新历史数据（示例：2024年1月1日至2024年1月31日）
python scripts/download_data.py history 2024-01-01 2024-01-31

# 下载个股历史数据（示例：贵州茅台 600519）
python scripts/download_data.py stock 600519 2024-01-01 2024-12-31

# 检查数据覆盖情况
python scripts/download_data.py check
```

### 4. 输出结果查看

#### 4.1 数据文件
采集的数据将保存在 `data/` 目录下：
- `data/daily/`: 每日更新的市场数据
- `data/history/`: 历史数据和个股数据

#### 4.2 可视化报告
生成的量化日报将保存在 `output/` 目录下：
- `output/daily_report_YYYY-MM-DD.html`: 交互式HTML报告
- `output/charts/`: 各类技术分析图表

### 5. 可选功能

#### 5.1 启用Qlib回测框架
如需使用回测功能，安装Qlib后，编辑 `config.yaml` 启用回测模块：

```yaml
# 回测配置
backtest:
  enabled: true
  initial_capital: 1000000
  commission: 0.0003
  slippage: 0.0001
  benchmark: 000001.SH
```

#### 5.2 添加其他数据源
如需使用其他数据源，可在 `data_collector/` 目录下添加新的数据源采集器。

### 6. 常见问题

#### Q: AKShare数据采集失败？
A: 请检查网络连接，或者尝试更新AKShare：
```bash
pip install --upgrade akshare
```

#### Q: 缺少依赖库？
A: 请确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

#### Q: 如何查看更详细的日志？
A: 日志文件保存在 `logs/` 目录下，可查看详细的运行日志和错误信息。

### 7. 下一步

体验完本地功能后，您可以：
1. 查看 `docs/` 目录下的详细文档
2. 根据需求自定义量化分析策略
3. 配置定时任务和GitHub Pages自动部署
4. 扩展更多数据源和分析功能

如有任何问题，请查看项目文档或提交Issue。祝您使用愉快！ 🎉