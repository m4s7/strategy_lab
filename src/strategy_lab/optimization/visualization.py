"""Visualization tools for optimization results."""

from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure

from .core.results import OptimizationResultSet


class OptimizationVisualizer:
    """Visualization tools for optimization results."""

    def __init__(self, results: OptimizationResultSet):
        """Initialize visualizer.

        Args:
            results: Optimization result set to visualize
        """
        self.results = results
        self.df = results.to_dataframe()

        # Set default style
        plt.style.use("seaborn-v0_8-darkgrid")
        sns.set_palette("husl")

    def plot_parameter_sensitivity(
        self,
        parameter: str,
        metric: str,
        figsize: Tuple[float, float] = (10, 6),
        show_confidence: bool = True,
    ) -> Figure:
        """Plot parameter sensitivity analysis.

        Args:
            parameter: Parameter name to analyze
            metric: Metric to plot
            figsize: Figure size
            show_confidence: Whether to show confidence intervals

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=figsize)

        param_col = f"param_{parameter}"
        metric_col = f"metric_{metric}"

        if param_col not in self.df.columns or metric_col not in self.df.columns:
            ax.text(0.5, 0.5, "Data not available", ha="center", va="center")
            return fig

        # Get sensitivity data
        sensitivity = self.results.get_parameter_sensitivity(parameter, metric)

        if sensitivity.empty:
            ax.text(0.5, 0.5, "No data to plot", ha="center", va="center")
            return fig

        # Create plot
        x = sensitivity[parameter]
        y = sensitivity["mean"]

        # Main line plot
        ax.plot(x, y, "o-", linewidth=2, markersize=8, label="Mean")

        # Confidence intervals
        if show_confidence and "std" in sensitivity.columns:
            lower = y - sensitivity["std"]
            upper = y + sensitivity["std"]
            ax.fill_between(x, lower, upper, alpha=0.3, label="± 1 STD")

        # Min/max range
        if "min" in sensitivity.columns and "max" in sensitivity.columns:
            ax.fill_between(
                x,
                sensitivity["min"],
                sensitivity["max"],
                alpha=0.1,
                color="gray",
                label="Min/Max range",
            )

        ax.set_xlabel(parameter, fontsize=12)
        ax.set_ylabel(f"{metric} (mean)", fontsize=12)
        ax.set_title(f"Parameter Sensitivity: {parameter} vs {metric}", fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def plot_heatmap(
        self,
        param1: str,
        param2: str,
        metric: str,
        figsize: Tuple[float, float] = (10, 8),
        cmap: str = "viridis",
        annotate: bool = True,
    ) -> Figure:
        """Plot 2D parameter heatmap.

        Args:
            param1: First parameter (x-axis)
            param2: Second parameter (y-axis)
            metric: Metric to visualize
            figsize: Figure size
            cmap: Colormap name
            annotate: Whether to annotate cells with values

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=figsize)

        param1_col = f"param_{param1}"
        param2_col = f"param_{param2}"
        metric_col = f"metric_{metric}"

        # Check columns exist
        required_cols = [param1_col, param2_col, metric_col]
        if not all(col in self.df.columns for col in required_cols):
            ax.text(0.5, 0.5, "Required data not available", ha="center", va="center")
            return fig

        # Pivot data for heatmap
        pivot = self.df.pivot_table(
            values=metric_col, index=param2_col, columns=param1_col, aggfunc="mean"
        )

        # Create heatmap
        sns.heatmap(
            pivot,
            annot=annotate,
            fmt=".3f",
            cmap=cmap,
            cbar_kws={"label": metric},
            ax=ax,
        )

        ax.set_xlabel(param1, fontsize=12)
        ax.set_ylabel(param2, fontsize=12)
        ax.set_title(f"{metric} Heatmap: {param1} vs {param2}", fontsize=14)

        plt.tight_layout()
        return fig

    def plot_surface_3d(
        self,
        param1: str,
        param2: str,
        metric: str,
        figsize: Tuple[float, float] = (12, 9),
        elevation: float = 30,
        azimuth: float = 45,
    ) -> Figure:
        """Plot 3D surface of optimization results.

        Args:
            param1: First parameter (x-axis)
            param2: Second parameter (y-axis)
            metric: Metric (z-axis)
            figsize: Figure size
            elevation: View elevation angle
            azimuth: View azimuth angle

        Returns:
            Matplotlib figure
        """
        from mpl_toolkits.mplot3d import Axes3D

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection="3d")

        param1_col = f"param_{param1}"
        param2_col = f"param_{param2}"
        metric_col = f"metric_{metric}"

        # Check columns exist
        if not all(
            col in self.df.columns for col in [param1_col, param2_col, metric_col]
        ):
            ax.text2D(0.5, 0.5, "Required data not available", transform=ax.transAxes)
            return fig

        # Get unique values for grid
        x_unique = sorted(self.df[param1_col].unique())
        y_unique = sorted(self.df[param2_col].unique())

        # Create meshgrid
        X, Y = np.meshgrid(x_unique, y_unique)

        # Pivot data for Z values
        pivot = self.df.pivot_table(
            values=metric_col, index=param2_col, columns=param1_col, aggfunc="mean"
        )

        # Reindex to ensure alignment
        Z = pivot.reindex(index=y_unique, columns=x_unique).values

        # Create surface plot
        surf = ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8, edgecolor="none")

        # Add scatter points for actual evaluations
        ax.scatter(
            self.df[param1_col],
            self.df[param2_col],
            self.df[metric_col],
            c="red",
            s=20,
            alpha=0.6,
        )

        ax.set_xlabel(param1, fontsize=12)
        ax.set_ylabel(param2, fontsize=12)
        ax.set_zlabel(metric, fontsize=12)
        ax.set_title(f"3D Surface: {metric}", fontsize=14)

        # Set viewing angle
        ax.view_init(elevation, azimuth)

        # Add colorbar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

        plt.tight_layout()
        return fig

    def plot_pareto_frontier(
        self,
        metric1: str,
        metric2: str,
        minimize: Optional[List[bool]] = None,
        figsize: Tuple[float, float] = (10, 8),
        highlight_frontier: bool = True,
    ) -> Figure:
        """Plot Pareto frontier for two objectives.

        Args:
            metric1: First metric (x-axis)
            metric2: Second metric (y-axis)
            minimize: Whether to minimize each metric
            figsize: Figure size
            highlight_frontier: Whether to highlight Pareto optimal points

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=figsize)

        metric1_col = f"metric_{metric1}"
        metric2_col = f"metric_{metric2}"

        # Check columns exist
        if metric1_col not in self.df.columns or metric2_col not in self.df.columns:
            ax.text(
                0.5, 0.5, "Required metrics not available", ha="center", va="center"
            )
            return fig

        # Get all points
        x = self.df[metric1_col].values
        y = self.df[metric2_col].values

        # Plot all points
        ax.scatter(x, y, alpha=0.5, s=50, label="All results")

        # Get and plot Pareto frontier
        if highlight_frontier:
            pareto_results = self.results.get_pareto_frontier(
                [metric1, metric2], minimize=minimize
            )

            if pareto_results:
                pareto_x = [r.get_metric(metric1) for r in pareto_results]
                pareto_y = [r.get_metric(metric2) for r in pareto_results]

                # Sort for line plot
                sorted_indices = np.argsort(pareto_x)
                pareto_x = np.array(pareto_x)[sorted_indices]
                pareto_y = np.array(pareto_y)[sorted_indices]

                ax.scatter(
                    pareto_x,
                    pareto_y,
                    color="red",
                    s=100,
                    marker="D",
                    edgecolor="black",
                    linewidth=2,
                    label="Pareto frontier",
                    zorder=5,
                )

                # Connect Pareto points
                ax.plot(pareto_x, pareto_y, "r--", alpha=0.5, linewidth=2)

        ax.set_xlabel(metric1, fontsize=12)
        ax.set_ylabel(metric2, fontsize=12)
        ax.set_title(f"Pareto Frontier: {metric1} vs {metric2}", fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Add direction indicators
        if minimize:
            if minimize[0]:
                ax.annotate("← Better", xy=(0.05, 0.5), xycoords="axes fraction")
            else:
                ax.annotate("Better →", xy=(0.85, 0.5), xycoords="axes fraction")

            if minimize[1]:
                ax.annotate(
                    "↓ Better", xy=(0.5, 0.05), xycoords="axes fraction", rotation=90
                )
            else:
                ax.annotate(
                    "Better ↑", xy=(0.5, 0.85), xycoords="axes fraction", rotation=90
                )

        plt.tight_layout()
        return fig

    def plot_parallel_coordinates(
        self,
        parameters: List[str],
        metric: str,
        n_best: int = 20,
        figsize: Tuple[float, float] = (12, 6),
        colormap: str = "viridis",
    ) -> Figure:
        """Plot parallel coordinates for multiple parameters.

        Args:
            parameters: List of parameter names
            metric: Metric to color by
            n_best: Number of best results to highlight
            figsize: Figure size
            colormap: Colormap name

        Returns:
            Matplotlib figure
        """
        from pandas.plotting import parallel_coordinates

        fig, ax = plt.subplots(figsize=figsize)

        # Prepare data
        param_cols = [f"param_{p}" for p in parameters]
        metric_col = f"metric_{metric}"

        # Check columns exist
        required_cols = param_cols + [metric_col]
        if not all(col in self.df.columns for col in required_cols):
            ax.text(0.5, 0.5, "Required data not available", ha="center", va="center")
            return fig

        # Get subset of data
        plot_df = self.df[param_cols + [metric_col]].copy()

        # Rename columns for display
        plot_df.columns = parameters + [metric]

        # Normalize parameters to 0-1 range
        for param in parameters:
            col_min = plot_df[param].min()
            col_max = plot_df[param].max()
            if col_max > col_min:
                plot_df[param] = (plot_df[param] - col_min) / (col_max - col_min)

        # Get best results
        best_results = self.results.get_best_results(metric, n=n_best)
        best_indices = []
        for result in best_results:
            # Find matching row
            mask = True
            for param, value in result.parameters.items():
                if f"param_{param}" in self.df.columns:
                    mask &= self.df[f"param_{param}"] == value
            matching_indices = self.df[mask].index
            if len(matching_indices) > 0:
                best_indices.append(matching_indices[0])

        # Plot all results with low alpha
        parallel_coordinates(
            plot_df,
            metric,
            color=plt.cm.get_cmap(colormap)(plot_df[metric]),
            alpha=0.3,
            ax=ax,
        )

        # Highlight best results
        if best_indices:
            best_df = plot_df.iloc[best_indices]
            parallel_coordinates(
                best_df, metric, color="red", alpha=0.8, linewidth=2, ax=ax
            )

        ax.set_title(
            f"Parallel Coordinates: Parameters colored by {metric}", fontsize=14
        )
        ax.set_ylabel("Normalized Value", fontsize=12)
        ax.legend().remove()  # Remove auto legend

        # Add colorbar
        sm = plt.cm.ScalarMappable(
            cmap=colormap,
            norm=plt.Normalize(vmin=plot_df[metric].min(), vmax=plot_df[metric].max()),
        )
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label(metric, fontsize=12)

        plt.tight_layout()
        return fig

    def create_dashboard(
        self,
        metrics: List[str],
        parameters: Optional[List[str]] = None,
        figsize: Tuple[float, float] = (16, 12),
    ) -> Figure:
        """Create comprehensive optimization dashboard.

        Args:
            metrics: List of metrics to include
            parameters: List of parameters to analyze (None for auto-detect)
            figsize: Figure size

        Returns:
            Matplotlib figure with multiple subplots
        """
        # Auto-detect parameters if not provided
        if parameters is None:
            param_cols = [col for col in self.df.columns if col.startswith("param_")]
            parameters = [col[6:] for col in param_cols[:3]]  # Take first 3

        # Create figure with subplots
        fig = plt.figure(figsize=figsize)
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # 1. Summary statistics (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        summary = self.results.get_summary_statistics()
        summary_text = f"Total Results: {summary['total_results']}\n"
        summary_text += f"Total Time: {summary['total_execution_time']:.1f}s\n"
        summary_text += f"Avg Time: {summary['average_execution_time']:.2f}s\n\n"

        for metric in metrics[:3]:  # Show first 3 metrics
            if metric in summary.get("metrics", {}):
                stats = summary["metrics"][metric]
                summary_text += f"{metric}:\n"
                summary_text += f"  Mean: {stats['mean']:.3f}\n"
                summary_text += f"  Best: {stats['max']:.3f}\n"

        ax1.text(
            0.1,
            0.9,
            summary_text,
            transform=ax1.transAxes,
            verticalalignment="top",
            fontsize=10,
            family="monospace",
        )
        ax1.set_title("Summary Statistics", fontsize=12)
        ax1.axis("off")

        # 2. Parameter sensitivity for first metric (top middle and right)
        if len(parameters) >= 1 and len(metrics) >= 1:
            ax2 = fig.add_subplot(gs[0, 1:])
            self.plot_parameter_sensitivity(parameters[0], metrics[0], figsize=None)
            plt.sca(ax2)
            sensitivity = self.results.get_parameter_sensitivity(
                parameters[0], metrics[0]
            )
            if not sensitivity.empty:
                ax2.plot(
                    sensitivity[parameters[0]], sensitivity["mean"], "o-", linewidth=2
                )
                ax2.fill_between(
                    sensitivity[parameters[0]],
                    sensitivity["mean"] - sensitivity["std"],
                    sensitivity["mean"] + sensitivity["std"],
                    alpha=0.3,
                )
                ax2.set_xlabel(parameters[0])
                ax2.set_ylabel(f"{metrics[0]} (mean)")
                ax2.set_title(f"Sensitivity: {parameters[0]}")
                ax2.grid(True, alpha=0.3)

        # 3. 2D Heatmap (middle left and center)
        if len(parameters) >= 2 and len(metrics) >= 1:
            ax3 = fig.add_subplot(gs[1, :2])
            param1_col = f"param_{parameters[0]}"
            param2_col = f"param_{parameters[1]}"
            metric_col = f"metric_{metrics[0]}"

            if all(
                col in self.df.columns for col in [param1_col, param2_col, metric_col]
            ):
                pivot = self.df.pivot_table(
                    values=metric_col,
                    index=param2_col,
                    columns=param1_col,
                    aggfunc="mean",
                )
                sns.heatmap(
                    pivot,
                    annot=False,
                    cmap="viridis",
                    ax=ax3,
                    cbar_kws={"label": metrics[0]},
                )
                ax3.set_xlabel(parameters[0])
                ax3.set_ylabel(parameters[1])
                ax3.set_title(f"{metrics[0]} Heatmap")

        # 4. Metric distribution (middle right)
        if len(metrics) >= 1:
            ax4 = fig.add_subplot(gs[1, 2])
            metric_col = f"metric_{metrics[0]}"
            if metric_col in self.df.columns:
                self.df[metric_col].hist(
                    bins=30, ax=ax4, alpha=0.7, color="skyblue", edgecolor="black"
                )
                ax4.axvline(
                    self.df[metric_col].mean(),
                    color="red",
                    linestyle="--",
                    linewidth=2,
                    label="Mean",
                )
                ax4.axvline(
                    self.df[metric_col].max(),
                    color="green",
                    linestyle="--",
                    linewidth=2,
                    label="Best",
                )
                ax4.set_xlabel(metrics[0])
                ax4.set_ylabel("Count")
                ax4.set_title(f"{metrics[0]} Distribution")
                ax4.legend()

        # 5. Best results table (bottom)
        ax5 = fig.add_subplot(gs[2, :])
        best_results = self.results.get_best_results(
            metrics[0] if metrics else "objective", n=5
        )

        if best_results:
            # Create table data
            table_data = []
            columns = (
                ["Rank"]
                + list(best_results[0].parameters.keys())
                + list(best_results[0].metrics.keys())
            )

            for i, result in enumerate(best_results):
                row = [i + 1]
                row.extend(result.parameters.values())
                row.extend(f"{v:.3f}" for v in result.metrics.values())
                table_data.append(row)

            # Create table
            table = ax5.table(
                cellText=table_data, colLabels=columns, cellLoc="center", loc="center"
            )
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.5)

            ax5.set_title("Top 5 Results", fontsize=12)
            ax5.axis("off")

        plt.suptitle("Grid Search Optimization Dashboard", fontsize=16)
        return fig
