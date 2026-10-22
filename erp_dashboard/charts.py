"""Matplotlib figure builders for the CRM and Sales modules.

Figures are created with the object-oriented ``Figure`` API (not ``pyplot``), so no global state
accumulates on a long-running server. Free of Streamlit imports.
"""

from __future__ import annotations

import pandas as pd
from matplotlib.figure import Figure


def _bar_of_sum(df: pd.DataFrame, by: str, value: str, title: str, ylabel: str) -> Figure:
    fig = Figure()
    ax = fig.subplots()
    df.groupby(by)[value].sum().plot(kind="bar", ax=ax)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    return fig


def _line_of_sum(df: pd.DataFrame, by: str, value: str, title: str, ylabel: str) -> Figure:
    fig = Figure()
    ax = fig.subplots()
    df.groupby(by)[value].sum().plot(kind="line", marker="o", ax=ax)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    return fig


def _pie_of_counts(df: pd.DataFrame, column: str, title: str) -> Figure:
    fig = Figure()
    ax = fig.subplots()
    counts = df[column].value_counts()
    ax.pie(counts, labels=counts.index, autopct="%1.1f%%", startangle=90)
    ax.set_title(title)
    return fig


# --- CRM ------------------------------------------------------------------------------
def crm_stage_distribution(df: pd.DataFrame) -> Figure:
    return _pie_of_counts(df, "Stage", "Distribusi Stage CRM")


def crm_revenue_by_salesperson(df: pd.DataFrame) -> Figure:
    return _bar_of_sum(df, "Salesperson", "Revenue", "Revenue per Salesperson", "Total Revenue")


def crm_revenue_trend(df: pd.DataFrame) -> Figure:
    return _line_of_sum(df, "Created", "Revenue", "Tren Revenue CRM per Tanggal", "Total Revenue")


# --- Sales ----------------------------------------------------------------------------
def sales_by_salesperson(df: pd.DataFrame) -> Figure:
    return _bar_of_sum(df, "Salesperson", "Amount", "Sales per Salesperson", "Total Amount")


def sales_trend(df: pd.DataFrame) -> Figure:
    return _line_of_sum(df, "Date", "Amount", "Tren Sales per Tanggal", "Total Amount")


def sales_status_distribution(df: pd.DataFrame) -> Figure:
    return _pie_of_counts(df, "Status", "Distribusi Status Order")
