# 安装指南

## 📋 系统要求

- **Python**: 3.10 或更高版本
- **操作系统**: Linux/macOS/Windows
- **内存**: 至少4GB RAM (建议8GB+)
- **存储**: 至少10GB可用空间

## 🚀 快速安装

### 方法一: 使用pip安装

```bash
# 安装稳定版本
pip install quant-daily-report

# 或安装开发版本
pip install git+https://github.com/your-username/quant-daily-report.git
```

### 方法二: 从源码安装

```bash
# 克隆仓库
git clone https://github.com/your-username/quant-daily-report.git
cd quant-daily-report

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 安装TA-Lib (如果安装失败，参考下面的手动安装方法)
pip install TA-Lib

# 安装包
pip install -e .
```

## ⚙️ 依赖安装说明

### 安装TA-Lib

TA-Lib是技术指标计算的核心依赖，在某些系统上可能需要手动安装：

#### Linux系统
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y build-essential wget
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..
pip install TA-Lib
```

#### macOS系统
```bash
# 使用Homebrew安装依赖
brew install ta-lib
pip install TA-Lib
```

#### Windows系统
1. 从TA-Lib官网下载预编译的二进制文件
2. 或者使用conda安装:
```bash
conda install -c conda-forge ta-lib
pip install TA-Lib
```

### 安装Qlib

Qlib是微软开源的量化回测框架，安装方法：

```bash
# 安装Qlib
pip install qlib==0.8.6

# 初始化Qlib数据
python -m qlib.init --reset
```

## 📦 数据准备

### A股数据下载

系统支持多种数据源，首次运行会自动下载所需数据：

```bash
# 运行数据下载脚本
python scripts/download_data.py
```

### 手动获取数据

如果自动下载失败，可以手动获取：

1. **Tushare数据**: 需要注册Tushare账号并获取token
2. **AKShare数据**: 免费开源数据接口
3. **Qlib数据**: 提供高质量的A股数据

## ⚙️ 配置设置

### 环境变量配置

```bash
# 复制示例配置文件
cp .env.example .env.local

# 编辑配置文件
vim .env.local
```

需要配置的主要环境变量：

```env
# Tushare配置
TUSHARE_TOKEN=your_tushare_token_here

# GitHub配置
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your_username/your_repo

# 其他配置
CRON_SECRET=your_cron_secret_here
```

### 系统配置

编辑 `config.yaml` 文件调整系统参数：

```yaml
# 数据源优先级
data_sources:
  - akshare
  - tushare
  - baostock

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
```

## ✅ 安装验证

### 基本功能验证

```bash
# 运行系统测试
python -m pytest tests/ -v

# 测试数据采集
python -c "from data_collector import MultiSourceDataFetcher; fetcher = MultiSourceDataFetcher(); data = fetcher.fetch_stock_data('000001'); print('数据获取成功:', data.get('symbol'))"

# 测试分析功能
python -c "from analyzer import StockAnalyzer; import pandas as pd; data = {'kline': pd.DataFrame(), 'financial': {}}; analyzer = StockAnalyzer(data); print('分析模块初始化成功')"
```

### Qlib回测验证

```bash
# 测试Qlib初始化
python -c "import qlib; qlib.init(); print('Qlib初始化成功')"

# 测试回测功能
python examples/backtest_example.py
```

### 完整系统测试

```bash
# 运行完整系统测试
python main.py --test
```

## 🚀 首次运行

### 手动运行系统

```bash
# 运行主程序
python main.py

# 或使用命令行工具
quant-daily
```

### 配置定时任务

```bash
# 配置每日定时任务
python scripts/setup_scheduler.py

# 或使用Vercel Cron Jobs
vercel deploy
```

## 📊 验证结果

运行成功后，你将在 `output` 目录中看到：

- `daily_report.md`: 每日量化报告（Markdown格式）
- `daily_report.html`: 每日量化报告（HTML格式）
- `charts/`: 生成的各种图表
- `logs/`: 系统日志文件

## 🐛 常见问题

### 1. TA-Lib安装失败

**解决方案**:
```bash
# 下载预编译版本
# Linux
wget https://anaconda.org/conda-forge/ta-lib/0.4.19/download/linux-64/ta-lib-0.4.19-hdbd6064_0.tar.bz2
tar -xvf ta-lib-0.4.19-hdbd6064_0.tar.bz2
sudo cp -r lib/ /usr/local/
sudo cp -r include/ /usr/local/

# macOS
brew install ta-lib
```

### 2. Qlib数据初始化失败

**解决方案**:
```bash
# 手动下载数据
python -m qlib.data.download.py_data --target_dir ~/.qlib/qlib_data/cn_data/small --region CN

# 重置Qlib
python -m qlib.init --reset
```

### 3. 数据源连接失败

**解决方案**:
- 检查网络连接
- 验证API token是否正确
- 检查数据源服务是否正常
- 尝试切换到其他数据源

### 4. 报告生成失败

**解决方案**:
- 检查依赖是否完整安装
- 验证数据是否正确加载
- 检查输出目录权限
- 查看日志文件定位问题

## 📞 技术支持

如果在安装过程中遇到问题，可以：

1. 查看 [问题排查指南](TROUBLESHOOTING.md)
2. 提交 [GitHub Issue](https://github.com/your-username/quant-daily-report/issues)
3. 查看项目文档和示例代码
4. 联系技术支持邮箱

## 🎉 安装完成

恭喜！你已成功安装A股量化日报系统。接下来可以：

- 查看 [使用指南](USAGE.md) 了解系统功能
- 运行 `python main.py` 生成第一份量化报告
- 配置定时任务实现全自动运行
- 自定义策略和报告模板

---

**下一章**: [使用指南](USAGE.md)