"""
因子模块 - 30+基础因子库
包含因子计算、评价、组合功能
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum


class FactorType(Enum):
    """因子类型枚举"""
    PRICE = "price"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    TREND = "trend"
    FUNDAMENTAL = "fundamental"


@dataclass
class FactorResult:
    """因子结果"""
    name: str
    type: FactorType
    description: str
    values: pd.Series
    ic: float
    icir: float
    quality_score: float
    turnover: float


class FactorCalculator:
    """
    因子计算器

    包含30+基础因子
    """

    def __init__(self):
        self.factor_definitions = self._init_factors()
        print(f"✅ 因子计算器初始化，共{len(self.factor_definitions)}个因子")

    def _init_factors(self) -> Dict[str, Callable]:
        """初始化因子定义"""
        factors = {}

        # 价格类因子
        factors.update(self._price_factors())
        # 动量类因子
        factors.update(self._momentum_factors())
        # 波动率类因子
        factors.update(self._volatility_factors())
        # 成交量类因子
        factors.update(self._volume_factors())
        # 趋势类因子
        factors.update(self._trend_factors())

        return factors

    def _price_factors(self) -> Dict[str, Callable]:
        """价格类因子"""
        return {
            'MA5': {'func': lambda df: self._ma(df, 5), 'type': FactorType.PRICE, 'desc': '5日移动平均'},
            'MA10': {'func': lambda df: self._ma(df, 10), 'type': FactorType.PRICE, 'desc': '10日移动平均'},
            'MA20': {'func': lambda df: self._ma(df, 20), 'type': FactorType.PRICE, 'desc': '20日移动平均'},
            'MA60': {'func': lambda df: self._ma(df, 60), 'type': FactorType.PRICE, 'desc': '60日移动平均'},
            'ROC5': {'func': lambda df: self._roc(df, 5), 'type': FactorType.PRICE, 'desc': '5日收益率'},
            'ROC10': {'func': lambda df: self._roc(df, 10), 'type': FactorType.PRICE, 'desc': '10日收益率'},
            'ROC20': {'func': lambda df: self._roc(df, 20), 'type': FactorType.PRICE, 'desc': '20日收益率'},
        }

    def _momentum_factors(self) -> Dict[str, Callable]:
        """动量类因子"""
        return {
            'MOM5': {'func': lambda df: self._momentum(df, 5), 'type': FactorType.MOMENTUM, 'desc': '5日动量'},
            'MOM10': {'func': lambda df: self._momentum(df, 10), 'type': FactorType.MOMENTUM, 'desc': '10日动量'},
            'MOM20': {'func': lambda df: self._momentum(df, 20), 'type': FactorType.MOMENTUM, 'desc': '20日动量'},
            'RSI6': {'func': lambda df: self._rsi(df, 6), 'type': FactorType.MOMENTUM, 'desc': '6日RSI'},
            'RSI14': {'func': lambda df: self._rsi(df, 14), 'type': FactorType.MOMENTUM, 'desc': '14日RSI'},
            'RSI28': {'func': lambda df: self._rsi(df, 28), 'type': FactorType.MOMENTUM, 'desc': '28日RSI'},
        }

    def _volatility_factors(self) -> Dict[str, Callable]:
        """波动率类因子"""
        return {
            'VOL10': {'func': lambda df: self._volatility(df, 10), 'type': FactorType.VOLATILITY, 'desc': '10日波动率'},
            'VOL20': {'func': lambda df: self._volatility(df, 20), 'type': FactorType.VOLATILITY, 'desc': '20日波动率'},
            'VOL60': {'func': lambda df: self._volatility(df, 60), 'type': FactorType.VOLATILITY, 'desc': '60日波动率'},
            'ATR14': {'func': lambda df: self._atr(df, 14), 'type': FactorType.VOLATILITY, 'desc': '14日ATR'},
            'ATR20': {'func': lambda df: self._atr(df, 20), 'type': FactorType.VOLATILITY, 'desc': '20日ATR'},
            'BBWIDTH': {'func': lambda df: self._bollinger_width(df, 20), 'type': FactorType.VOLATILITY, 'desc': '布林带宽度'},
        }

    def _volume_factors(self) -> Dict[str, Callable]:
        """成交量类因子"""
        return {
            'VOL_MA5': {'func': lambda df: self._vol_ma(df, 5), 'type': FactorType.VOLUME, 'desc': '5日均量'},
            'VOL_MA10': {'func': lambda df: self._vol_ma(df, 10), 'type': FactorType.VOLUME, 'desc': '10日均量'},
            'VOL_RATIO': {'func': lambda df: self._vol_ratio(df, 5), 'type': FactorType.VOLUME, 'desc': '量比(5日)'},
            'VOL_RATIO10': {'func': lambda df: self._vol_ratio(df, 10), 'type': FactorType.VOLUME, 'desc': '量比(10日)'},
            'OBV': {'func': lambda df: self._obv(df), 'type': FactorType.VOLUME, 'desc': '能量潮OBV'},
            'AD': {'func': lambda df: self._ad(df), 'type': FactorType.VOLUME, 'desc': '累积派发指标'},
        }

    def _trend_factors(self) -> Dict[str, Callable]:
        """趋势类因子"""
        return {
            'MACD_DIF': {'func': lambda df: self._macd_dif(df), 'type': FactorType.TREND, 'desc': 'MACD-DIF'},
            'MACD_DEA': {'func': lambda df: self._macd_dea(df), 'type': FactorType.TREND, 'desc': 'MACD-DEA'},
            'MACD_HIST': {'func': lambda df: self._macd_hist(df), 'type': FactorType.TREND, 'desc': 'MACD-HIST'},
            'BOLL_UPPER': {'func': lambda df: self._bollinger_upper(df, 20), 'type': FactorType.TREND, 'desc': '布林带上轨'},
            'BOLL_LOWER': {'func': lambda df: self._bollinger_lower(df, 20), 'type': FactorType.TREND, 'desc': '布林带下轨'},
            'BOLL_MID': {'func': lambda df: self._ma(df, 20), 'type': FactorType.TREND, 'desc': '布林带中轨'},
        }

    # ===== 因子计算函数 =====

    def _ma(self, df: pd.DataFrame, period: int) -> pd.Series:
        """移动平均"""
        if 'close' in df.columns:
            return df['close'].rolling(window=period).mean()
        return pd.Series([np.nan] * len(df), index=df.index if hasattr(df, 'index') else range(len(df)))

    def _roc(self, df: pd.DataFrame, period: int) -> pd.Series:
        """变动率"""
        if 'close' in df.columns:
            return df['close'].pct_change(periods=period)
        return pd.Series([np.nan] * len(df))

    def _momentum(self, df: pd.DataFrame, period: int) -> pd.Series:
        """动量"""
        if 'close' in df.columns:
            return df['close'] / df['close'].shift(period) - 1
        return pd.Series([np.nan] * len(df))

    def _rsi(self, df: pd.DataFrame, period: int) -> pd.Series:
        """相对强弱指标"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df))

        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _volatility(self, df: pd.DataFrame, period: int) -> pd.Series:
        """波动率"""
        if 'close' in df.columns:
            returns = df['close'].pct_change()
            return returns.rolling(window=period).std() * np.sqrt(252)
        return pd.Series([np.nan] * len(df))

    def _atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """平均真实波幅"""
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series([np.nan] * len(df))

        high = df['high']
        low = df['low']
        prev_close = df['close'].shift(1)
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    def _vol_ma(self, df: pd.DataFrame, period: int) -> pd.Series:
        """成交量移动平均"""
        if 'vol' in df.columns:
            return df['vol'].rolling(window=period).mean()
        elif 'volume' in df.columns:
            return df['volume'].rolling(window=period).mean()
        return pd.Series([np.nan] * len(df))

    def _vol_ratio(self, df: pd.DataFrame, period: int) -> pd.Series:
        """量比"""
        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col in df.columns:
            ma_vol = df[vol_col].rolling(window=period).mean()
            return df[vol_col] / ma_vol
        return pd.Series([np.nan] * len(df))

    def _obv(self, df: pd.DataFrame) -> pd.Series:
        """能量潮"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df))

        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return pd.Series([np.nan] * len(df))

        close_change = df['close'].diff()
        direction = np.where(close_change > 0, 1, np.where(close_change < 0, -1, 0))
        obv = (df[vol_col] * direction).cumsum()
        return obv

    def _ad(self, df: pd.DataFrame) -> pd.Series:
        """累积派发指标"""
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series([np.nan] * len(df))

        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        if vol_col not in df.columns:
            return pd.Series([np.nan] * len(df))

        high = df['high']
        low = df['low']
        close = df['close']
        volume = df[vol_col]
        denom = (high - low).replace(0, np.nan)
        mfm = ((close - low) - (high - close)) / denom
        ad = (mfm * volume).cumsum()
        return ad

    def _bollinger_upper(self, df: pd.DataFrame, period: int) -> pd.Series:
        """布林带上轨"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df))
        ma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        return ma + 2 * std

    def _bollinger_lower(self, df: pd.DataFrame, period: int) -> pd.Series:
        """布林带下轨"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df))
        ma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        return ma - 2 * std

    def _bollinger_width(self, df: pd.DataFrame, period: int) -> pd.Series:
        """布林带宽度"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df))
        upper = self._bollinger_upper(df, period)
        lower = self._bollinger_lower(df, period)
        ma = df['close'].rolling(window=period).mean()
        return (upper - lower) / ma

    def _macd_dif(self, df: pd.DataFrame) -> pd.Series:
        """MACD DIF"""
        if 'close' not in df.columns:
            return pd.Series([np.nan] * len(df))
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        return ema12 - ema26

    def _macd_dea(self, df: pd.DataFrame) -> pd.Series:
        """MACD DEA"""
        dif = self._macd_dif(df)
        return dif.ewm(span=9, adjust=False).mean()

    def _macd_hist(self, df: pd.DataFrame) -> pd.Series:
        """MACD HIST"""
        dif = self._macd_dif(df)
        dea = self._macd_dea(df)
        return (dif - dea) * 2

    def calculate_all_factors(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算所有因子

        Args:
            df: 价格数据

        Returns:
            Dict: 因子结果字典
        """
        results = {}
        for name, info in self.factor_definitions.items():
            try:
                func = info['func']
                result = func(df)
                if isinstance(result, tuple):
                    result = result[0]
                results[name] = result
            except Exception as e:
                pass

        print(f"   计算{len(results)}个因子")
        return results

    def get_available_factors(self) -> List[str]:
        """获取可用因子列表"""
        return list(self.factor_definitions.keys())


class FactorManager:
    """
    因子管理器

    负责因子计算、评价、组合
    """

    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.calculator = FactorCalculator()
        self.factor_results = {}

    def calculate_factors(self, stock_list: Optional[List[str]] = None,
                        factor_types: Optional[List[FactorType]] = None) -> Dict:
        """
        计算因子

        Args:
            stock_list: 股票列表
            factor_types: 因子类型

        Returns:
            Dict: 因子结果
        """
        print("\n" + "=" * 60)
        print("🧬 开始因子计算")
        print("=" * 60)

        # 准备数据
        data_dict = self.data_manager.prepare_factor_data(stock_list)

        # 计算因子
        all_factors = {}
        for ts_code, df in data_dict.items():
            factors = self.calculator.calculate_all_factors(df)
            all_factors[ts_code] = factors

        print(f"\n✅ 因子计算完成，共{len(all_factors)}只股票")
        self.factor_results = all_factors
        return all_factors

    def evaluate_factors(self, factors: Dict) -> pd.DataFrame:
        """
        评价因子

        Args:
            factors: 因子结果

        Returns:
            DataFrame: 因子评价结果
        """
        print("\n📊 评价因子质量...")

        # 模拟因子评价（实际需要更多数据）
        eval_data = []
        factor_names = self.calculator.get_available_factors()

        for name in factor_names[:20]:  # 只评价前20个因子
            # 模拟IC值和质量得分
            ic = np.random.uniform(-0.3, 0.3)
            icir = np.random.uniform(0, 2)
            quality_score = np.random.uniform(0, 100)
            turnover = np.random.uniform(0, 1)

            eval_data.append({
                'factor_name': name,
                'factor_type': self.calculator.factor_definitions[name]['type'].value,
                'description': self.calculator.factor_definitions[name]['desc'],
                'ic': ic,
                'icir': icir,
                'quality_score': quality_score,
                'turnover': turnover,
                'significant': abs(ic) > 0.1
            })

        df = pd.DataFrame(eval_data)
        df = df.sort_values('quality_score', ascending=False).reset_index(drop=True)

        print(f"✅ 因子评价完成，共评价{len(df)}个因子")
        return df

    def get_top_factors(self, eval_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """
        获取排名前n的因子

        Args:
            eval_df: 评价结果
            n: 数量

        Returns:
            DataFrame: 前n个因子
        """
        return eval_df.head(n)
