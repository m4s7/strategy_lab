"""Visualization configuration."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class PlotConfig:
    """Configuration for plots and visualizations."""

    # Figure settings
    figure_size: Tuple[int, int] = (12, 8)
    dpi: int = 100
    style: str = "seaborn-v0_8-darkgrid"

    # Color scheme
    primary_color: str = "#1f77b4"
    secondary_color: str = "#ff7f0e"
    positive_color: str = "#2ca02c"
    negative_color: str = "#d62728"

    # Font settings
    title_size: int = 16
    label_size: int = 12
    tick_size: int = 10

    # Grid settings
    show_grid: bool = True
    grid_alpha: float = 0.3

    # Save settings
    save_path: Optional[str] = None
    save_format: str = "png"

    # Interactive settings
    interactive: bool = False
    show_toolbar: bool = True
