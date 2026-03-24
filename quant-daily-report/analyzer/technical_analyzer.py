"""
技术指标计算引擎
负责计算各种技术指标并生成交易信号
"""

import talib
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class TechnicalAnalyzer:
    def __init__(self, kline_data: pd.DataFrame):
        self.kline_data = kline_data
        self.close = kline_data['close'].values if 'close' in kline_data else np.array([])
        self.high = kline_data['high'].values if 'high' in kline_data else np.array([])
        self.low = kline_data['low'].values if 'low' in kline_data else np.array([])
        self.volume = kline_data['volume'].values if 'volume' in kline_data else np.array([])

    def calculate_all_indicators(self) -> Dict:
        """计算所有技术指标"""
        try:
            indicators = {}

            # 趋势指标
            indicators.update(self.calculate_trend_indicators())

            # 震荡指标
            indicators.update(self.calculate_oscillators())

            # 成交量指标
            indicators.update(self.calculate_volume_indicators())

            # 波动性指标
            indicators.update(self.calculate_volatility_indicators())

            # 模式识别
            indicators.update(self.calculate_pattern_recognition())

            return indicators

        except Exception as e:
            print(f"技术指标计算失败: {e}")
            return {}

    def calculate_trend_indicators(self) -> Dict:
        """计算趋势指标"""
        try:
            indicators = {}

            # 移动平均线
            if len(self.close) >= 60:
                indicators['ma5'] = talib.SMA(self.close, timeperiod=5)
                indicators['ma10'] = talib.SMA(self.close, timeperiod=10)
                indicators['ma20'] = talib.SMA(self.close, timeperiod=20)
                indicators['ma60'] = talib.SMA(self.close, timeperiod=60)
                indicators['ma120'] = talib.SMA(self.close, timeperiod=120)

                # 指数移动平均线
                indicators['ema5'] = talib.EMA(self.close, timeperiod=5)
                indicators['ema10'] = talib.EMA(self.close, timeperiod=10)
                indicators['ema20'] = talib.EMA(self.close, timeperiod=20)

            # MACD
            if len(self.close) >= 34:
                macd, macdsignal, macdhist = talib.MACD(self.close)
                indicators['macd'] = macd
                indicators['macdsignal'] = macdsignal
                indicators['macdhist'] = macdhist

            # 布林带
            if len(self.close) >= 20:
                upper, middle, lower = talib.BBANDS(self.close)
                indicators['bb_upper'] = upper
                indicators['bb_middle'] = middle
                indicators['bb_lower'] = lower
                indicators['bb_width'] = upper - lower
                indicators['bb_percent'] = (self.close - lower) / (upper - lower)

            # 动向指标(DMI)
            if len(self.close) >= 14:
                plus_di, minus_di, dx = talib.DX(self.high, self.low, self.close)
                indicators['plus_di'] = plus_di
                indicators['minus_di'] = minus_di
                indicators['dx'] = dx

            # 抛物线指标(SAR)
            if len(self.close) >= 5:
                sar = talib.SAR(self.high, self.low)
                indicators['sar'] = sar

            # 计算趋势信号
            indicators['trend_signals'] = self._analyze_trend_signals(indicators)

            return indicators

        except Exception as e:
            print(f"趋势指标计算失败: {e}")
            return {}

    def calculate_oscillators(self) -> Dict:
        """计算震荡指标"""
        try:
            indicators = {}

            # RSI
            if len(self.close) >= 14:
                indicators['rsi6'] = talib.RSI(self.close, timeperiod=6)
                indicators['rsi12'] = talib.RSI(self.close, timeperiod=12)
                indicators['rsi24'] = talib.RSI(self.close, timeperiod=24)

            # 随机指标(KDJ)
            if len(self.close) >= 9:
                slowk, slowd = talib.STOCH(self.high, self.low, self.close)
                indicators['kdj_k'] = slowk
                indicators['kdj_d'] = slowd
                indicators['kdj_j'] = 3 * slowk - 2 * slowd

            # 顺势指标(CCI)
            if len(self.close) >= 20:
                indicators['cci'] = talib.CCI(self.high, self.low, self.close)

            # 威廉指标(Williams %R)
            if len(self.close) >= 14:
                indicators['willr'] = talib.WILLR(self.high, self.low, self.close)

            # 动量指标(MTM)
            if len(self.close) >= 10:
                indicators['mom'] = talib.MOM(self.close, timeperiod=10)

            # 计算震荡信号
            indicators['oscillator_signals'] = self._analyze_oscillator_signals(indicators)

            return indicators

        except Exception as e:
            print(f"震荡指标计算失败: {e}")
            return {}

    def calculate_volume_indicators(self) -> Dict:
        """计算成交量指标"""
        try:
            indicators = {}

            # 成交量均线
            if len(self.volume) >= 20:
                indicators['volume_ma5'] = talib.SMA(self.volume, timeperiod=5)
                indicators['volume_ma10'] = talib.SMA(self.volume, timeperiod=10)
                indicators['volume_ma20'] = talib.SMA(self.volume, timeperiod=20)

            # 能量潮(OBV)
            if len(self.close) >= 2:
                indicators['obv'] = talib.OBV(self.close, self.volume)

            # 成交量比率(VR)
            if len(self.close) >= 24:
                # VR指标需要自己计算
                up = self.volume[self.close > np.roll(self.close, 1)]
                down = self.volume[self.close < np.roll(self.close, 1)]
                vr = np.cumsum(up) / np.cumsum(down)
                indicators['vr'] = vr

            # 计算成交量信号
            indicators['volume_signals'] = self._analyze_volume_signals(indicators)

            return indicators

        except Exception as e:
            print(f"成交量指标计算失败: {e}")
            return {}

    def calculate_volatility_indicators(self) -> Dict:
        """计算波动性指标"""
        try:
            indicators = {}

            # 平均真实波幅(ATR)
            if len(self.close) >= 14:
                indicators['atr'] = talib.ATR(self.high, self.low, self.close)

            # 历史波动率
            if len(self.close) >= 30:
                log_returns = np.log(self.close[1:] / self.close[:-1])
                indicators['historical_vol'] = np.std(log_returns) * np.sqrt(252)

            # 计算波动性信号
            indicators['volatility_signals'] = self._analyze_volatility_signals(indicators)

            return indicators

        except Exception as e:
            print(f"波动性指标计算失败: {e}")
            return {}

    def calculate_pattern_recognition(self) -> Dict:
        """计算形态识别"""
        try:
            indicators = {}

            # 蜡烛图形态识别
            if len(self.close) >= 10:
                # 早晨之星
                indicators['morning_star'] = talib.CDLMORNINGSTAR(self.open, self.high, self.low, self.close)
                # 黄昏之星
                indicators['evening_star'] = talib.CDLEVENINGSTAR(self.open, self.high, self.low, self.close)
                # 锤头线
                indicators['hammer'] = talib.CDLHAMMER(self.open, self.high, self.low, self.close)
                # 倒锤头线
                indicators['inverted_hammer'] = talib.CDLINVERTEDHAMMER(self.open, self.high, self.low, self.close)
                # 吞没形态
                indicators['engulfing'] = talib.CDLENGULFING(self.open, self.high, self.low, self.close)
                # 十字星
                indicators['doji'] = talib.CDLDOJI(self.open, self.high, self.low, self.close)

            # 计算形态信号
            indicators['pattern_signals'] = self._analyze_pattern_signals(indicators)

            return indicators

        except Exception as e:
            print(f"形态识别计算失败: {e}")
            return {}

    def generate_trading_signals(self) -> Dict:
        """生成交易信号"""
        try:
            indicators = self.calculate_all_indicators()
            signals = []

            # 分析趋势信号
            trend_signals = indicators.get('trend_signals', [])
            signals.extend(trend_signals)

            # 分析震荡信号
            oscillator_signals = indicators.get('oscillator_signals', [])
            signals.extend(oscillator_signals)

            # 分析成交量信号
            volume_signals = indicators.get('volume_signals', [])
            signals.extend(volume_signals)

            # 分析形态信号
            pattern_signals = indicators.get('pattern_signals', [])
            signals.extend(pattern_signals)

            # 综合信号
            bullish_signals = [s for s in signals if s['signal_type'] == 'buy']
            bearish_signals = [s for s in signals if s['signal_type'] == 'sell']

            # 计算信号强度
            signal_strength = self._calculate_signal_strength(bullish_signals, bearish_signals)

            return {
                'all_signals': signals,
                'bullish_signals_count': len(bullish_signals),
                'bearish_signals_count': len(bearish_signals),
                'signal_strength': signal_strength,
                'final_signal': self._get_final_signal(signal_strength),
                'confidence': self._calculate_confidence(signals)
            }

        except Exception as e:
            print(f"交易信号生成失败: {e}")
            return {}

    def _analyze_trend_signals(self, indicators: Dict) -> List[Dict]:
        """分析趋势信号"""
        signals = []

        # 均线金叉死叉
        if 'ma5' in indicators and 'ma20' in indicators:
            ma5 = indicators['ma5']
            ma20 = indicators['ma20']

            if not np.isnan(ma5[-1]) and not np.isnan(ma20[-1]):
                # 金叉
                if ma5[-2] < ma20[-2] and ma5[-1] > ma20[-1]:
                    signals.append({
                        'indicator': 'MA',
                        'signal_type': 'buy',
                        'signal': 'MA5上穿MA20 金叉',
                        'strength': 70,
                        'price': self.close[-1]
                    })
                # 死叉
                elif ma5[-2] > ma20[-2] and ma5[-1] < ma20[-1]:
                    signals.append({
                        'indicator': 'MA',
                        'signal_type': 'sell',
                        'signal': 'MA5下穿MA20 死叉',
                        'strength': 70,
                        'price': self.close[-1]
                    })

        # MACD金叉死叉
        if 'macd' in indicators and 'macdsignal' in indicators:
            macd = indicators['macd']
            signal = indicators['macdsignal']

            if not np.isnan(macd[-1]) and not np.isnan(signal[-1]):
                # 金叉
                if macd[-2] < signal[-2] and macd[-1] > signal[-1]:
                    signals.append({
                        'indicator': 'MACD',
                        'signal_type': 'buy',
                        'signal': 'MACD金叉',
                        'strength': 65,
                        'price': self.close[-1]
                    })
                # 死叉
                elif macd[-2] > signal[-2] and macd[-1] < signal[-1]:
                    signals.append({
                        'indicator': 'MACD',
                        'signal_type': 'sell',
                        'signal': 'MACD死叉',
                        'strength': 65,
                        'price': self.close[-1]
                    })

        return signals

    def _analyze_oscillator_signals(self, indicators: Dict) -> List[Dict]:
        """分析震荡信号"""
        signals = []

        # RSI超买超卖
        if 'rsi12' in indicators:
            rsi = indicators['rsi12'][-1]

            if not np.isnan(rsi):
                if rsi < 20:
                    signals.append({
                        'indicator': 'RSI',
                        'signal_type': 'buy',
                        'signal': 'RSI超卖',
                        'strength': 60,
                        'price': self.close[-1]
                    })
                elif rsi > 80:
                    signals.append({
                        'indicator': 'RSI',
                        'signal_type': 'sell',
                        'signal': 'RSI超买',
                        'strength': 60,
                        'price': self.close[-1]
                    })

        # KDJ信号
        if 'kdj_k' in indicators and 'kdj_d' in indicators:
            k = indicators['kdj_k'][-1]
            d = indicators['kdj_d'][-1]

            if not np.isnan(k) and not np.isnan(d):
                if k < 20 and d < 20 and k > d:
                    signals.append({
                        'indicator': 'KDJ',
                        'signal_type': 'buy',
                        'signal': 'KDJ超卖区金叉',
                        'strength': 65,
                        'price': self.close[-1]
                    })
                elif k > 80 and d > 80 and k < d:
                    signals.append({
                        'indicator': 'KDJ',
                        'signal_type': 'sell',
                        'signal': 'KDJ超买区死叉',
                        'strength': 65,
                        'price': self.close[-1]
                    })

        return signals

    def _analyze_volume_signals(self, indicators: Dict) -> List[Dict]:
        """分析成交量信号"""
        signals = []

        # OBV分析
        if 'obv' in indicators:
            obv = indicators['obv']
            close = self.close

            if len(obv) >= 2:
                # OBV与价格背离
                if close[-1] > close[-5] and obv[-1] < obv[-5]:
                    signals.append({
                        'indicator': 'OBV',
                        'signal_type': 'sell',
                        'signal': '量价背离 看跌',
                        'strength': 75,
                        'price': self.close[-1]
                    })
                elif close[-1] < close[-5] and obv[-1] > obv[-5]:
                    signals.append({
                        'indicator': 'OBV',
                        'signal_type': 'buy',
                        'signal': '量价背离 看涨',
                        'strength': 75,
                        'price': self.close[-1]
                    })

        return signals

    def _analyze_volatility_signals(self, indicators: Dict) -> List[Dict]:
        """分析波动性信号"""
        signals = []

        # 布林带信号
        if 'bb_lower' in indicators and 'bb_upper' in indicators:
            bb_lower = indicators['bb_lower'][-1]
            bb_upper = indicators['bb_upper'][-1]
            price = self.close[-1]

            if not np.isnan(bb_lower) and not np.isnan(bb_upper):
                if price < bb_lower:
                    signals.append({
                        'indicator': '布林带',
                        'signal_type': 'buy',
                        'signal': '价格触及下轨 超卖',
                        'strength': 60,
                        'price': price
                    })
                elif price > bb_upper:
                    signals.append({
                        'indicator': '布林带',
                        'signal_type': 'sell',
                        'signal': '价格触及上轨 超买',
                        'strength': 60,
                        'price': price
                    })

        return signals

    def _analyze_pattern_signals(self, indicators: Dict) -> List[Dict]:
        """分析形态信号"""
        signals = []

        # 蜡烛图形态
        pattern_weights = {
            'morning_star': {'buy': 80},
            'evening_star': {'sell': 80},
            'hammer': {'buy': 70},
            'inverted_hammer': {'buy': 70},
            'engulfing': {'buy': 75, 'sell': 75}
        }

        for pattern, weights in pattern_weights.items():
            if pattern in indicators:
                pattern_value = indicators[pattern][-1]
                if pattern_value != 0:
                    if pattern_value > 0 and 'buy' in weights:
                        signals.append({
                            'indicator': 'K线形态',
                            'signal_type': 'buy',
                            'signal': f'{pattern} 看涨形态',
                            'strength': weights['buy'],
                            'price': self.close[-1]
                        })
                    elif pattern_value < 0 and 'sell' in weights:
                        signals.append({
                            'indicator': 'K线形态',
                            'signal_type': 'sell',
                            'signal': f'{pattern} 看跌形态',
                            'strength': weights['sell'],
                            'price': self.close[-1]
                        })

        return signals

    def _calculate_signal_strength(self, bullish_signals: List[Dict], bearish_signals: List[Dict]) -> float:
        """计算信号强度"""
        bullish_strength = sum(signal.get('strength', 0) for signal in bullish_signals)
        bearish_strength = sum(signal.get('strength', 0) for signal in bearish_signals)

        return bullish_strength - bearish_strength

    def _get_final_signal(self, signal_strength: float) -> str:
        """获取最终信号"""
        if signal_strength > 100:
            return "强烈买入"
        elif signal_strength > 30:
            return "买入"
        elif signal_strength < -100:
            return "强烈卖出"
        elif signal_strength < -30:
            return "卖出"
        else:
            return "观望"

    def _calculate_confidence(self, signals: List[Dict]) -> float:
        """计算信号置信度"""
        if not signals:
            return 0.0

        valid_signals = [s for s in signals if not np.isnan(s.get('strength', 0))]
        confidence = sum(s.get('strength', 0) for s in valid_signals) / len(valid_signals)
        return confidence

if __name__ == "__main__":
    # 测试代码
    import pandas as pd
    import numpy as np

    # 创建模拟数据
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    close = np.cumsum(np.random.randn(100)) + 100
    high = close + np.random.rand(100) * 5
    low = close - np.random.rand(100) * 5
    volume = np.random.randint(1000, 5000, size=100)

    kline_data = pd.DataFrame({
        'date': dates,
        'open': close,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    kline_data.set_index('date', inplace=True)

    analyzer = TechnicalAnalyzer(kline_data)
    indicators = analyzer.calculate_all_indicators()
    print(f"计算得到 {len(indicators)} 个技术指标")

    signals = analyzer.generate_trading_signals()
    print(f"\n最终交易信号: {signals['final_signal']}")
    print(f"信号强度: {signals['signal_strength']}")
    print(f"置信度: {signals['confidence']:.1f}%")
    print(f"看涨信号: {signals['bullish_signals_count']} 个")
    print(f"看跌信号: {signals['bearish_signals_count']} 个")