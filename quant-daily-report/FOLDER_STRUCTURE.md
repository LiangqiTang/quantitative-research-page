# 项目文件夹结构

## 📁 当前目录结构

```
📦 quant-daily-report
├── 📁 __pycache__/              # Python编译缓存
├── 📁 .github/                  # GitHub配置文件
├── 📁 .pytest_cache/            # pytest缓存
├── 📁 analyzer/                 # 分析模块
│   ├── __pycache__/
│   ├── base_analyzer.py
│   ├── macro_analyzer.py
│   ├── news_analyzer.py
│   ├── stock_analyzer.py
│   └── technical_analyzer.py
├── 📁 api/                      # API接口模块
│   └── __pycache__/
├── 📁 backtester/               # 回测模块
│   ├── __pycache__/
│   ├── base_backtester.py
│   ├── __init__.py
│   ├── qlib_backtester.py
│   ├── README.md
│   └── test_qlib_integration.py
├── 📁 data_collector/           # 数据采集模块
│   ├── __pycache__/
│   ├── base_collector.py
│   ├── data_validator.py
│   ├── macro_data_collector.py
│   ├── __init__.py
│   ├── multi_source_fetcher.py
│   ├── news_data_collector.py
│   └── stock_data_collector.py
├── 📁 docs/                     # 文档目录
│   └── DATA_PERMISSION_MANAGEMENT.md
├── 📁 examples/                 # 示例代码
│   └── tushare_config_example.py
├── 📁 factor_mining/            # 因子挖掘模块
│   ├── __pycache__/
│   ├── built_in_factor_miner.py
│   ├── factor_mining_engine.py
│   ├── __init__.py
│   └── rd_agent_factor_miner.py
├── 📁 output/                   # 输出目录
│   ├── __pycache__/
│   ├── backtest_report.txt
│   ├── factor_mining_report.md
│   ├── index.html
│   └── README.md
├── 📁 scripts/                  # 脚本目录
│   ├── __pycache__/
│   ├── github_uploader.py
│   └── README.md
├── 📁 templates/                # 模板目录
│   └── __pycache__/
├── 📁 tests/                    # 测试目录
│   ├── __pycache__/
│   └── test_data_validator.py
├── 📁 utils/                    # 工具模块
│   ├── __pycache__/
│   ├── alert_utils.py
│   ├── config_utils.py
│   └── __init__.py
├── 📁 visualizer/               # 可视化模块
│   ├── __pycache__/
│   ├── base_visualizer.py
│   ├── __init__.py
│   ├── kline_visualizer.py
│   └── report_generator.py
├── 📄 .DS_Store                # macOS系统文件
├── 📄 .env                     # 环境变量文件
├── 📄 .env.example             # 环境变量示例
├── 📄 .gitignore               # Git忽略配置
├── 📄 config.yaml              # 主配置文件
├── 📄 demo_factor_mining.py     # 因子挖掘演示
├── 📄 firebase-debug.log       # Firebase调试日志
├── 📄 IMPLEMENTATION_SUMMARY.md# 实现总结文档
├── 📄 INSTALL.md               # 安装说明
├── 📄 main.py                  # 主程序入口
├── 📄 quant_daily.log          # 系统日志文件
├── 📄 quick_start.md           # 快速开始指南
├── 📄 README.md                # 项目说明文档
├── 📄 requirements-dev.txt     # 开发依赖
├── 📄 requirements.txt         # 生产依赖
├── 📄 setup.py                 # 安装脚本
├── 📄 test_backtest_integration.py # 回测集成测试
├── 📄 test_data_permission.py  # 数据权限测试
├── 📄 test_factor_mining_integration.py # 因子挖掘集成测试
├── 📄 vercel.json              # Vercel配置
```

## 🧹 建议清理的文件

### 1. 临时和缓存文件
- `__pycache__/` - Python编译缓存（可删除，会自动重建）
- `.pytest_cache/` - pytest缓存（可删除）
- `firebase-debug.log` - Firebase调试日志（已过期）
- `quant_daily.log` - 系统日志文件（可归档清理）
- `output/` - 输出目录（可清空，会重新生成）

