import io

import pytest
from matplotlib.figure import Figure

from erp_dashboard import config
from erp_dashboard.modules import MODULES, MODULES_BY_NAME

CHART_VIEWS = [(spec, view) for spec in MODULES for view in spec.views if view.chart is not None]


def test_registry_lists_the_eleven_modules_in_display_order():
    assert [spec.name for spec in MODULES] == [
        "CRM",
        "Sales",
        "Finance",
        "Inventory",
        "Purchase",
        "Payment",
        "Partners",
        "Products",
        "Credit",
        "HR",
        "GA",
    ]
    assert set(MODULES_BY_NAME) == {spec.name for spec in MODULES}


def test_registry_view_counts():
    assert sum(len(spec.views) for spec in MODULES) == 17
    assert len(CHART_VIEWS) == 6
    assert {spec.name for spec, _ in CHART_VIEWS} == {"CRM", "Sales"}


def test_view_labels_are_unique_within_a_module():
    for spec in MODULES:
        labels = [view.label for view in spec.views]
        assert len(labels) == len(set(labels)), spec.name


def test_company_registry_has_one_page_and_ten_placeholders():
    pages = [page for page in config.COMPANIES.values() if page]
    assert pages == ["pages/dashboard_fistx.py"]
    assert len(config.COMPANIES) == 11


@pytest.mark.parametrize(("spec", "view"), CHART_VIEWS, ids=lambda item: getattr(item, "label", ""))
def test_chart_builds_a_figure_that_renders_to_png(spec, view):
    df = spec.load(config.FISTX_DATA_DIR)

    figure = view.chart(df)

    assert isinstance(figure, Figure)
    assert figure.axes
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png")
    assert buffer.getvalue().startswith(b"\x89PNG")
    assert len(buffer.getvalue()) > 5_000


def test_charts_do_not_leave_pyplot_figures_open():
    import matplotlib.pyplot as plt

    before = len(plt.get_fignums())
    for spec, view in CHART_VIEWS:
        view.chart(spec.load(config.FISTX_DATA_DIR))
    assert len(plt.get_fignums()) == before
