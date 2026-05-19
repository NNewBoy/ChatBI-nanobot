import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def plot_arima_forecast(hist_df, forecast_dates, forecast_values, stock_name, ts_code, save_path):
    fig, ax = plt.subplots(figsize=(14, 6))

    recent = hist_df.tail(60).copy()
    ax.plot(recent['trade_date'], recent['close'], color='#2196F3', linewidth=1.5, label='历史收盘价')

    ax.plot(forecast_dates, forecast_values, color='#FF5722', linewidth=2, marker='o', markersize=5, label='ARIMA预测')

    last_hist_date = recent['trade_date'].iloc[-1]
    last_hist_close = recent['close'].iloc[-1]
    ax.plot([last_hist_date, forecast_dates[0]], [last_hist_close, forecast_values[0]],
            color='#FF5722', linewidth=2, linestyle='--')

    ax.axvline(x=last_hist_date, color='gray', linestyle=':', alpha=0.7, label='预测起点')

    ax.fill_between(forecast_dates, forecast_values * 0.97, forecast_values * 1.03,
                    color='#FF5722', alpha=0.15, label='预测区间(±3%)')

    ax.set_title(f'{stock_name}({ts_code}) ARIMA(5,1,5) 收盘价预测', fontsize=14)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('收盘价', fontsize=12)
    ax.legend(loc='best', fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    all_dates = pd.concat([recent['trade_date'].reset_index(drop=True), pd.Series(forecast_dates)]).reset_index(drop=True)
    n = len(all_dates)
    if n > 10:
        tick_indices = np.linspace(0, n - 1, 10, dtype=int)
        ax.set_xticks(all_dates.iloc[tick_indices])

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
