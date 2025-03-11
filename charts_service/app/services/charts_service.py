import io
from random import shuffle
from typing import Literal

import matplotlib.pyplot as plt
import seaborn as sns

COLORS = ["#005f73", "#0a9396", "#94d2bd", "#e9d8a6", "#ee9b00", "#ca6702",
          "#bb3e03", "#ae2012", "#9b2226", "#d9ed92", "#b5e48c", "#99d98c",
          "#76c893", "#52b69a", "#34a0a4", "#168aad", "#1a759f", "#1e6091",
          "#184e77", "#ffcdb2", "#ffb4a2", "#e5989b", "#b5838d", "#6d6875",
          "#52796f"]


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
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    return buffer.getvalue()


async def _create_pie_chart(
    values: list,
    labels: list,
    colors: list,
):
    plt.pie(values, labels=labels, colors=colors, autopct='%.1f%%')


async def _create_barplot_chart(
    values: list,
    labels: list,
    colors: list,
):
    colors = colors[:len(labels)]
    sns.barplot(x=labels, y=values, palette=colors, hue=labels, legend=False)
