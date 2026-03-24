# 项目清理计划

## 保留的核心量化系统

### 核心模块
- `quant_system/` - 完整的个人量化系统（v2.0.0）
- `main_quant_system.py` - 量化系统主程序入口

### 输出与缓存
- `quant_output/` - 量化系统输出目录
- `quant_cache/` - 数据缓存目录

### 配置与文档
- `config.yaml` - 配置文件（保留参考）
- `requirements.txt` - Python依赖
- `QUANT_SYSTEM_README.md` - 量化系统使用文档
- `QUANT_SYSTEM_DESIGN.md` - 量化系统设计文档
- `.gitignore` - Git忽略配置

---

## 待删除的旧系统文件

### 旧日报系统模块
- `analyzer/` - 旧的分析模块
- `api/` - 旧的API模块
- `backtester/` - 旧的回测模块（已被quant_system替代）
- `data_collector/` - 旧的数据采集模块
- `factor_mining/` - 旧的因子挖掘模块
- `scripts/` - 旧的脚本目录
- `templates/` - 旧的模板目录
- `utils/` - 旧的工具模块
- `visualizer/` - 旧的可视化模块

### 测试与示例
- `tests/` - 旧的测试文件
- `examples/` - 示例目录
- `docs/` - 旧文档目录
- `test_*.py` - 临时测试文件
- `demo_*.py` - 演示文件

### 旧输出与日志
- `output/` - 旧的输出目录
- `quant_daily.log` - 旧日志文件
- `firebase-debug.log` - Firebase调试日志

### 旧文档与配置
- `main.py` - 旧的日报系统主程序
- `FOLDER_STRUCTURE.md` - 旧的文件夹结构
- `IMPLEMENTATION_SUMMARY.md` - 旧的实现总结
- `INSTALL.md` - 旧安装文档
- `quick_start.md` - 旧快速入门
- `README.md` - 旧README（将用QUANT_SYSTEM_README.md替代）
- `setup.py` - 旧安装脚本
- `vercel.json` - Vercel配置
- `.env` - 环境变量（敏感信息）
- `.env.example` - 环境变量示例
- `.DS_Store` - macOS系统文件
- `cleanup_project.sh` - 旧清理脚本

---

## 最终项目结构

```
quant-daily-report/
├── quant_system/           # 核心量化系统
│   ├── __init__.py
│   ├── data_module.py
│   ├── factor_module.py
│   ├── backtest_module.py
│   └── report_module.py
├── quant_output/           # 输出目录
├── quant_cache/            # 缓存目录
├── main_quant_system.py    # 主程序
├── config.yaml             # 配置文件
├── requirements.txt        # 依赖
├── QUANT_SYSTEM_README.md # 使用文档
├── QUANT_SYSTEM_DESIGN.md # 设计文档
└── .gitignore             # Git配置
```