### 2. 测试文件
- `test_backtest_integration.py` - 回测集成测试（已完成，可保留在tests/目录）
- `test_factor_mining_integration.py` - 因子挖掘集成测试（已完成，可保留在tests/目录）

### 3. 其他可以清理的文件
- `.DS_Store` - macOS系统文件（Windows/Linux不需要）

## 🔧 清理命令

```bash
# 删除所有__pycache__目录
find . -type d -name "__pycache__" -exec rm -rf {} +

# 删除pytest缓存
rm -rf .pytest_cache/

# 清空output目录（保留目录结构）
find output/ -type f -delete

# 删除过期日志
rm -f firebase-debug.log

# 清理系统日志（保留最后1000行）
tail -1000 quant_daily.log > quant_daily.log.tmp && mv quant_daily.log.tmp quant_daily.log

# 删除macOS系统文件
rm -f .DS_Store
```

## 📁 建议优化的目录结构

### 优化后的结构

```
📦 quant-daily-report
├── 📁 docs/                     # 文档目录
├── 📁 examples/                 # 示例代码
├── 📁 src/                      # 源代码目录
│   ├── analyzer/
│   ├── api/
│   ├── backtester/
│   ├── data_collector/
│   ├── factor_mining/
│   ├── scripts/
│   ├── utils/
│   └── visualizer/
├── 📁 tests/                    # 测试目录
├── 📁 output/                   # 输出目录
├── 📁 templates/                # 模板目录
├── 📄 .env                      # 环境变量
├── 📄 config.yaml               # 配置文件
├── 📄 main.py                   # 主程序
├── 📄 README.md                 # 项目说明
├── 📄 requirements.txt          # 依赖
└── 📄 setup.py                  # 安装脚本
```

### 优化命令

```bash
# 创建src目录
mkdir -p src

# 移动核心代码到src目录
mv analyzer/ api/ backtester/ data_collector/ factor_mining/ scripts/ utils/ visualizer/ src/

# 移动测试文件到tests目录
mv test_backtest_integration.py test_factor_mining_integration.py test_data_permission.py tests/

# 更新导入路径（需要同步修改代码中的import语句）
# 建议使用相对导入或修改Python路径
```

## 📋 文件类型分类

### 配置文件
- `config.yaml` - 主配置文件
- `.env` - 环境变量
- `.env.example` - 环境变量示例
- `vercel.json` - Vercel配置

### 依赖文件
- `requirements.txt` - 生产依赖
- `requirements-dev.txt` - 开发依赖
- `setup.py` - 安装脚本

### 文档文件
- `README.md` - 项目说明
- `INSTALL.md` - 安装说明
- `quick_start.md` - 快速开始
- `IMPLEMENTATION_SUMMARY.md` - 实现总结
- `docs/DATA_PERMISSION_MANAGEMENT.md` - 数据权限管理文档

### 核心代码
- `main.py` - 主程序入口
- `src/` - 所有核心源代码

### 测试代码
- `tests/` - 单元测试和集成测试
- `test_*.py` - 根目录的测试文件（建议移到tests/）

### 示例代码
- `demo_factor_mining.py` - 因子挖掘演示
- `examples/` - 示例代码目录

### 输出文件
- `output/` - 输出目录
- `quant_daily.log` - 系统日志

## 🎯 清理建议

### 立即清理
- 所有`__pycache__/`目录
- `.pytest_cache/`目录
- `firebase-debug.log`文件
- `.DS_Store`文件（如果在Windows/Linux）

### 定期清理
- `quant_daily.log`（每月清理或归档）
- `output/`目录（每周清理或归档）

### 结构优化
- 将所有核心代码移动到`src/`目录
- 将所有测试文件移动到`tests/`目录
- 更新导入路径，确保代码能正常运行

### 长期维护
- 建立.gitignore规则，排除不必要的文件
- 制定文档更新计划，保持文档与代码同步
- 定期清理日志和输出文件
