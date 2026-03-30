# 个人量化系统 - 配置信息清单

**最后更新**: 2026-03-24

---

## 📋 配置项总览

本量化系统需要以下配置项。请根据您的实际情况填写。

---

## 🔑 数据源配置

### 1. Tushare Token（推荐）
- **配置项**: `TUSHARE_TOKEN`
- **用途**: 获取A股市场数据（日线行情、财务数据等）
- **获取方式**:
  1. 访问 [Tushare官网](https://tushare.pro/)
  2. 注册账号并登录
  3. 在个人中心获取Token
- **配置位置**: `config.yaml` 或环境变量
- **当前状态**: ✅ 已配置（用户已提供）
- **示例值**: `d8d09d2910337867b1966484fe2bf8e8ab3c35536a8b46f97498dcb`

### 2. Baostock（免费，无需Token）
- **配置项**: 无需Token
- **用途**: A股历史数据接口（备用数据源）
- **获取方式**: 直接使用，免费开源
- **配置位置**: `config.yaml`
- **当前状态**: ✅ 已启用

### 3. AKShare（可选，免费）
- **配置项**: 无需Token
- **用途**: 额外的数据源选项
- **获取方式**: 直接使用，免费开源
- **配置位置**: `config.yaml`
- **当前状态**: ⏸️ 已禁用（默认）

---

## 🚀 GitHub Pages 部署配置

### 4. GitHub Personal Access Token
- **配置项**: `GITHUB_TOKEN`
- **用途**: 自动部署HTML报告到GitHub Pages
- **获取方式**:
  1. 登录GitHub
  2. 进入 Settings → Developer settings → Personal access tokens
  3. 生成新Token，勾选 `repo` 权限
- **配置位置**: 环境变量或 `.env` 文件
- **当前状态**: ⏸️ 待配置
- **权限要求**: `repo` (完整仓库访问权限)

### 5. GitHub 仓库名称
- **配置项**: `GITHUB_REPO`
- **用途**: 指定要部署到的GitHub仓库
- **格式**: `username/repository-name`
- **示例**: `your-username/quant-daily-report`
- **配置位置**: 环境变量或 `.env` 文件
- **当前状态**: ⏸️ 待配置

### 6. GitHub Pages 分支
- **配置项**: `branch` (在 `config.yaml` 中)
- **默认值**: `gh-pages`
- **用途**: 指定GitHub Pages部署的分支
- **当前状态**: ✅ 已配置默认值

---

## 📧 告警通知配置（可选）

### 7. 告警邮箱地址
- **配置项**: `ALERT_EMAIL`
- **用途**: 接收系统告警通知
- **示例**: `your-email@example.com`
- **配置位置**: 环境变量或 `.env` 文件
- **当前状态**: ⏸️ 待配置

### 8. SMTP 服务器地址
- **配置项**: `SMTP_SERVER`
- **用途**: 发送邮件的SMTP服务器
- **示例**: `smtp.gmail.com` (Gmail), `smtp.qq.com` (QQ邮箱)
- **配置位置**: 环境变量或 `.env` 文件
- **当前状态**: ⏸️ 待配置

### 9. SMTP 端口
- **配置项**: `SMTP_PORT`
- **用途**: SMTP服务器端口
- **常用值**:
  - `587` (TLS加密，推荐)
  - `465` (SSL加密)
  - `25` (不加密)
- **配置位置**: 环境变量或 `.env` 文件
- **当前状态**: ⏸️ 待配置

### 10. SMTP 用户名
- **配置项**: `SMTP_USERNAME`
- **用途**: SMTP认证用户名（通常是邮箱地址）
- **示例**: `your-email@gmail.com`
- **配置位置**: 环境变量或 `.env` 文件
- **当前状态**: ⏸️ 待配置

### 11. SMTP 密码/授权码
- **配置项**: `SMTP_PASSWORD`
- **用途**: SMTP认证密码或授权码
- **注意**: 部分邮箱（如Gmail、QQ邮箱）需要使用"授权码"而非登录密码
- **配置位置**: 环境变量或 `.env` 文件
- **当前状态**: ⏸️ 待配置

---

## 📊 监控配置（可选）

### 12. Sentry DSN
- **配置项**: `SENTRY_DSN`
- **用途**: 错误监控与性能追踪
- **获取方式**: 注册 [Sentry](https://sentry.io/) 账号并创建项目
- **配置位置**: 环境变量或 `.env` 文件
- **当前状态**: ⏸️ 待配置

---

## 💰 其他数据源（可选）

### 13. Wind 量化接口（可选）
- **配置项**: `WIND_USERNAME`, `WIND_PASSWORD`
- **用途**: Wind金融终端数据接口
- **说明**: 需要购买Wind金融终端
- **配置位置**: 环境变量或 `.env` 文件
- **当前状态**: ⏸️ 待配置（非必需）

---

## ⚙️ config.yaml 配置文件说明

当前 `config.yaml` 中的主要配置项：

```yaml
# 数据源配置
data_sources:
  tushare:
    enabled: true          # 是否启用Tushare
    priority: 1            # 优先级（数字越小优先级越高）
    token: "your_token"    # Tushare Token

  baostock:
    enabled: true          # 是否启用Baostock（免费）
    priority: 2

# 回测配置
backtest:
  enabled: true            # 是否启用回测
  initial_capital: 1000000 # 初始资金
  commission: 0.0003       # 手续费率
  slippage: 0.0001         # 滑点
  benchmark: 000001.SH     # 基准指数

# 因子挖掘配置
factor_mining:
  enabled: true            # 是否启用因子挖掘
  max_factors: 20          # 最大因子数量
  # ... 更多配置
```

---

## 📝 配置方式

### 方式1: 环境变量（推荐用于生产）

```bash
# 在终端中设置
export TUSHARE_TOKEN="your_token_here"
export GITHUB_TOKEN="your_github_token"
export GITHUB_REPO="username/repo"

# 或者写入 .env 文件
cat > .env << 'EOF'
TUSHARE_TOKEN=your_token_here
GITHUB_TOKEN=your_github_token
GITHUB_REPO=username/repo
EOF
```

### 方式2: 修改 config.yaml

直接编辑 `config.yaml` 文件，填入相应的配置值。

---

## ✅ 配置检查清单

在运行系统前，请确认：

- [ ] Tushare Token 已配置（必需）
- [ ] 了解数据缓存机制（`quant_cache/` 目录）
- [ ] 了解输出位置（`quant_output/` 目录）

**可选配置**：
- [ ] GitHub Token 已配置（如需自动部署）
- [ ] GitHub 仓库已配置（如需自动部署）
- [ ] 邮箱告警配置已完成（如需告警）
- [ ] Sentry 配置已完成（如需错误监控）

---

## 🆘 获取帮助

如遇到配置问题：
1. 查看 `README.md` 了解系统使用方法
2. 检查 `quant_output/` 目录下的运行日志
3. 确保所有依赖已安装：`pip install -r requirements.txt`

---

*个人量化系统 v2.0.0*
