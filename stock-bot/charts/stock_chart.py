import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def set_sparse_xticks(ax, x_values, max_ticks=10):
    n = len(x_values)
    if n <= max_ticks:
        ax.set_xticks(x_values)
        return
    tick_indices = np.linspace(0, n - 1, max_ticks, dtype=int)
    if hasattr(x_values, 'iloc'):
        ax.set_xticks(x_values.iloc[tick_indices])
    else:
        ax.set_xticks([x_values[i] for i in tick_indices])


def sample_x_axis(df, x_col, max_points=10):
    n = len(df)
    if n <= max_points:
        return df
    indices = np.linspace(0, n - 1, max_points, dtype=int)
    return df.iloc[indices].copy()


def generate_stock_chart(df_sql, save_path):
    columns = df_sql.columns.tolist()
    num_columns = df_sql.select_dtypes(include='number').columns.tolist()
    date_columns = []
    for col in columns:
        if df_sql[col].dtype == 'object':
            try:
                pd.to_datetime(df_sql[col])
                date_columns.append(col)
            except (ValueError, TypeError):
                pass
        elif pd.api.types.is_datetime64_any_dtype(df_sql[col]):
            date_columns.append(col)

    x_col = None
    if date_columns:
        x_col = date_columns[0]
    elif columns:
        x_col = columns[0]

    stock_name_col = None
    for c in columns:
        if c.lower() == 'stock_name':
            stock_name_col = c
            break

    has_stock_name = stock_name_col is not None

    if has_stock_name and x_col and len(num_columns) > 0:
        _plot_multi_series(df_sql, x_col, stock_name_col, num_columns, save_path)
    elif x_col and len(num_columns) > 0:
        _plot_single_series(df_sql, x_col, num_columns, save_path)
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, '数据无法自动生成图表', ha='center', va='center', fontsize=16)
        ax.set_title("提示")
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()


def _plot_multi_series(df_sql, x_col, stock_name_col, num_columns, save_path):
    df_plot = df_sql.copy()
    try:
        df_plot[x_col] = pd.to_datetime(df_plot[x_col])
    except (ValueError, TypeError):
        pass

    stock_names = df_plot[stock_name_col].unique()
    plot_cols = [c for c in num_columns if c != stock_name_col]

    if not plot_cols:
        return

    primary_col = plot_cols[0]
    is_price = any(kw in primary_col.lower() for kw in ['open', 'high', 'low', 'close', 'pre_close', 'price'])

    n = len(df_plot)
    use_line = n > 10 or is_price

    fig, ax1 = plt.subplots(figsize=(12, 6))

    if use_line:
        for name in stock_names:
            subset = df_plot[df_plot[stock_name_col] == name].sort_values(x_col)
            ax1.plot(subset[x_col], subset[primary_col], marker='o', markersize=2, label=str(name))
        ax1.set_ylabel(primary_col)
        ax1.set_title(f"{' / '.join([str(n) for n in stock_names])} - {primary_col}走势")
        if pd.api.types.is_datetime64_any_dtype(df_plot[x_col]):
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        set_sparse_xticks(ax1, df_plot.sort_values(x_col)[x_col].reset_index(drop=True))
    else:
        for name in stock_names:
            subset = df_plot[df_plot[stock_name_col] == name].sort_values(x_col)
            subset_sampled = sample_x_axis(subset, x_col)
            ax1.bar(subset_sampled[x_col], subset_sampled[primary_col], label=str(name), alpha=0.7)
        ax1.set_ylabel(primary_col)
        ax1.set_title(f"{' / '.join([str(n) for n in stock_names])} - {primary_col}对比")

    ax1.set_xlabel(str(x_col))
    ax1.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


def _plot_single_series(df_sql, x_col, num_columns, save_path):
    df_plot = df_sql.copy()
    try:
        df_plot[x_col] = pd.to_datetime(df_plot[x_col])
    except (ValueError, TypeError):
        pass

    n = len(df_plot)
    use_line = n > 10

    price_cols = [c for c in num_columns if any(kw in c.lower() for kw in ['open', 'high', 'low', 'close', 'pre_close', 'price'])]
    vol_cols = [c for c in num_columns if 'vol' in c.lower()]
    other_cols = [c for c in num_columns if c not in price_cols and c not in vol_cols]

    has_dual_axis = len(price_cols) > 0 and len(vol_cols) > 0

    fig, ax1 = plt.subplots(figsize=(12, 6))

    if use_line:
        for col in price_cols:
            ax1.plot(df_plot[x_col], df_plot[col], marker='o', markersize=2, label=str(col))
        ax1.set_ylabel('价格')
        ax1.tick_params(axis='y')

        if has_dual_axis:
            ax2 = ax1.twinx()
            for col in vol_cols:
                ax2.bar(df_plot[x_col], df_plot[col], alpha=0.3, label=str(col), color='gray')
            ax2.set_ylabel('成交量')
            ax2.tick_params(axis='y')
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        else:
            for col in other_cols:
                ax1.plot(df_plot[x_col], df_plot[col], marker='o', markersize=2, label=str(col))
            ax1.legend()

        set_sparse_xticks(ax1, df_plot.sort_values(x_col)[x_col].reset_index(drop=True))
    else:
        df_sampled = sample_x_axis(df_plot, x_col)
        for col in price_cols:
            ax1.bar(df_sampled[x_col], df_sampled[col], alpha=0.7, label=str(col))
        ax1.set_ylabel('价格')
        ax1.tick_params(axis='y')

        if has_dual_axis:
            ax2 = ax1.twinx()
            for col in vol_cols:
                ax2.bar(df_sampled[x_col], df_sampled[col], alpha=0.3, label=str(col), color='gray')
            ax2.set_ylabel('成交量')
            ax2.tick_params(axis='y')
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        else:
            for col in other_cols:
                ax1.bar(df_sampled[x_col], df_sampled[col], alpha=0.7, label=str(col))
            ax1.legend()

    ax1.set_xlabel(str(x_col))
    ax1.set_title("股票行情走势")
    if pd.api.types.is_datetime64_any_dtype(df_plot[x_col]):
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
