"""
专业K线图绘制工具
负责绘制包含技术指标的专业K线图
"""

import mplfinance as mpf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import os

class KLineVisualizer:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.fig = None

    def plot_kline_with_indicators(self, symbol: str, indicators: List[str] = None):
        """
        绘制包含技术指标的K线图
        :param symbol: 股票代码
        :param indicators: 要显示的指标列表
        """
        if indicators is None:
            indicators = ['ma', 'volume', 'macd']

        try:
            # 准备数据
            df = self.data.copy()
            df.index = pd.to_datetime(df.index)

            # 创建子图
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.15, 0.15]
            )

            # 绘制K线主图
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='K线'
            ), row=1, col=1)

            # 绘制均线
            if 'ma' in indicators:
                for ma_period in [5, 20, 60]:
                    if len(df) >= ma_period:
                        df[f'ma{ma_period}'] = df['close'].rolling(window=ma_period).mean()
                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=df[f'ma{ma_period}'],
                            name=f'MA{ma_period}',
                            line=dict(width=1)
                        ), row=1, col=1)

            # 绘制成交量
            if 'volume' in indicators:
                # 成交量颜色区分
                colors = ['rgba(255,0,0,0.5)' if close > open else 'rgba(0,255,0,0.5)'
                         for close, open in zip(df['close'], df['open'])]

                fig.add_trace(go.Bar(
                    x=df.index,
                    y=df['volume'],
                    name='成交量',
                    marker_color=colors
                ), row=2, col=1)

            # 绘制MACD
            if 'macd' in indicators and len(df) >= 26:
                df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
                df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
                df['macd'] = df['ema12'] - df['ema26']
                df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
                df['histogram'] = df['macd'] - df['signal']

                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['macd'],
                    name='MACD',
                    line=dict(color='blue', width=1)
                ), row=3, col=1)

                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['signal'],
                    name='Signal',
                    line=dict(color='red', width=1)
                ), row=3, col=1)

                # MACD直方图
                colors = ['rgba(0,255,0,0.5)' if hist > 0 else 'rgba(255,0,0,0.5)'
                         for hist in df['histogram']]
                fig.add_trace(go.Bar(
                    x=df.index,
                    y=df['histogram'],
                    name='Histogram',
                    marker_color=colors
                ), row=3, col=1)

            # 绘制RSI
            if 'rsi' in indicators and len(df) >= 14:
                # 检查是否已经创建了第4行
                if len(fig.layout.annotations) < 4:
                    fig = make_subplots(
                        rows=4, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.02,
                        row_heights=[0.6, 0.15, 0.15, 0.1]
                    )
                    # 这里需要重新绘制前面的内容，简化处理
                    pass

            # 布局设置
            fig.update_layout(
                title=f'{symbol} 专业分析图',
                yaxis_title='价格',
                xaxis_rangeslider_visible=False,
                template='plotly_dark',
                height=800,
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1
                )
            )

            # 设置Y轴标签
            fig.update_yaxes(title_text='价格', row=1, col=1)
            fig.update_yaxes(title_text='成交量', row=2, col=1)
            fig.update_yaxes(title_text='MACD', row=3, col=1)

            self.fig = fig
            return fig

        except Exception as e:
            print(f"绘制K线图失败: {e}")
            return None

    def plot_mplfinance_kline(self, symbol: str, save_path: str = None):
        """
        使用mplfinance绘制K线图
        :param symbol: 股票代码
        :param save_path: 保存路径
        """
        try:
            df = self.data.copy()
            df.index = pd.to_datetime(df.index)

            # 添加技术指标
            apds = []

            # 均线
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma20'] = df['close'].rolling(window=20).mean()
            df['ma60'] = df['close'].rolling(window=60).mean()

            apds.append(mpf.make_addplot(df['ma5'], color='blue'))
            apds.append(mpf.make_addplot(df['ma20'], color='red'))
            apds.append(mpf.make_addplot(df['ma60'], color='green'))

            # MACD
            df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = df['ema12'] - df['ema26']
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['histogram'] = df['macd'] - df['signal']

            apds.append(mpf.make_addplot(df['macd'], panel=1, color='blue', secondary_y=False))
            apds.append(mpf.make_addplot(df['signal'], panel=1, color='red', secondary_y=False))
            apds.append(mpf.make_addplot(df['histogram'], panel=1, type='bar', color='gray', secondary_y=True))

            # 自定义样式
            mc = mpf.make_marketcolors(
                up='red', down='green',
                edge='inherit',
                wick='inherit'
            )
            s = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle='-',
                y_on_right=False
            )

            # 绘制图表
            fig, axes = mpf.plot(
                df,
                type='candle',
                volume=True,
                addplot=apds,
                style=s,
                title=f'\n{symbol} K线分析图',
                ylabel='价格',
                figratio=(16, 9),
                figscale=1.2,
                returnfig=True
            )

            # 调整布局
            fig.tight_layout()

            if save_path:
                mpf.plot(
                    df,
                    type='candle',
                    volume=True,
                    addplot=apds,
                    style=s,
                    title=f'\n{symbol} K线分析图',
                    ylabel='价格',
                    figratio=(16, 9),
                    figscale=1.2,
                    savefig=save_path
                )
                print(f"K线图已保存至: {save_path}")

            self.fig = fig
            return fig

        except Exception as e:
            print(f"mplfinance绘制K线图失败: {e}")
            return None

    def plot_trend_lines(self, trend_lines: List[Dict] = None):
        """
        绘制趋势线
        :param trend_lines: 趋势线数据列表
        """
        if trend_lines is None:
            trend_lines = self._detect_trend_lines()

        if self.fig is None:
            self.plot_kline_with_indicators('')

        try:
            for trend_line in trend_lines:
                self.fig.add_trace(go.Scatter(
                    x=pd.to_datetime(trend_line['dates']),
                    y=trend_line['prices'],
                    mode='lines',
                    name=trend_line['name'],
                    line=dict(color=trend_line.get('color', 'yellow'), width=2, dash='dash')
                ), row=1, col=1)

            return self.fig

        except Exception as e:
            print(f"绘制趋势线失败: {e}")
            return None

    def plot_chip_distribution(self, chip_data: Dict = None):
        """
        绘制筹码分布图
        :param chip_data: 筹码分布数据
        """
        if chip_data is None:
            chip_data = self._calculate_chip_distribution()

        try:
            fig = go.Figure()

            # 绘制筹码分布
            fig.add_trace(go.Bar(
                x=chip_data['price_levels'],
                y=chip_data['chip_distribution'],
                name='筹码分布',
                marker_color='rgba(50, 171, 96, 0.6)'
            ))

            # 绘制当前价格线
            fig.add_vline(
                x=self.data['close'].iloc[-1],
                line_width=2,
                line_dash='dash',
                line_color='red',
                annotation_text=f'当前价: {self.data["close"].iloc[-1]:.2f}'
            )

            # 布局设置
            fig.update_layout(
                title='筹码分布图',
                xaxis_title='价格',
                yaxis_title='筹码比例',
                template='plotly_dark',
                height=500
            )

            return fig

        except Exception as e:
            print(f"绘制筹码分布图失败: {e}")
            return None

    def save_plot(self, filename: str, format: str = 'png'):
        """
        保存图表文件
        :param filename: 文件名
        :param format: 保存格式
        """
        try:
            if self.fig is None:
                print("错误: 没有可保存的图表，请先绘制图表")
                return False

            # 创建目录
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # 保存图表
            if format == 'png':
                self.fig.write_image(filename, format='png', scale=2)
            elif format == 'jpg':
                self.fig.write_image(filename, format='jpg', scale=2)
            elif format == 'html':
                self.fig.write_html(filename)
            elif format == 'pdf':
                self.fig.write_image(filename, format='pdf', scale=2)

            print(f"图表已成功保存至: {filename}")
            return True

        except Exception as e:
            print(f"保存图表失败: {e}")
            return False

    def _detect_trend_lines(self) -> List[Dict]:
        """自动检测趋势线（简化实现）"""
        try:
            df = self.data.copy()
            trend_lines = []

            # 计算支撑线和压力线
            if len(df) >= 20:
                # 最近20天的最低价作为支撑线
                support_price = df['low'].tail(20).min()
                support_dates = [df.index[-20], df.index[-1]]
                support_prices = [support_price, support_price]

                trend_lines.append({
                    'name': '支撑线',
                    'dates': support_dates,
                    'prices': support_prices,
                    'color': 'green'
                })

                # 最近20天的最高价作为压力线
                resistance_price = df['high'].tail(20).max()
                resistance_dates = [df.index[-20], df.index[-1]]
                resistance_prices = [resistance_price, resistance_price]

                trend_lines.append({
                    'name': '压力线',
                    'dates': resistance_dates,
                    'prices': resistance_prices,
                    'color': 'red'
                })

            return trend_lines

        except Exception as e:
            print(f"趋势线检测失败: {e}")
            return []

    def _calculate_chip_distribution(self) -> Dict:
        """计算筹码分布（简化实现）"""
        try:
            df = self.data.tail(60).copy()
            prices = np.linspace(df['low'].min(), df['high'].max(), 50)

            # 简单的筹码分布计算
            chip_distribution = []
            for price in prices:
                # 计算在该价格附近的成交量占比
                volume_at_price = df[abs(df['close'] - price) < (df['high'].max() - df['low'].min())/20]['volume'].sum()
                chip_distribution.append(volume_at_price)

            # 归一化
            total = sum(chip_distribution)
            if total > 0:
                chip_distribution = [x / total for x in chip_distribution]

            return {
                'price_levels': prices,
                'chip_distribution': chip_distribution,
                'avg_cost': (df['close'] * df['volume']).sum() / df['volume'].sum(),
                'update_time': datetime.now()
            }

        except Exception as e:
            print(f"计算筹码分布失败: {e}")
            return {}

if __name__ == "__main__":
    # 测试代码
    import pandas as pd
    import numpy as np

    # 创建模拟数据
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    close = np.cumsum(np.random.randn(100)) + 100
    high = close + np.random.rand(100) * 5
    low = close - np.random.rand(100) * 5
    open = close + np.random.randn(100) * 2
    volume = np.random.randint(1000, 5000, size=100)

    df = pd.DataFrame({
        'open': open,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)

    # 测试可视化
    visualizer = KLineVisualizer(df)
    fig = visualizer.plot_kline_with_indicators('000001')

    # 保存图表
    visualizer.save_plot('test_kline.png')

    # 测试筹码分布
    chip_fig = visualizer.plot_chip_distribution()
    if chip_fig:
        chip_fig.write_image('test_chip.png')