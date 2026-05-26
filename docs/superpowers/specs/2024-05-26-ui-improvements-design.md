# 量化系统 UI 改进设计文档

**日期**: 2024-05-26
**版本**: v1.0
**设计目标**: 修复图表标签、统一涨跌颜色、添加日期选择器

---

## 1. 概述

本次改动包含三个主要功能：
1. 修正市场图表的横轴和纵轴标签
2. 统一整体风格为"红涨绿跌"（中国股市风格）
3. 添加日期选择器，实现全页面数据联动

---

## 2. 颜色系统设计

### 2.1 CSS 变量更新

在 `:root` 中添加语义化颜色变量：

```css
:root {
    /* 现有变量保持不变 */
    --neon-green: #00ff88;
    --neon-red: #ff3333;

    /* 新增：涨跌语义化变量 */
    --price-up: #ff3333;    /* 上涨 = 红色 */
    --price-down: #00ff88;  /* 下跌 = 绿色 */
    --glow-up: 0 0 20px rgba(255, 51, 51, 0.5);   /* 上涨光晕 */
    --glow-down: 0 0 20px rgba(0, 255, 136, 0.5); /* 下跌光晕 */
}
```

### 2.2 需要更新的元素

| 元素 | 原逻辑 | 新逻辑 |
|------|--------|--------|
| `.stat-value.positive` | 绿色 | 红色 (`--price-up`) |
| `.stat-value.negative` | 红色 | 绿色 (`--price-down`) |
| 市场图表颜色 | 根据市场类型 | 根据整体趋势涨跌 |
| 自选股涨跌 | 需检查 | 统一红涨绿跌 |

### 2.3 市场图表颜色逻辑

```javascript
// 检查趋势：终点值 vs 起点值
const isUpTrend = data[data.length - 1] > data[0];
color = isUpTrend ? '#ff3333' : '#00ff88';
bgColor = isUpTrend ? 'rgba(255, 51, 51, 0.1)' : 'rgba(0, 255, 136, 0.1)';
```

---

## 3. 日期选择器设计

### 3.1 位置

放置在 **仪表盘 page-header 区域**，在"⚔️ LAUNCH BATTLE"按钮左侧：

```
┌─────────────────────────────────────────────────────────────────┐
│ 🚀 MAIN CONTROL DECK        [📅 2024年5月26日 ▼]  [⚔️ LAUNCH BATTLE] │
│ System Status: Online • Mission: Active                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 HTML 结构

```html
<div class="header-actions">
    <div class="date-selector-container">
        <input type="date" id="datePicker" class="cyber-date-picker">
        <div class="date-display" id="dateDisplay">📅 2024年5月26日</div>
    </div>
    <button class="cyber-btn primary" onclick="navigateTo('backtest')" data-i18n="⚔️ LAUNCH BATTLE">
        ⚔️ LAUNCH BATTLE
    </button>
</div>
```

### 3.3 CSS 样式

```css
.date-selector-container {
    position: relative;
    display: inline-flex;
    align-items: center;
}

.cyber-date-picker {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
}

.date-display {
    padding: 8px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border-cyan);
    border-radius: 4px;
    color: var(--neon-cyan);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.3s;
}

.date-display:hover {
    box-shadow: var(--glow-cyan);
    border-color: var(--neon-cyan);
}
```

### 3.4 日期范围限制

```javascript
const today = new Date();
const oneYearAgo = new Date();
oneYearAgo.setFullYear(today.getFullYear() - 1);

