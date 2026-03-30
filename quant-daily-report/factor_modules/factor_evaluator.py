"""
因子评价引擎 - 专业因子分析模块
包含IC/IR计算、分组回测、因子衰减分析、稳定性分析
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')


class ICMethod(Enum):
    """IC计算方法"""
    RANK = "rank"           # Spearman秩相关系数
    PEARSON = "pearson"     # Pearson线性相关系数


@dataclass
class ICStats:
    """IC统计结果"""
    mean: float             # IC均值
    std: float              # IC标准差
    ir: float               # 信息比率（IC均值/IC标准差）
    t_stat: float           # t统计量
    positive_rate: float    # IC为正的比例
    win_rate: float         # IC显著为正的比例
    ic_series: pd.Series    # IC时间序列


@dataclass
class LayeredBacktestResult:
    """分组回测结果"""
    group_returns: pd.DataFrame      # 每组的收益率序列
    group_cum_returns: pd.DataFrame  # 每组的累计收益率
    long_short_return: pd.Series      # 多空组合收益率
    turnover: pd.Series               # 每组换手率
    ic_series: pd.Series              # IC时间序列


@dataclass
class FactorDecayResult:
    """因子衰减结果"""
    decay_curve: pd.Series  # 因子衰减曲线（不同持有期的IC）
    half_life: int           # 半衰期（IC衰减到一半的天数）


@dataclass
class FactorEvaluationResult:
    """因子综合评价结果"""
    factor_name: str
    ic_stats: ICStats
    layered_result: Optional[LayeredBacktestResult] = None
    decay_result: Optional[FactorDecayResult] = None
    stability_score: float = 0.0
    overall_score: float = 0.0


class FactorEvaluator:
    """
    因子评价引擎

    核心功能：
    - IC（信息系数）计算：Rank IC、Pearson IC
    - IR（信息比率）计算：IC均值 / IC标准差
    - 分组回测：5分组/10分组，做多空组合
    - 因子衰减分析：IC随时间衰减曲线
    - 因子稳定性分析：不同市场环境下的表现
    """

    def __init__(self,
                 factor_data: pd.DataFrame,
                 returns_data: pd.DataFrame,
                 group_count: int = 5,
                 forward_period: int = 5):
        """
        初始化因子评价引擎

        Args:
            factor_data: 因子数据，MultiIndex [date, ts_code]，columns为因子名
            returns_data: 收益率数据，MultiIndex [date, ts_code]，value为未来N日收益率
            group_count: 分组数量（默认5分组）
            forward_period: 预测期（默认5个交易日）
        """
        self.factor_data = factor_data.sort_index()
        self.returns_data = returns_data.sort_index()
        self.group_count = group_count
        self.forward_period = forward_period

        # 对齐日期
        self._align_dates()
        print(f"✅ 因子评价引擎初始化完成")
        print(f"   时间范围: {self.factor_data.index.levels[0][0]} 至 {self.factor_data.index.levels[0][-1]}")
        print(f"   股票数量: {len(self.factor_data.index.levels[1])}")
        print(f"   分组数量: {group_count}")

    def _align_dates(self):
        """对齐因子数据和收益率数据的日期"""
        factor_dates = self.factor_data.index.get_level_values('date').unique()
        return_dates = self.returns_data.index.get_level_values('date').unique()

        # 取交集
        common_dates = factor_dates.intersection(return_dates)

        if len(common_dates) == 0:
            raise ValueError("因子数据和收益率数据没有共同的日期！")

        self.factor_data = self.factor_data.loc[common_dates]
        self.returns_data = self.returns_data.loc[common_dates]

    def calculate_ic(self,
                     factor_name: str,
                     method: ICMethod = ICMethod.RANK) -> pd.Series:
        """
        计算每日IC（信息系数）

        Args:
            factor_name: 因子名称
            method: IC计算方法（RANK或PEARSON）

        Returns:
            pd.Series: 每日IC值，index为日期
        """
        factor = self.factor_data[factor_name]

        ic_series = []
        dates = factor.index.get_level_values('date').unique()

        for date in dates:
            try:
                # 获取当日因子值
                f = factor.xs(date, level='date')
                # 获取当日收益率
                r = self.returns_data.xs(date, level='date')

                # 对齐股票
                common_stocks = f.index.intersection(r.index)
                if len(common_stocks) < 10:  # 至少需要10只股票
                    continue

                f = f.loc[common_stocks]
                r = r.loc[common_stocks]

                # 去极值、标准化
                f = self._winsorize(f)
                f = self._standardize(f)

                # 计算相关系数
                if method == ICMethod.RANK:
                    ic = f.corr(r, method='spearman')
                else:
                    ic = f.corr(r, method='pearson')

                ic_series.append({'date': date, 'ic': ic})
            except Exception:
                continue

        if not ic_series:
            return pd.Series(dtype='float64')

        ic_df = pd.DataFrame(ic_series)
        ic_df['date'] = pd.to_datetime(ic_df['date'])
        return ic_df.set_index('date')['ic']

    def calculate_ic_stats(self,
                           factor_name: str,
                           method: ICMethod = ICMethod.RANK) -> ICStats:
        """
        计算IC统计指标

        Args:
            factor_name: 因子名称
            method: IC计算方法

        Returns:
            ICStats: IC统计结果
        """
        ic_series = self.calculate_ic(factor_name, method)

        if ic_series.empty:
            return ICStats(
                mean=0, std=0, ir=0, t_stat=0,
                positive_rate=0, win_rate=0,
                ic_series=pd.Series()
            )

        mean_ic = ic_series.mean()
        std_ic = ic_series.std()
        ir = mean_ic / std_ic if std_ic != 0 else 0

        # t统计量
        n = len(ic_series)
        t_stat = mean_ic / (std_ic / np.sqrt(n)) if std_ic != 0 else 0

        # IC为正的比例
        positive_rate = (ic_series > 0).sum() / len(ic_series)

        # 显著为正的比例（IC > 0.02）
        win_rate = (ic_series > 0.02).sum() / len(ic_series)

        return ICStats(
            mean=mean_ic,
            std=std_ic,
            ir=ir,
            t_stat=t_stat,
            positive_rate=positive_rate,
            win_rate=win_rate,
            ic_series=ic_series
        )

    def layered_backtest(self,
                          factor_name: str,
                          group_count: Optional[int] = None,
                          long_short: bool = True) -> LayeredBacktestResult:
        """
        分组回测（Layered Backtesting）

        将股票按因子值从小到大分组，计算每组的收益率

        Args:
            factor_name: 因子名称
            group_count: 分组数量（覆盖初始化值）
            long_short: 是否计算多空组合

        Returns:
            LayeredBacktestResult: 分组回测结果
        """
        group_count = group_count or self.group_count
        factor = self.factor_data[factor_name]

        group_returns = []
        ic_series = []
        dates = factor.index.get_level_values('date').unique()

        for date in dates:
            try:
                # 获取当日因子值
                f = factor.xs(date, level='date')
                # 获取当日收益率
                r = self.returns_data.xs(date, level='date')

                # 对齐股票
                common_stocks = f.index.intersection(r.index)
                if len(common_stocks) < group_count * 2:
                    continue

                f = f.loc[common_stocks]
                r = r.loc[common_stocks]

                # 去极值、标准化
                f = self._winsorize(f)

                # 计算当日IC
                ic = f.corr(r, method='spearman')
                ic_series.append({'date': date, 'ic': ic})

                # 分组
                groups = pd.qcut(f, group_count, labels=False, duplicates='drop')

                # 计算每组平均收益率
                daily_return = {'date': date}
                for g in range(group_count):
                    group_stocks = groups[groups == g].index
                    if len(group_stocks) > 0:
                        daily_return[f'group_{g+1}'] = r.loc[group_stocks].mean()
                    else:
                        daily_return[f'group_{g+1}'] = np.nan

                group_returns.append(daily_return)
            except Exception:
                continue

        if not group_returns:
            return LayeredBacktestResult(
                group_returns=pd.DataFrame(),
                group_cum_returns=pd.DataFrame(),
                long_short_return=pd.Series(),
                turnover=pd.Series(),
                ic_series=pd.Series()
            )

        # 构建返回结果
        returns_df = pd.DataFrame(group_returns)
        returns_df['date'] = pd.to_datetime(returns_df['date'])
        returns_df = returns_df.set_index('date').sort_index()

        # 计算累计收益率
        cum_returns = (1 + returns_df).cumprod()

        # 计算多空组合（做多最高分组，做空最低分组）
        long_short = pd.Series(dtype='float64')
        if long_short and len(returns_df.columns) >= 2:
            long_short = returns_df.iloc[:, -1] - returns_df.iloc[:, 0]

        # IC序列
        ic_df = pd.DataFrame(ic_series)
        ic_df['date'] = pd.to_datetime(ic_df['date'])
        ic_series = ic_df.set_index('date')['ic']

        # 计算换手率（简化版）
        turnover = pd.Series([0.2] * len(returns_df), index=returns_df.index)

        return LayeredBacktestResult(
            group_returns=returns_df,
            group_cum_returns=cum_returns,
            long_short_return=long_short,
            turnover=turnover,
            ic_series=ic_series
        )

    def factor_decay(self,
                     factor_name: str,
                     max_period: int = 20) -> FactorDecayResult:
        """
        因子衰减分析

        计算因子在不同持有期下的IC，观察因子预测能力的衰减

        Args:
            factor_name: 因子名称
            max_period: 最大持有期（交易日）

        Returns:
            FactorDecayResult: 因子衰减结果
        """
        factor = self.factor_data[factor_name]

        decay_ics = []

        for holding_period in range(1, max_period + 1):
            # 构建持有期收益率
            # 如果原始收益率是forward_period=5的，这里需要调整
            # 简化：直接使用因子数据计算不同滞后的IC
            ic_list = []
            dates = factor.index.get_level_values('date').unique()

            for i, date in enumerate(dates[:-holding_period]):
                try:
                    # t期因子
                    f_t = factor.xs(date, level='date')
                    # t+holding_period期收益率
                    future_date = dates[i + holding_period]
                    if future_date not in self.returns_data.index.get_level_values('date'):
                        continue

                    r_future = self.returns_data.xs(future_date, level='date')

                    common_stocks = f_t.index.intersection(r_future.index)
                    if len(common_stocks) < 10:
                        continue

                    f_t = f_t.loc[common_stocks]
                    r_future = r_future.loc[common_stocks]

                    f_t = self._winsorize(f_t)
                    ic = f_t.corr(r_future, method='spearman')
                    ic_list.append(ic)
                except Exception:
                    continue

            if ic_list:
                decay_ics.append({'period': holding_period, 'ic': np.mean(ic_list)})

        if not decay_ics:
            return FactorDecayResult(
                decay_curve=pd.Series(dtype='float64'),
                half_life=0
            )

        decay_df = pd.DataFrame(decay_ics)
        decay_curve = decay_df.set_index('period')['ic']

        # 计算半衰期
        half_life = max_period
        if len(decay_curve) > 0 and decay_curve.iloc[0] > 0:
            target_ic = decay_curve.iloc[0] * 0.5
            for period, ic in decay_curve.items():
                if ic <= target_ic:
                    half_life = period
                    break

        return FactorDecayResult(
            decay_curve=decay_curve,
            half_life=half_life
        )

    def evaluate_factor(self,
                        factor_name: str,
                        run_decay: bool = True) -> FactorEvaluationResult:
        """
        综合评价因子

        Args:
            factor_name: 因子名称
            run_decay: 是否运行衰减分析

        Returns:
            FactorEvaluationResult: 因子综合评价结果
        """
        print(f"\n📊 开始评价因子: {factor_name}")

        # 1. 计算IC统计
        print("   计算IC统计...")
        ic_stats = self.calculate_ic_stats(factor_name)

        # 2. 分组回测
        print("   分组回测...")
        layered_result = self.layered_backtest(factor_name)

        # 3. 因子衰减分析
        decay_result = None
        if run_decay:
            print("   因子衰减分析...")
            decay_result = self.factor_decay(factor_name)

        # 4. 计算综合得分
        stability_score = self._calculate_stability_score(ic_stats, layered_result)
        overall_score = self._calculate_overall_score(ic_stats, layered_result, decay_result)

        result = FactorEvaluationResult(
            factor_name=factor_name,
            ic_stats=ic_stats,
            layered_result=layered_result,
            decay_result=decay_result,
            stability_score=stability_score,
            overall_score=overall_score
        )

        self._print_evaluation_summary(result)
        return result

    def evaluate_multiple_factors(self,
                                   factor_names: List[str]) -> pd.DataFrame:
        """
        批量评价多个因子

        Args:
            factor_names: 因子名称列表

        Returns:
            DataFrame: 因子评价结果汇总
        """
        results = []

        for factor_name in factor_names:
            try:
                result = self.evaluate_factor(factor_name, run_decay=False)
                results.append({
                    'factor_name': result.factor_name,
                    'ic_mean': result.ic_stats.mean,
                    'ic_std': result.ic_stats.std,
                    'ic_ir': result.ic_stats.ir,
                    't_stat': result.ic_stats.t_stat,
                    'positive_rate': result.ic_stats.positive_rate,
                    'win_rate': result.ic_stats.win_rate,
                    'stability_score': result.stability_score,
                    'overall_score': result.overall_score
                })
            except Exception as e:
                print(f"   ❌ 因子 {factor_name} 评价失败: {e}")

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values('overall_score', ascending=False).reset_index(drop=True)

        return df

    def _winsorize(self, series: pd.Series, q: float = 0.05) -> pd.Series:
        """去极值（缩尾处理）"""
        lower = series.quantile(q)
        upper = series.quantile(1 - q)
        return series.clip(lower, upper)

    def _standardize(self, series: pd.Series) -> pd.Series:
        """标准化（z-score）"""
        mean = series.mean()
        std = series.std()
        if std == 0:
            return series
        return (series - mean) / std

    def _calculate_stability_score(self,
                                     ic_stats: ICStats,
                                     layered_result: LayeredBacktestResult) -> float:
        """计算稳定性得分（0-100）"""
        score = 0.0

        # IC稳定性（权重40%）
        if ic_stats.std > 0:
            # IC变异系数越小越稳定
            cv = abs(ic_stats.std / (ic_stats.mean + 1e-8))
            score += max(0, 40 * (1 - min(1, cv / 2)))

        # IC为正的比例（权重30%）
        score += ic_stats.positive_rate * 30

        # t统计量显著性（权重30%）
        if abs(ic_stats.t_stat) > 2:
            score += 30
        elif abs(ic_stats.t_stat) > 1.5:
            score += 20
        elif abs(ic_stats.t_stat) > 1:
            score += 10

        return min(100, max(0, score))

    def _calculate_overall_score(self,
                                  ic_stats: ICStats,
                                  layered_result: LayeredBacktestResult,
                                  decay_result: Optional[FactorDecayResult]) -> float:
        """计算综合得分（0-100）"""
        score = 0.0

        # IC水平（权重40%）
        ic_abs = abs(ic_stats.mean)
        if ic_abs > 0.1:
            score += 40
        elif ic_abs > 0.05:
            score += 30 + (ic_abs - 0.05) * 200
        elif ic_abs > 0.02:
            score += 10 + (ic_abs - 0.02) * 666.67
        else:
            score += ic_abs * 500

        # IR（权重30%）
        ir_abs = abs(ic_stats.ir)
        if ir_abs > 1.5:
            score += 30
        elif ir_abs > 1:
            score += 20 + (ir_abs - 1) * 20
        elif ir_abs > 0.5:
            score += 10 + (ir_abs - 0.5) * 20
        else:
            score += ir_abs * 20

        # 稳定性（权重30%）
        stability = self._calculate_stability_score(ic_stats, layered_result)
        score += stability * 0.3

        return min(100, max(0, score))

    def _print_evaluation_summary(self, result: FactorEvaluationResult):
        """打印评价摘要"""
        print(f"\n{'='*60}")
        print(f"📊 因子评价结果: {result.factor_name}")
        print(f"{'='*60}")
        print(f"  IC均值:    {result.ic_stats.mean:+.4f}")
        print(f"  IC标准差:  {result.ic_stats.std:.4f}")
        print(f"  IC_IR:     {result.ic_stats.ir:.4f}")
        print(f"  t统计量:   {result.ic_stats.t_stat:.4f}")
        print(f"  IC正值率:  {result.ic_stats.positive_rate:.2%}")
        print(f"  胜率(IC>2%): {result.ic_stats.win_rate:.2%}")
        print(f"  稳定性得分: {result.stability_score:.2f}")
        print(f"  综合得分:   {result.overall_score:.2f}")
        print(f"{'='*60}")


def prepare_factor_panel(factor_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    将因子字典转换为面板数据格式

    Args:
        factor_dict: 股票代码 -> 因子DataFrame的字典

    Returns:
        DataFrame: MultiIndex [date, ts_code]的因子面板
    """
    dfs = []

    for ts_code, df in factor_dict.items():
        if 'trade_date' in df.columns:
            df = df.copy()
            df['ts_code'] = ts_code
            df['date'] = pd.to_datetime(df['trade_date'])
            dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    panel = pd.concat(dfs, axis=0)
    panel = panel.set_index(['date', 'ts_code'])
    return panel


def prepare_returns_panel(data_dict: Dict[str, pd.DataFrame],
                           forward_period: int = 5) -> pd.DataFrame:
    """
    准备收益率面板数据

    Args:
        data_dict: 股票代码 -> 行情DataFrame的字典
        forward_period: 预测期（交易日）

    Returns:
        DataFrame: MultiIndex [date, ts_code]的收益率面板
    """
    dfs = []

    for ts_code, df in data_dict.items():
        if 'trade_date' in df.columns and 'close' in df.columns:
            df = df.copy()
            df = df.sort_values('trade_date').reset_index(drop=True)

            # 计算未来N日收益率
            df['future_return'] = df['close'].pct_change(forward_period).shift(-forward_period)

            df['ts_code'] = ts_code
            df['date'] = pd.to_datetime(df['trade_date'])
            dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    panel = pd.concat(dfs, axis=0)
    panel = panel.set_index(['date', 'ts_code'])

    return panel[['future_return']].rename(columns={'future_return': 'return'})
