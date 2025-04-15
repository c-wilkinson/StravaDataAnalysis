"""
Utilities for chart styling or other shared visualisation helpers.
"""

import matplotlib.pyplot as plt


def configure_matplotlib_styles() -> None:
    """
    Applies consistent style settings across all charts.
    """
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["axes.labelsize"] = 12
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["legend.fontsize"] = 12
    plt.rcParams["axes.grid"] = True