datePicker.max = today.toISOString().split('T')[0];
datePicker.min = oneYearAgo.toISOString().split('T')[0];
```

---

## 4. 图表设计更新

### 4.1 横轴（X轴）

- **显示内容**: 真实日期，从 `currentDate` 往前推50个自然日
- **标签格式**:
  - 中文: "2024年1月15日"
  - 英文: "Jan 15, 2024"
- **显示密度**: 只在第0、25、49个点显示完整标签，其余为空，避免拥挤

### 4.2 纵轴（Y轴）

- **显示内容**: 指数数值
- **格式**: 保留1位小数（如 "105.3"）
- **基准值**: 从100开始模拟

### 4.3 数据生成逻辑

```javascript
function generateChartData(startDate, market, days = 50) {
    let val = 100;
    const drift = market === 'cn' ? -0.1 : (market === 'us' ? 0.2 : 0.05);
    const volatility = market === 'cn' ? 2.5 : (market === 'us' ? 1.5 : 2);

    const data = [];
    const labels = [];

    for (let i = days - 1; i >= 0; i--) {
        const d = new Date(startDate);
        d.setDate(d.getDate() - i);
        labels.push(d);

        val += (Math.random() - 0.5 + drift) * volatility;
        data.push(val);
    }

    return { data, labels };
}
```

### 4.4 日期格式化函数

```javascript
function formatDateForDisplay(date, lang) {
    const d = new Date(date);
    if (lang === 'zh') {
        return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
    } else {
        return d.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
}
```

---

## 5. 状态管理更新

### 5.1 AppState 新增字段

```javascript
const AppState = {
    // ... 现有字段 ...

    // 新增：当前选中的日期
    currentDate: new Date().toISOString().split('T')[0], // 'YYYY-MM-DD'

    // ... 其他字段 ...
};
```

### 5.2 localStorage 持久化

```javascript
// 在初始化时读取
const savedDate = localStorage.getItem('preferredDate');
if (savedDate) {
    AppState.currentDate = savedDate;
}

// 在设置日期时保存
function setDate(dateStr) {
    AppState.currentDate = dateStr;
    localStorage.setItem('preferredDate', dateStr);
    updateAllDataForDate(dateStr);
}
```

---

## 6. 数据联动设计

### 6.1 主联动函数

```javascript
function updateAllDataForDate(targetDate) {
    // 1. 更新日期显示
    updateDateDisplay(targetDate);

    // 2. 根据日期生成新的市场指数数据
    updateMarketIndicesForDate(targetDate);

    // 3. 更新自选股数据
    updateWatchlistForDate(targetDate);

    // 4. 重新初始化市场图表
    initMarketChart();

    // 5. 更新仪表盘统计数据
    updateDashboardStats();
}
```

### 6.2 需要联动更新的模块

| 模块 | 函数 | 说明 |
|------|------|------|
| 市场指数 | `renderMarketIndices()` | 更新指数数值和涨跌 |
| 自选股 | `renderWatchlist()` | 更新股票价格和涨跌幅 |
| 市场图表 | `initMarketChart()` | 重新生成图表数据 |
| 仪表盘 | `updateDashboardStats()` | 更新收益统计等 |

---

## 7. i18n 翻译补充

### 7.1 新增翻译条目

```javascript
const i18n = {
    en: {
        // ... 现有翻译 ...
        "Select Date": "Select Date",
        "Date": "Date",
        "Today": "Today",
        "Market Data": "Market Data"
    },
    zh: {
        // ... 现有翻译 ...
        "Select Date": "选择日期",
        "Date": "日期",
        "Today": "今天",
        "Market Data": "市场数据"
    }
}
```

### 7.2 日期选择器 data-i18n

```html
<div class="date-display" id="dateDisplay" data-i18n="Date">
    📅 2024年5月26日
</div>
```

---

## 8. 实现清单

### 8.1 CSS 修改
- [ ] 添加涨跌语义化颜色变量
- [ ] 更新 `.stat-value.positive` 样式
- [ ] 更新 `.stat-value.negative` 样式
- [ ] 添加日期选择器样式

### 8.2 HTML 修改
- [ ] 在 page-header 添加日期选择器 HTML
- [ ] 给相关元素添加 data-i18n 属性

### 8.3 JavaScript 修改
- [ ] 在 AppState 添加 `currentDate` 字段
- [ ] 添加日期格式化函数 `formatDateForDisplay()`
- [ ] 重写 `initMarketChart()` 支持真实日期
- [ ] 修改图表颜色逻辑为按趋势涨跌
- [ ] 添加 `setDate()` 函数
- [ ] 添加 `updateAllDataForDate()` 函数
- [ ] 添加 `updateMarketIndicesForDate()` 函数
- [ ] 添加 `updateWatchlistForDate()` 函数
- [ ] 在初始化时加载 localStorage 中的日期
- [ ] 更新 i18n 翻译对象

---

## 9. 测试清单

- [ ] 日期选择器能正常工作，范围限制在过去一年
- [ ] 切换日期后，市场指数数据更新
- [ ] 切换日期后，自选股数据更新
- [ ] 切换日期后，图表数据更新
- [ ] 图表横轴日期显示正确（中英文格式）
- [ ] 图表纵轴显示指数数值
- [ ] 上涨时图表为红色，下跌时为绿色
- [ ] 所有正收益显示红色，负收益显示绿色
- [ ] 语言切换时，日期格式同步切换
- [ ] 刷新页面后，记住上次选择的日期
