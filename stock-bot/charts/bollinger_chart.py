import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def plot_bollinger(df, overbought, oversold, stock_name, ts_code, window, num_std, save_path):
    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(df['trade_date'], df['close'], color='#2196F3', linewidth=1.2, label='收盘价')
    ax.plot(df['trade_date'], df['ma'], color='#FF9800', linewidth=1.2, label=f'MA{window}')
    ax.plot(df['trade_date'], df['upper'], color='#F44336', linewidth=1, linestyle='--', label=f'上轨(+{num_std}σ)')
    ax.plot(df['trade_date'], df['lower'], color='#4CAF50', linewidth=1, linestyle='--', label=f'下轨(-{num_std}σ)')

    ax.fill_between(df['trade_date'], df['upper'], df['lower'], alpha=0.08, color='#FF9800')

    if not overbought.empty:
        ax.scatter(overbought['trade_date'], overbought['close'],
                   color='#F44336', s=50, zorder=5, marker='v', label=f'超买({len(overbought)}天)')
    if not oversold.empty:
        ax.scatter(oversold['trade_date'], oversold['close'],
                   color='#4CAF50', s=50, zorder=5, marker='^', label=f'超卖({len(oversold)}天)')

    ax.set_title(f'{stock_name}({ts_code}) 布林带({window}日±{num_std}σ) 异常检测', fontsize=14)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('价格', fontsize=12)
    ax.legend(loc='best', fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    x_values = df['trade_date'].reset_index(drop=True)
    n = len(x_values)
    if n > 10:
        tick_indices = np.linspace(0, n - 1, 10, dtype=int)
        ax.set_xticks(x_values.iloc[tick_indices])

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
