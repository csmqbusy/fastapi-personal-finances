import io
from random import shuffle
from typing import Literal

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

COLORS = [
    "#005f73",
    "#0a9396",
    "#94d2bd",
    "#e9d8a6",
    "#ee9b00",
    "#ca6702",
    "#bb3e03",
    "#ae2012",
    "#9b2226",
    "#d9ed92",
    "#b5e48c",
    "#99d98c",
    "#76c893",
    "#52b69a",
    "#34a0a4",
    "#168aad",
    "#1a759f",
    "#1e6091",
    "#184e77",
    "#ffcdb2",
    "#ffb4a2",
    "#e5989b",
    "#b5838d",
    "#6d6875",
    "#52796f",
]


async def create_simple_chart(
    values: list[float],
    labels: list,
    chart_type: Literal["pie", "barplot"],
) -> bytes:
    colors_palette = COLORS.copy()
    shuffle(colors_palette)

    if chart_type == "pie":
        await _create_pie_chart(values, labels, colors_palette)
    else:
        await _create_barplot_chart(values, labels, colors_palette)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)

    return buffer.getvalue()


def create_simple_bar_chart(
    values: list[float],
    width: int,
    height: int,
    title: str,
    xlabel: str,
    ylabel: str = "Summary amount",
    color: str = "purple",
    linewidth: int = 2,
):
    x_labels = [i for i in range(1, len(values) + 1)]

    plt.figure(figsize=(width, height))
    sns.set_theme(style="whitegrid")
    sns.barplot(
        x=x_labels,
        y=values,
        color=color,
        linewidth=linewidth,
    )

    for i, total in enumerate(values):
        plt.text(
            x_labels[i] - 1.1,
            total,
            f"{total}",
            color="black",
            fontsize=10,
        )

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)

    return buffer.getvalue()


def create_annual_chart_with_categories(
    data: list[dict],
    categories: set,
    width: int,
    height: int,
    title: str,
    xlabel: str = "Month",
    ylabel: str = "Summary amount",
):
    if not data:
        df = pd.DataFrame({"month_number": range(1, 13)})
        for category in categories:
            df[category] = 0
        df["total_amount"] = 0
    else:
        df = pd.DataFrame(data)

    all_months = pd.DataFrame({"month_number": range(1, 13)})
    df = pd.merge(all_months, df, on="month_number", how="left").fillna(0)

    for col in df.columns:
        if col != "month_number":
            df[col] = df[col].astype(int)

    sns.set_theme(style="darkgrid")

    fig, ax = plt.subplots()
    fig.set_figwidth(width)
    fig.set_figheight(height)

    bottom = pd.Series([0] * len(df))

    for category in categories:
        ax.bar(df["month_number"], df[category], bottom=bottom, label=category)
        bottom += df[category]

    for i, total in enumerate(df["total_amount"]):
        ax.text(
            df["month_number"][i] - 0.1,
            total,
            f"{total}",
            color="black",
            fontsize=10,
        )

    ax.set_xticks(df["month_number"])
    ax.set_xticklabels(df["month_number"])

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)

    return buffer.getvalue()


def create_monthly_chart_with_categories(
    data: list[dict],
    days_in_month: int,
    categories: set,
    width: int,
    height: int,
    title: str,
    xlabel: str = "Day",
    ylabel: str = "Summary amount",
):
    if not data:
        df = pd.DataFrame({"day_number": range(1, days_in_month + 1)})
        for category in categories:
            df[category] = 0
        df["total_amount"] = 0
    else:
        df = pd.DataFrame(data)

    all_days = pd.DataFrame({"day_number": range(1, days_in_month + 1)})
    df = pd.merge(all_days, df, on="day_number", how="left").fillna(0)

    for col in df.columns:
        if col != "day_number":
            df[col] = df[col].astype(int)

    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots()
    fig.set_figwidth(width)
    fig.set_figheight(height)

    bottom = pd.Series([0] * len(df))

    for category in categories:
        ax.bar(df["day_number"], df[category], bottom=bottom, label=category)
        bottom += df[category]

    for i, total in enumerate(df["total_amount"]):
        ax.text(
            df["day_number"][i] - 0.1,
            total,
            f"{total}",
            color="black",
            fontsize=10,
        )

    ax.set_xticks(df["day_number"])
    ax.set_xticklabels(df["day_number"])

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)

    return buffer.getvalue()


async def _create_pie_chart(
    values: list,
    labels: list,
    colors: list,
):
    plt.pie(values, labels=labels, colors=colors, autopct="%.1f%%")


async def _create_barplot_chart(
    values: list,
    labels: list,
    colors: list,
):
    colors = colors[: len(labels)]
    sns.barplot(x=labels, y=values, palette=colors, hue=labels, legend=False)
