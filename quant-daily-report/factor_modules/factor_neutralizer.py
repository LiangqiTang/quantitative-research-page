"""
因子中性化模块 - 专业因子正交化处理
包含市值中性化、行业中性化、Barra风格因子中性化、因子正交化
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')


class NeutralizationMethod(Enum):
    """中性化方法"""
    RESIDUAL = "residual"        # 残差法（回归取残差）
    RANK = "rank"                # 排序法（行业内排序）
    ZSCORE = "zscore"            # Z-score法（行业内标准化）


@dataclass
class NeutralizationResult:
    """中性化结果"""
    original_factor: pd.Series
    neutralized_factor: pd.Series
    method: NeutralizationMethod
    neutralization_type: str
    r_squared: Optional[float] = None  # 回归的R²
    correlation_before: Optional[float] = None  # 中性化前与中性化变量的相关性
    correlation_after: Optional[float] = None   # 中性化后与中性化变量的相关性


class FactorNeutralizer:
    """
    因子中性化器

    核心功能：
    - 市值中性化：剔除市值因子暴露
    - 行业中性化：剔除行业因子暴露
    - Barra风格因子中性化：市值、贝塔、动量、波动率、流动性、成长性、价值、盈利
    - 正交化处理：因子之间的相关性处理
    """

    def __init__(self):
        """初始化因子中性化器"""
        print(f"✅ 因子中性化器初始化完成")

    def neutralize_by_market_cap(self,
                                   factor: pd.Series,
                                   market_cap: pd.Series,
                                   method: NeutralizationMethod = NeutralizationMethod.RESIDUAL,
                                   use_log: bool = True) -> NeutralizationResult:
        """
        市值中性化

        Args:
            factor: 原始因子，MultiIndex [date, ts_code]
            market_cap: 市值数据，MultiIndex [date, ts_code]
            method: 中性化方法
            use_log: 是否对市值取对数

        Returns:
            NeutralizationResult: 中性化结果
        """
        # 对齐数据
        factor = factor.copy()
        market_cap = market_cap.copy()

        common_index = factor.index.intersection(market_cap.index)
        if len(common_index) == 0:
            return NeutralizationResult(
                original_factor=factor,
                neutralized_factor=factor,
                method=method,
                neutralization_type="market_cap"
            )

        factor = factor.loc[common_index]
        market_cap = market_cap.loc[common_index]

        # 对市值取对数
        if use_log:
            market_cap = np.log(market_cap)

        # 计算中性化前的相关性
        corr_before = factor.corr(market_cap)

        # 逐日中性化
        neutralized = []
        r_squared_values = []

        for date in factor.index.get_level_values('date').unique():
            try:
                f_day = factor.xs(date, level='date')
                m_day = market_cap.xs(date, level='date')

                # 对齐
                common = f_day.index.intersection(m_day.index)
                if len(common) < 5:
                    continue

                f_day = f_day.loc[common]
                m_day = m_day.loc[common]

                if method == NeutralizationMethod.RESIDUAL:
                    # 回归取残差
                    result = self._regress_residual(f_day, m_day)
                    neutralized.append(result['residual'])
                    if result['r_squared'] is not None:
                        r_squared_values.append(result['r_squared'])
                else:
                    # 简单去极值标准化
                    f_neu = self._winsorize(f_day)
                    f_neu = (f_neu - f_neu.mean()) / f_neu.std() if f_neu.std() > 0 else f_neu
                    neutralized.append(f_neu)

            except Exception:
                continue

        if not neutralized:
            return NeutralizationResult(
                original_factor=factor,
                neutralized_factor=factor,
                method=method,
                neutralization_type="market_cap"
            )

        neutralized_series = pd.concat(neutralized)

        # 计算中性化后的相关性
        corr_after = neutralized_series.corr(market_cap.loc[neutralized_series.index]) if len(neutralized_series) > 0 else None

        return NeutralizationResult(
            original_factor=factor,
            neutralized_factor=neutralized_series,
            method=method,
            neutralization_type="market_cap",
            r_squared=np.mean(r_squared_values) if r_squared_values else None,
            correlation_before=corr_before,
            correlation_after=corr_after
        )

    def neutralize_by_industry(self,
                                factor: pd.Series,
                                industry: pd.Series,
                                method: NeutralizationMethod = NeutralizationMethod.RESIDUAL) -> NeutralizationResult:
        """
        行业中性化

        Args:
            factor: 原始因子，MultiIndex [date, ts_code]
            industry: 行业分类，MultiIndex [date, ts_code] 或单索引 [ts_code]
            method: 中性化方法

        Returns:
            NeutralizationResult: 中性化结果
        """
        factor = factor.copy()

        # 检查行业数据是否有日期维度
        if isinstance(industry.index, pd.MultiIndex):
            # 有日期维度，直接对齐
            common_index = factor.index.intersection(industry.index)
            if len(common_index) == 0:
                return NeutralizationResult(
                    original_factor=factor,
                    neutralized_factor=factor,
                    method=method,
                    neutralization_type="industry"
                )
            factor = factor.loc[common_index]
            industry = industry.loc[common_index]
        else:
            # 无日期维度，按股票代码对齐
            factor_df = factor.reset_index()
            if 'ts_code' not in factor_df.columns:
                return NeutralizationResult(
                    original_factor=factor,
                    neutralized_factor=factor,
                    method=method,
                    neutralization_type="industry"
                )

            # 合并行业数据
            factor_df['industry'] = factor_df['ts_code'].map(industry)

            # 转换回MultiIndex
            if 'date' in factor_df.columns:
                factor_df = factor_df.set_index(['date', 'ts_code'])
            else:
                factor_df = factor_df.set_index(['ts_code'])

            industry = factor_df['industry']
            factor = factor_df[factor.name] if factor.name in factor_df.columns else factor_df.iloc[:, 0]

        # 逐日中性化
        neutralized = []

        for date in factor.index.get_level_values('date').unique():
            try:
                f_day = factor.xs(date, level='date')
                ind_day = industry.xs(date, level='date')

                # 对齐
                common = f_day.index.intersection(ind_day.index)
                if len(common) < 10:
                    continue

                f_day = f_day.loc[common]
                ind_day = ind_day.loc[common]

                if method == NeutralizationMethod.RESIDUAL:
                    # 对行业虚拟变量回归取残差
                    result = self._regress_industry(f_day, ind_day)
                    neutralized.append(result['residual'])
                elif method == NeutralizationMethod.RANK:
                    # 行业内排序
                    result = self._rank_within_industry(f_day, ind_day)
                    neutralized.append(result)
                else:  # ZSCORE
                    # 行业内标准化
                    result = self._zscore_within_industry(f_day, ind_day)
                    neutralized.append(result)

            except Exception:
                continue

        if not neutralized:
            return NeutralizationResult(
                original_factor=factor,
                neutralized_factor=factor,
                method=method,
                neutralization_type="industry"
            )

        neutralized_series = pd.concat(neutralized)

        return NeutralizationResult(
            original_factor=factor,
            neutralized_factor=neutralized_series,
            method=method,
            neutralization_type="industry"
        )

    def neutralize_by_barra(self,
                             factor: pd.Series,
                             barra_factors: pd.DataFrame,
                             method: NeutralizationMethod = NeutralizationMethod.RESIDUAL) -> NeutralizationResult:
        """
        Barra风格因子中性化

        Barra风格因子通常包括：
        - SIZE: 市值
        - BETA: 贝塔
        - MOM: 动量
        - VOL: 波动率
        - LIQ: 流动性
        - GROWTH: 成长性
        - VALUE: 价值
        - EARNINGS: 盈利

        Args:
            factor: 原始因子，MultiIndex [date, ts_code]
            barra_factors: Barra风格因子，MultiIndex [date, ts_code]，columns为各风格因子
            method: 中性化方法

        Returns:
            NeutralizationResult: 中性化结果
        """
        factor = factor.copy()

        # 对齐数据
        common_index = factor.index.intersection(barra_factors.index)
        if len(common_index) == 0:
            return NeutralizationResult(
                original_factor=factor,
                neutralized_factor=factor,
                method=method,
                neutralization_type="barra"
            )

        factor = factor.loc[common_index]
        barra_factors = barra_factors.loc[common_index]

        # 逐日中性化
        neutralized = []
        r_squared_values = []

        for date in factor.index.get_level_values('date').unique():
            try:
                f_day = factor.xs(date, level='date')
                b_day = barra_factors.xs(date, level='date')

                # 对齐
                common = f_day.index.intersection(b_day.index)
                if len(common) < 10:
                    continue

                f_day = f_day.loc[common]
                b_day = b_day.loc[common]

                if method == NeutralizationMethod.RESIDUAL:
                    # 对Barra因子多元回归取残差
                    result = self._regress_multiple(f_day, b_day)
                    neutralized.append(result['residual'])
                    if result['r_squared'] is not None:
                        r_squared_values.append(result['r_squared'])
                else:
                    # 简单去极值标准化
                    f_neu = self._winsorize(f_day)
                    f_neu = (f_neu - f_neu.mean()) / f_neu.std() if f_neu.std() > 0 else f_neu
                    neutralized.append(f_neu)

            except Exception:
                continue

        if not neutralized:
            return NeutralizationResult(
                original_factor=factor,
                neutralized_factor=factor,
                method=method,
                neutralization_type="barra"
            )

        neutralized_series = pd.concat(neutralized)

        return NeutralizationResult(
            original_factor=factor,
            neutralized_factor=neutralized_series,
            method=method,
            neutralization_type="barra",
            r_squared=np.mean(r_squared_values) if r_squared_values else None
        )

    def neutralize_multiple(self,
                            factor: pd.Series,
                            market_cap: Optional[pd.Series] = None,
                            industry: Optional[pd.Series] = None,
                            barra_factors: Optional[pd.DataFrame] = None) -> NeutralizationResult:
        """
        多级中性化（市值 + 行业 + Barra）

        Args:
            factor: 原始因子
            market_cap: 市值数据
            industry: 行业数据
            barra_factors: Barra风格因子

        Returns:
            NeutralizationResult: 中性化结果
        """
        current_factor = factor.copy()

        # 1. 先市值中性化
        if market_cap is not None:
            result = self.neutralize_by_market_cap(current_factor, market_cap)
            current_factor = result.neutralized_factor

        # 2. 再行业中性化
        if industry is not None:
            result = self.neutralize_by_industry(current_factor, industry)
            current_factor = result.neutralized_factor

        # 3. 最后Barra风格中性化
        if barra_factors is not None:
            result = self.neutralize_by_barra(current_factor, barra_factors)
            current_factor = result.neutralized_factor

        return NeutralizationResult(
            original_factor=factor,
            neutralized_factor=current_factor,
            method=NeutralizationMethod.RESIDUAL,
            neutralization_type="multiple"
        )

    def orthogonalize_factors(self,
                              factors: pd.DataFrame,
                              reference_factor: Optional[str] = None) -> pd.DataFrame:
        """
        因子正交化

        使用Gram-Schmidt正交化过程，使得因子之间互不相关

        Args:
            factors: 因子数据框，columns为因子名
            reference_factor: 参考因子（第一个正交化的因子，保持不变）

        Returns:
            DataFrame: 正交化后的因子
        """
        factors = factors.copy()

        # 确定正交化顺序
        factor_names = list(factors.columns)

        if reference_factor and reference_factor in factor_names:
            # 将参考因子放到第一位
            factor_names.remove(reference_factor)
            factor_names = [reference_factor] + factor_names

        # 初始化正交化后的因子
        orthogonal = pd.DataFrame(index=factors.index)

        for i, factor_name in enumerate(factor_names):
            f = factors[factor_name].copy()

            # 对前面已正交化的因子回归取残差
            for j in range(i):
                prev_factor = orthogonal.iloc[:, j]

                # 对齐
                common = f.index.intersection(prev_factor.index)
                if len(common) < 5:
                    continue

                f_sub = f.loc[common]
                p_sub = prev_factor.loc[common]

                # 去极值
                f_sub = self._winsorize(f_sub)
                p_sub = self._winsorize(p_sub)

                # 回归
                beta = np.cov(f_sub, p_sub)[0, 1] / np.var(p_sub) if np.var(p_sub) > 0 else 0
                f.loc[common] = f_sub - beta * p_sub

            orthogonal[factor_name] = f

        # 标准化
        for col in orthogonal.columns:
            s = orthogonal[col]
            s = self._winsorize(s)
            orthogonal[col] = (s - s.mean()) / s.std() if s.std() > 0 else s

        return orthogonal

    # ===== 内部方法 =====

    def _regress_residual(self, y: pd.Series, x: pd.Series) -> Dict:
        """一元线性回归取残差"""
        # 去极值
        y = self._winsorize(y)
        x = self._winsorize(x)

        # 标准化
        y_std = (y - y.mean()) / y.std() if y.std() > 0 else y
        x_std = (x - x.mean()) / x.std() if x.std() > 0 else x

        # 计算回归系数
        n = len(y_std)
        xy_cov = np.cov(y_std, x_std)[0, 1] if n > 1 else 0
        x_var = np.var(x_std) if n > 1 else 0

        if x_var == 0:
            return {'residual': y_std, 'r_squared': 0}

        beta = xy_cov / x_var
        residual = y_std - beta * x_std

        # 计算R²
        y_var = np.var(y_std)
        r_squared = 1 - np.var(residual) / y_var if y_var > 0 else 0

        return {'residual': residual, 'r_squared': r_squared}

    def _regress_industry(self, y: pd.Series, industry: pd.Series) -> Dict:
        """对行业虚拟变量回归取残差"""
        y = self._winsorize(y)
        y_std = (y - y.mean()) / y.std() if y.std() > 0 else y

        # 创建行业虚拟变量
        dummies = pd.get_dummies(industry, drop_first=True)

        if dummies.shape[1] == 0:
            return {'residual': y_std, 'r_squared': 0}

        # 简单方法：行业内去均值
        industry_means = y_std.groupby(industry).transform('mean')
        residual = y_std - industry_means

        # 计算伪R²
        y_var = np.var(y_std)
        r_squared = 1 - np.var(residual) / y_var if y_var > 0 else 0

        return {'residual': residual, 'r_squared': r_squared}

    def _regress_multiple(self, y: pd.Series, x: pd.DataFrame) -> Dict:
        """多元线性回归取残差（简化版）"""
        y = self._winsorize(y)
        y_std = (y - y.mean()) / y.std() if y.std() > 0 else y

        residual = y_std.copy()

        # 逐个因子回归
        for col in x.columns:
            xi = x[col]

            # 对齐
            common = residual.index.intersection(xi.index)
            if len(common) < 5:
                continue

            r_sub = residual.loc[common]
            x_sub = xi.loc[common]

            # 去极值
            x_sub = self._winsorize(x_sub)
            x_sub = (x_sub - x_sub.mean()) / x_sub.std() if x_sub.std() > 0 else x_sub

            # 回归
            xy_cov = np.cov(r_sub, x_sub)[0, 1] if len(r_sub) > 1 else 0
            x_var = np.var(x_sub) if len(x_sub) > 1 else 0

            if x_var > 0:
                beta = xy_cov / x_var
                residual.loc[common] = r_sub - beta * x_sub

        y_var = np.var(y_std)
        r_squared = 1 - np.var(residual) / y_var if y_var > 0 else 0

        return {'residual': residual, 'r_squared': r_squared}

    def _rank_within_industry(self, y: pd.Series, industry: pd.Series) -> pd.Series:
        """行业内排序"""
        y = self._winsorize(y)

        # 行业内排序并标准化到[-0.5, 0.5]
        ranked = y.groupby(industry).rank(pct=True) - 0.5

        return ranked

    def _zscore_within_industry(self, y: pd.Series, industry: pd.Series) -> pd.Series:
        """行业内Z-score标准化"""
        y = self._winsorize(y)

        # 行业内去均值、除标准差
        def zscore(group):
            if len(group) < 2:
                return group * 0
            return (group - group.mean()) / group.std() if group.std() > 0 else group * 0

        zscored = y.groupby(industry).transform(zscore)

        return zscored

    def _winsorize(self, series: pd.Series, q: float = 0.05) -> pd.Series:
        """去极值（缩尾处理）"""
        if len(series) < 10:
            return series

        lower = series.quantile(q)
        upper = series.quantile(1 - q)
        return series.clip(lower, upper)
