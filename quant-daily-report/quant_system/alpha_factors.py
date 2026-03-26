"""
Alpha因子库 - 专业Alpha因子集合
参考Alpha101/Alpha158，包含价量类、技术指标增强、资金流向类因子
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum


class AlphaFactorType(Enum):
    """Alpha因子类型"""
    PRICE_VOLUME = "price_volume"    # 价量类
    TECHNICAL = "technical"          # 技术指标类
    MOMENTUM = "momentum"            # 动量类
    VOLATILITY = "volatility"        # 波动率类
    LIQUIDITY = "liquidity"          # 流动性类
    SENTIMENT = "sentiment"          # 情绪类


@dataclass
class AlphaFactorDef:
    """Alpha因子定义"""
    name: str
    type: AlphaFactorType
    description: str
    category: str
    reference: str  # 参考来源


class AlphaFactorCalculator:
    """
    Alpha因子计算器

    包含参考Alpha101/Alpha158的专业因子库：
    - 价量类因子（参考Alpha101）
    - 技术指标增强
    - 资金流向类因子
    """

    def __init__(self):
        """初始化Alpha因子计算器"""
        self.factor_definitions = self._init_factor_definitions()
        print(f"✅ Alpha因子计算器初始化完成，共{len(self.factor_definitions)}个因子")

    def _init_factor_definitions(self) -> Dict[str, AlphaFactorDef]:
        """初始化因子定义"""
        factors = {}

        # ===== 价量类因子（参考Alpha101）=====

        # Alpha1: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)
        factors['alpha_001'] = AlphaFactorDef(
            name='alpha_001',
            type=AlphaFactorType.PRICE_VOLUME,
            description='Alpha101: 下跌时波动率，上涨时收盘价，取5日最大值',
            category='Alpha101',
            reference='WorldQuant Alpha101'
        )

        # Alpha2: (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))
        factors['alpha_002'] = AlphaFactorDef(
            name='alpha_002',
            type=AlphaFactorType.PRICE_VOLUME,
            description='Alpha101: 成交量变化与日内收益的秩相关',
            category='Alpha101',
            reference='WorldQuant Alpha101'
        )

        # Alpha3: (-1 * correlation(rank(open), rank(volume), 10))
        factors['alpha_003'] = AlphaFactorDef(
            name='alpha_003',
            type=AlphaFactorType.PRICE_VOLUME,
            description='Alpha101: 开盘价与成交量的秩相关',
            category='Alpha101',
            reference='WorldQuant Alpha101'
        )

        # Alpha4: (-1 * Ts_Rank(rank(low), 9))
        factors['alpha_004'] = AlphaFactorDef(
            name='alpha_004',
            type=AlphaFactorType.PRICE_VOLUME,
            description='Alpha101: 最低价排名的时序排名',
            category='Alpha101',
            reference='WorldQuant Alpha101'
        )

        # Alpha5: (rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))
        factors['alpha_005'] = AlphaFactorDef(
            name='alpha_005',
            type=AlphaFactorType.PRICE_VOLUME,
            description='Alpha101: 开盘价偏离VWAP',
            category='Alpha101',
            reference='WorldQuant Alpha101'
        )

        # Alpha6: (-1 * correlation(open, volume, 10))
        factors['alpha_006'] = AlphaFactorDef(
            name='alpha_006',
            type=AlphaFactorType.PRICE_VOLUME,
            description='Alpha101: 开盘价与成交量的相关系数',
            category='Alpha101',
            reference='WorldQuant Alpha101'
        )

        # Alpha7: ((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * 1))
        factors['alpha_007'] = AlphaFactorDef(
            name='alpha_007',
            type=AlphaFactorType.PRICE_VOLUME,
            description='Alpha101: 放量时的动量因子',
            category='Alpha101',
            reference='WorldQuant Alpha101'
        )

        # Alpha8: (-1 * rank(((sum(open, 5) * sum(returns, 5)) - delay((sum(open, 5) * sum(returns, 5)), 10))))
        factors['alpha_008'] = AlphaFactorDef(
            name='alpha_008',
            type=AlphaFactorType.PRICE_VOLUME,
            description='Alpha101: 价格与成交量的交叉动量',
            category='Alpha101',
            reference='WorldQuant Alpha101'
        )

        # Alpha9: ((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ? delta(close, 1) : (-1 * delta(close, 1))))
        factors['alpha_009'] = AlphaFactorDef(
            name='alpha_009',
            type=AlphaFactorType.MOMENTUM,
            description='Alpha101: 基于涨跌持续性的动量',
            category='Alpha101',
            reference='WorldQuant Alpha101'
        )

        # Alpha10: rank(((0 < ts_min(delta(close, 1), 4)) ? delta(close, 1) : ((ts_max(delta(close, 1), 4) < 0) ? delta(close, 1) : (-1 * delta(close, 1)))))
        factors['alpha_010'] = AlphaFactorDef(
            name='alpha_010',
            type=AlphaFactorType.MOMENTUM,
            description='Alpha101: 基于涨跌持续性的动量排名',
            category='Alpha101',
            reference='WorldQuant Alpha101'
        )

        # ===== 价量类因子（通用）=====

        factors['roc_5'] = AlphaFactorDef(
            name='roc_5',
            type=AlphaFactorType.MOMENTUM,
            description='5日收益率',
            category='ROC',
            reference='Classic'
        )

        factors['roc_10'] = AlphaFactorDef(
            name='roc_10',
            type=AlphaFactorType.MOMENTUM,
            description='10日收益率',
            category='ROC',
            reference='Classic'
        )

        factors['roc_20'] = AlphaFactorDef(
            name='roc_20',
            type=AlphaFactorType.MOMENTUM,
            description='20日收益率',
            category='ROC',
            reference='Classic'
        )

        # 波动率类
        factors['vol_10'] = AlphaFactorDef(
            name='vol_10',
            type=AlphaFactorType.VOLATILITY,
            description='10日波动率',
            category='Volatility',
            reference='Classic'
        )

        factors['vol_20'] = AlphaFactorDef(
            name='vol_20',
            type=AlphaFactorType.VOLATILITY,
            description='20日波动率',
            category='Volatility',
            reference='Classic'
        )

        factors['atr_14'] = AlphaFactorDef(
            name='atr_14',
            type=AlphaFactorType.VOLATILITY,
            description='14日ATR',
            category='ATR',
            reference='Classic'
        )

        # 成交量类
        factors['vol_ratio_5'] = AlphaFactorDef(
            name='vol_ratio_5',
            type=AlphaFactorType.LIQUIDITY,
            description='5日量比',
            category='Volume',
            reference='Classic'
        )

        factors['vol_ratio_20'] = AlphaFactorDef(
            name='vol_ratio_20',
            type=AlphaFactorType.LIQUIDITY,
            description='20日量比',
            category='Volume',
            reference='Classic'
        )

        factors['turnover'] = AlphaFactorDef(
            name='turnover',
            type=AlphaFactorType.LIQUIDITY,
            description='换手率（模拟）',
            category='Liquidity',
            reference='Classic'
        )

        # ===== 技术指标增强 =====

        # KDJ系列
        factors['kdj_k'] = AlphaFactorDef(
            name='kdj_k',
            type=AlphaFactorType.TECHNICAL,
            description='KDJ的K值',
            category='KDJ',
            reference='Classic'
        )

        factors['kdj_d'] = AlphaFactorDef(
            name='kdj_d',
            type=AlphaFactorType.TECHNICAL,
            description='KDJ的D值',
            category='KDJ',
            reference='Classic'
        )

        factors['kdj_j'] = AlphaFactorDef(
            name='kdj_j',
            type=AlphaFactorType.TECHNICAL,
            description='KDJ的J值',
            category='KDJ',
            reference='Classic'
        )

        # CCI
        factors['cci_14'] = AlphaFactorDef(
            name='cci_14',
            type=AlphaFactorType.TECHNICAL,
            description='14日CCI商品通道指标',
            category='CCI',
            reference='Classic'
        )

        # WR威廉指标
        factors['wr_14'] = AlphaFactorDef(
            name='wr_14',
            type=AlphaFactorType.TECHNICAL,
            description='14日威廉指标',
            category='WR',
            reference='Classic'
        )

        factors['wr_28'] = AlphaFactorDef(
            name='wr_28',
            type=AlphaFactorType.TECHNICAL,
            description='28日威廉指标',
            category='WR',
            reference='Classic'
        )

        # DMA平均线差
        factors['dma_dif'] = AlphaFactorDef(
            name='dma_dif',
            type=AlphaFactorType.TECHNICAL,
            description='DMA差离值',
            category='DMA',
            reference='Classic'
        )

        factors['dma_ama'] = AlphaFactorDef(
            name='dma_ama',
            type=AlphaFactorType.TECHNICAL,
            description='DMA平均线',
            category='DMA',
            reference='Classic'
        )

        # TRIX三重指数平滑
        factors['trix'] = AlphaFactorDef(
            name='trix',
            type=AlphaFactorType.TECHNICAL,
            description='TRIX指标',
            category='TRIX',
            reference='Classic'
        )

        factors['trix_signal'] = AlphaFactorDef(
            name='trix_signal',
            type=AlphaFactorType.TECHNICAL,
            description='TRIX信号线',
            category='TRIX',
            reference='Classic'
        )

        # ===== 资金流向类 =====

        factors['money_flow_index'] = AlphaFactorDef(
            name='money_flow_index',
            type=AlphaFactorType.SENTIMENT,
            description='MFI资金流量指标',
            category='MoneyFlow',
            reference='Classic'
        )

        factors['obv'] = AlphaFactorDef(
            name='obv',
            type=AlphaFactorType.SENTIMENT,
            description='OBV能量潮',
            category='MoneyFlow',
            reference='Classic'
        )

        factors['obv_ma'] = AlphaFactorDef(
            name='obv_ma',
            type=AlphaFactorType.SENTIMENT,
            description='OBV移动平均',
            category='MoneyFlow',
            reference='Classic'
        )

        factors['ad_line'] = AlphaFactorDef(
            name='ad_line',
            type=AlphaFactorType.SENTIMENT,
            description='AD累积派发线',
            category='MoneyFlow',
            reference='Classic'
        )

        factors['ad_oscillator'] = AlphaFactorDef(
            name='ad_oscillator',
            type=AlphaFactorType.SENTIMENT,
            description='AD震荡指标',
            category='MoneyFlow',
            reference='Classic'
        )

        # ===== 高级价量因子 =====

        factors['price_volume_corr'] = AlphaFactorDef(
            name='price_volume_corr',
            type=AlphaFactorType.PRICE_VOLUME,
            description='价量相关性',
            category='Correlation',
            reference='Classic'
        )

        factors['high_low_ratio'] = AlphaFactorDef(
            name='high_low_ratio',
            type=AlphaFactorType.PRICE_VOLUME,
            description='高低价位置',
            category='PricePosition',
            reference='Classic'
        )

        factors['close_position'] = AlphaFactorDef(
            name='close_position',
            type=AlphaFactorType.PRICE_VOLUME,
            description='收盘价在日内波动中的位置',
            category='PricePosition',
            reference='Classic'
        )

        factors['volume_price_trend'] = AlphaFactorDef(
            name='volume_price_trend',
            type=AlphaFactorType.PRICE_VOLUME,
            description='量价趋势指标',
            category='Trend',
            reference='Classic'
        )

        return factors

    def calculate_factor(self, df: pd.DataFrame, factor_name: str) -> Optional[pd.Series]:
        """
        计算单个Alpha因子

        Args:
            df: 价格数据（需包含open, high, low, close, volume/vol）
            factor_name: 因子名称

        Returns:
            Series: 因子值
        """
        if factor_name not in self.factor_definitions:
            return None

        # 检查必需的列
        required_cols = ['close']
        if not all(col in df.columns for col in required_cols):
            return pd.Series([np.nan] * len(df), index=df.index)

        # ===== Alpha101因子 =====

        if factor_name == 'alpha_001':
            return self._alpha_001(df)
        elif factor_name == 'alpha_002':
            return self._alpha_002(df)
        elif factor_name == 'alpha_003':
            return self._alpha_003(df)
        elif factor_name == 'alpha_004':
            return self._alpha_004(df)
        elif factor_name == 'alpha_005':
            return self._alpha_005(df)
        elif factor_name == 'alpha_006':
            return self._alpha_006(df)
        elif factor_name == 'alpha_007':
            return self._alpha_007(df)
        elif factor_name == 'alpha_008':
            return self._alpha_008(df)
        elif factor_name == 'alpha_009':
            return self._alpha_009(df)
        elif factor_name == 'alpha_010':
            return self._alpha_010(df)

        # ===== 价量类因子 =====

        elif factor_name == 'roc_5':
            return self._roc(df, 5)
        elif factor_name == 'roc_10':
            return self._roc(df, 10)
        elif factor_name == 'roc_20':
            return self._roc(df, 20)

        elif factor_name == 'vol_10':
            return self._volatility(df, 10)
        elif factor_name == 'vol_20':
            return self._volatility(df, 20)
        elif factor_name == 'atr_14':
            return self._atr(df, 14)

        elif factor_name == 'vol_ratio_5':
            return self._vol_ratio(df, 5)
        elif factor_name == 'vol_ratio_20':
            return self._vol_ratio(df, 20)
        elif factor_name == 'turnover':
            return self._turnover(df)

        # ===== 技术指标 =====

        elif factor_name == 'kdj_k':
            return self._kdj(df)[0]
        elif factor_name == 'kdj_d':
            return self._kdj(df)[1]
        elif factor_name == 'kdj_j':
            return self._kdj(df)[2]

        elif factor_name == 'cci_14':
            return self._cci(df, 14)

        elif factor_name == 'wr_14':
            return self._williams_r(df, 14)
        elif factor_name == 'wr_28':
            return self._williams_r(df, 28)

        elif factor_name == 'dma_dif':
            return self._dma(df)[0]
        elif factor_name == 'dma_ama':
            return self._dma(df)[1]

        elif factor_name == 'trix':
            return self._trix(df)[0]
        elif factor_name == 'trix_signal':
            return self._trix(df)[1]

        # ===== 资金流向 =====

        elif factor_name == 'money_flow_index':
            return self._mfi(df, 14)
        elif factor_name == 'obv':
            return self._obv(df)
        elif factor_name == 'obv_ma':
            return self._obv(df).rolling(10).mean()
        elif factor_name == 'ad_line':
            return self._ad_line(df)
        elif factor_name == 'ad_oscillator':
            return self._ad_oscillator(df)

        # ===== 高级价量 =====

        elif factor_name == 'price_volume_corr':
            return self._price_volume_corr(df, 10)
        elif factor_name == 'high_low_ratio':
            return self._high_low_position(df, 20)
        elif factor_name == 'close_position':
            return self._close_position(df)
        elif factor_name == 'volume_price_trend':
            return self._volume_price_trend(df)

        return None

    def calculate_all_factors(self, df: pd.DataFrame,
                               factor_names: Optional[List[str]] = None) -> Dict[str, pd.Series]:
        """
        计算所有Alpha因子

        Args:
            df: 价格数据
            factor_names: 指定因子列表，None则计算所有

        Returns:
            Dict: 因子结果字典
        """
        if factor_names is None:
            factor_names = list(self.factor_definitions.keys())

        results = {}
        for name in factor_names:
            try:
                factor = self.calculate_factor(df, name)
                if factor is not None:
                    results[name] = factor
            except Exception:
                continue

        return results

    def get_available_factors(self) -> List[str]:
        """获取可用因子列表"""
        return list(self.factor_definitions.keys())

    def get_factor_info(self, factor_name: str) -> Optional[AlphaFactorDef]:
        """获取因子信息"""
        return self.factor_definitions.get(factor_name)

    # ===== Alpha101因子实现 =====

    def _alpha_001(self, df: pd.DataFrame) -> pd.Series:
        """Alpha1: 下跌时波动率，上涨时收盘价"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        close = df['close']
        returns = close.pct_change()
        std_20 = returns.rolling(20).std()

        # 条件选择：下跌时用波动率，上涨时用收盘价
        condition = returns < 0
        part1 = std_20.copy()
        part2 = close.copy()

        # 简化版：取5日最大值位置
        result = pd.Series(np.nan, index=df.index)
        # 排名取最高
        for i in range(5, len(df)):
            window = returns.iloc[i-4:i+1]
            if len(window) > 0:
                result.iloc[i] = window.rank(pct=True).iloc[-1] - 0.5

        return result

    def _alpha_002(self, df: pd.DataFrame) -> pd.Series:
        """Alpha2: 成交量变化与日内收益的秩相关"""
        if 'open' not in df.columns or 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        volume = df[vol_col]
        open_p = df['open']
        close_p = df['close']

        # 成交量对数变化
        vol_delta = np.log(volume).diff(2)

        # 日内收益率
        intraday_ret = (close_p - open_p) / open_p

        # 6日滚动秩相关
        corr = pd.Series(np.nan, index=df.index)

        for i in range(6, len(df)):
            try:
                v = vol_delta.iloc[i-5:i+1].rank(pct=True)
                r = intraday_ret.iloc[i-5:i+1].rank(pct=True)
                corr.iloc[i] = v.corr(r)
            except:
                continue

        return -1 * corr

    def _alpha_003(self, df: pd.DataFrame) -> pd.Series:
        """Alpha3: 开盘价与成交量的秩相关"""
        if 'open' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        open_p = df['open']
        volume = df[vol_col]

        # 10日滚动秩相关
        corr = pd.Series(np.nan, index=df.index)

        for i in range(10, len(df)):
            try:
                o = open_p.iloc[i-9:i+1].rank(pct=True)
                v = volume.iloc[i-9:i+1].rank(pct=True)
                corr.iloc[i] = o.corr(v)
            except:
                continue

        return -1 * corr

    def _alpha_004(self, df: pd.DataFrame) -> pd.Series:
        """Alpha4: 最低价排名的时序排名"""
        if 'low' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        low = df['low']

        # 横截面排名（简化为时序排名）
        rank = low.rolling(20).rank(pct=True)

        # 时序排名
        ts_rank = rank.rolling(9).rank(pct=True)

        return -1 * ts_rank

    def _alpha_005(self, df: pd.DataFrame) -> pd.Series:
        """Alpha5: 开盘价偏离VWAP"""
        vwap = self._vwap(df)
        if vwap is None:
            return pd.Series([np.nan] * len(df), index=df.index)

        if 'open' not in df.columns or 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        open_p = df['open']
        close_p = df['close']

        vwap_ma_10 = vwap.rolling(10).mean()
        open_dev = (open_p - vwap_ma_10).rank(pct=True)
        close_dev = (close_p - vwap).rank(pct=True)

        return open_dev * (-1 * abs(close_dev))

    def _alpha_006(self, df: pd.DataFrame) -> pd.Series:
        """Alpha6: 开盘价与成交量的相关系数"""
        if 'open' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        open_p = df['open']
        volume = df[vol_col]

        # 10日滚动相关
        corr = open_p.rolling(10).corr(volume)

        return -1 * corr

    def _alpha_007(self, df: pd.DataFrame) -> pd.Series:
        """Alpha7: 放量时的动量因子"""
        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns or 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        close = df['close']
        volume = df[vol_col]

        adv20 = volume.rolling(20).mean()
        delta7 = close.diff(7)
        abs_delta7_rank = abs(delta7).rolling(60).rank(pct=True)
        sign_delta7 = np.sign(delta7)

        condition = adv20 < volume
        result = pd.Series(np.nan, index=df.index)

        result[condition] = -1 * abs_delta7_rank[condition] * sign_delta7[condition]
        result[~condition] = -1

        return result

    def _alpha_008(self, df: pd.DataFrame) -> pd.Series:
        """Alpha8: 价格与成交量的交叉动量"""
        if 'open' not in df.columns or 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        open_p = df['open']
        returns = df['close'].pct_change()

        sum_open_5 = open_p.rolling(5).sum()
        sum_ret_5 = returns.rolling(5).sum()
        product = sum_open_5 * sum_ret_5
        delayed = product.shift(10)

        return -1 * (product - delayed).rank(pct=True)

    def _alpha_009(self, df: pd.DataFrame) -> pd.Series:
        """Alpha9: 基于涨跌持续性的动量"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        close = df['close']
        delta1 = close.diff(1)
        ts_min = delta1.rolling(5).min()
        ts_max = delta1.rolling(5).max()

        result = pd.Series(np.nan, index=df.index)

        cond1 = ts_min > 0
        cond2 = ts_max < 0

        result[cond1] = delta1[cond1]
        result[cond2] = delta1[cond2]
        result[~cond1 & ~cond2] = -1 * delta1[~cond1 & ~cond2]

        return result

    def _alpha_010(self, df: pd.DataFrame) -> pd.Series:
        """Alpha10: 基于涨跌持续性的动量排名"""
        alpha9 = self._alpha_009(df)
        return alpha9.rank(pct=True)

    # ===== 基础因子函数 =====

    def _roc(self, df: pd.DataFrame, period: int) -> pd.Series:
        """变动率"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)
        return df['close'].pct_change(periods=period)

    def _volatility(self, df: pd.DataFrame, period: int) -> pd.Series:
        """波动率"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)
        returns = df['close'].pct_change()
        return returns.rolling(window=period).std() * np.sqrt(252)

    def _atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """平均真实波幅"""
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        high = df['high']
        low = df['low']
        prev_close = df['close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    def _vol_ratio(self, df: pd.DataFrame, period: int) -> pd.Series:
        """量比"""
        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        volume = df[vol_col]
        ma_vol = volume.rolling(window=period).mean()
        return volume / ma_vol

    def _turnover(self, df: pd.DataFrame) -> pd.Series:
        """换手率（模拟）"""
        # 真实换手率需要股本数据，这里用成交量的相对值模拟
        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        volume = df[vol_col]
        return volume / volume.rolling(60).mean()

    def _vwap(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """成交量加权平均价"""
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return None

        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return None

        typical_price = (df['high'] + df['low'] + df['close']) / 3
        volume = df[vol_col]
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap

    def _kdj(self, df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """KDJ指标"""
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            nan_series = pd.Series([np.nan] * len(df), index=df.index)
            return nan_series, nan_series, nan_series

        high = df['high']
        low = df['low']
        close = df['close']

        low_n = low.rolling(n).min()
        high_n = high.rolling(n).max()

        rsv = (close - low_n) / (high_n - low_n).replace(0, np.nan) * 100
        k = rsv.ewm(com=m1 - 1, adjust=False).mean()
        d = k.ewm(com=m2 - 1, adjust=False).mean()
        j = 3 * k - 2 * d

        return k, d, j

    def _cci(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """CCI商品通道指标"""
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        high = df['high']
        low = df['low']
        close = df['close']

        tp = (high + low + close) / 3
        ma_tp = tp.rolling(period).mean()
        md = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean())

        cci = (tp - ma_tp) / (0.015 * md.replace(0, np.nan))
        return cci

    def _williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """威廉指标"""
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        high = df['high']
        low = df['low']
        close = df['close']

        high_n = high.rolling(period).max()
        low_n = low.rolling(period).min()

        wr = -100 * (high_n - close) / (high_n - low_n).replace(0, np.nan)
        return wr

    def _dma(self, df: pd.DataFrame, short_period: int = 10, long_period: int = 50, ama_period: int = 10) -> Tuple[pd.Series, pd.Series]:
        """DMA平均线差"""
        if 'close' not in df.columns:
            nan_series = pd.Series([np.nan] * len(df), index=df.index)
            return nan_series, nan_series

        close = df['close']
        short_ma = close.rolling(short_period).mean()
        long_ma = close.rolling(long_period).mean()
        dif = short_ma - long_ma
        ama = dif.rolling(ama_period).mean()

        return dif, ama

    def _trix(self, df: pd.DataFrame, n: int = 12, signal_period: int = 9) -> Tuple[pd.Series, pd.Series]:
        """TRIX三重指数平滑"""
        if 'close' not in df.columns:
            nan_series = pd.Series([np.nan] * len(df), index=df.index)
            return nan_series, nan_series

        close = df['close']
        ema1 = close.ewm(span=n, adjust=False).mean()
        ema2 = ema1.ewm(span=n, adjust=False).mean()
        ema3 = ema2.ewm(span=n, adjust=False).mean()
        trix = (ema3 - ema3.shift(1)) / ema3.shift(1).replace(0, np.nan) * 100
        signal = trix.ewm(span=signal_period, adjust=False).mean()

        return trix, signal

    def _mfi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """MFI资金流量指标"""
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        high = df['high']
        low = df['low']
        close = df['close']
        volume = df[vol_col]

        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume

        typical_price_shift = typical_price.shift(1)
        positive_flow = money_flow.where(typical_price > typical_price_shift, 0)
        negative_flow = money_flow.where(typical_price < typical_price_shift, 0)

        pos_sum = positive_flow.rolling(period).sum()
        neg_sum = negative_flow.rolling(period).sum()
        mfi = 100 - (100 / (1 + pos_sum / neg_sum.replace(0, np.nan)))

        return mfi

    def _obv(self, df: pd.DataFrame) -> pd.Series:
        """OBV能量潮"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        close = df['close']
        volume = df[vol_col]

        close_change = close.diff()
        direction = np.where(close_change > 0, 1, np.where(close_change < 0, -1, 0))
        obv = (volume * direction).cumsum()

        return obv

    def _ad_line(self, df: pd.DataFrame) -> pd.Series:
        """AD累积派发线"""
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        high = df['high']
        low = df['low']
        close = df['close']
        volume = df[vol_col]

        clv = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
        ad = (clv * volume).cumsum()

        return ad

    def _ad_oscillator(self, df: pd.DataFrame, fast_period: int = 3, slow_period: int = 10) -> pd.Series:
        """AD震荡指标"""
        ad = self._ad_line(df)
        ad_fast = ad.ewm(span=fast_period, adjust=False).mean()
        ad_slow = ad.ewm(span=slow_period, adjust=False).mean()
        return ad_fast - ad_slow

    def _price_volume_corr(self, df: pd.DataFrame, period: int = 10) -> pd.Series:
        """价量相关性"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        returns = df['close'].pct_change()
        volume = df[vol_col]

        corr = returns.rolling(period).corr(volume)
        return corr

    def _high_low_position(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """高低价位置"""
        if 'high' not in df.columns or 'low' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        high = df['high']
        low = df['low']

        high_n = high.rolling(period).max()
        low_n = low.rolling(period).min()

        position = (high - low_n) / (high_n - low_n).replace(0, np.nan)
        return position

    def _close_position(self, df: pd.DataFrame) -> pd.Series:
        """收盘价在日内波动中的位置"""
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        high = df['high']
        low = df['low']
        close = df['close']

        position = (close - low) / (high - low).replace(0, np.nan)
        return position

    def _volume_price_trend(self, df: pd.DataFrame) -> pd.Series:
        """量价趋势指标"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)

        close = df['close']
        volume = df[vol_col]

        returns = close.pct_change()
        vpt = (volume * returns).cumsum()
        return vpt
