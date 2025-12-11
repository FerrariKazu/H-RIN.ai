import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import argparse
import os
from pathlib import Path

def plot_feature_importance(
    input_csv_path: Path,
    output_png_path: Path,
    title: str = "Feature Importance",
    xlabel: str = "Importance Score",
    ylabel: str = "Features",
    figsize: tuple = (12, 8),
    fontsize_title: int = 16,
    fontsize_labels: int = 12,
    fontsize_ticks: int = 10,
    dpi: int = 300
):
    """
    Generates a comprehensive feature importance graph visualization.

    Args:
        input_csv_path (Path): Path to the CSV file containing feature coefficients.
                                Expected columns: 'feature', 'coefficient', 'abs_coefficient'.
        output_png_path (Path): Path to save the output PNG file.
        title (str): Title of the plot.
        xlabel (str): Label for the x-axis.
        ylabel (str): Label for the y-axis.
        figsize (tuple): Figure size (width, height) in inches.
        fontsize_title (int): Font size for the plot title.
        fontsize_labels (int): Font size for axis labels.
        fontsize_ticks (int): Font size for axis ticks.
        dpi (int): Dots per inch for saving the PNG file.
    """
    # Load the feature coefficients
    df = pd.read_csv(input_csv_path)

    # Sort features by absolute importance score in ascending order for horizontal bar chart
    df_sorted = df.sort_values(by='abs_coefficient', ascending=True)

    features = df_sorted['feature']
    importance_scores = df_sorted['abs_coefficient']
    coefficients = df_sorted['coefficient'] # Keep original coefficients for color coding

    # Create a color gradient based on importance scores
    norm = mcolors.Normalize(vmin=importance_scores.min(), vmax=importance_scores.max())
    cmap = plt.cm.viridis # You can choose other colormaps like 'plasma', 'magma', 'cividis'
    colors = cmap(norm(importance_scores))

    # Create the horizontal bar chart
    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.barh(features, importance_scores, color=colors)

    # Add labels and title
    ax.set_title(title, fontsize=fontsize_title)
    ax.set_xlabel(xlabel, fontsize=fontsize_labels)
    ax.set_ylabel(ylabel, fontsize=fontsize_labels)

    # Adjust tick font sizes
    ax.tick_params(axis='x', labelsize=fontsize_ticks)
    ax.tick_params(axis='y', labelsize=fontsize_ticks)

    # Ensure proper scaling and layout
    fig.tight_layout()

    # Add a color bar as a legend
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([]) # Only needed for matplotlib < 3.1
    cbar = fig.colorbar(sm, ax=ax, orientation='vertical', fraction=0.02, pad=0.04)
    cbar.set_label("Absolute Coefficient Value", fontsize=fontsize_labels)
    cbar.ax.tick_params(labelsize=fontsize_ticks)

    # Save the visualization
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_png_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig) # Close the figure to free up memory

    print(f"Feature importance plot saved to {output_png_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a feature importance visualization.")
    parser.add_argument(
        "--input_csv",
        type=Path,
        default=Path(os.path.join("models", "pipeline_v3", "coefficients_recruiter.csv")),
        help="Path to the input CSV file containing feature coefficients."
    )
    parser.add_argument(
        "--output_png",
        type=Path,
        default=Path(os.path.join("plots", "model_b", "feature_importance_recruiter.png")),
        help="Path to save the output PNG file."
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Recruiter Model Feature Importance",
        help="Title of the plot."
    )
    parser.add_argument(
        "--xlabel",
        type=str,
        default="Absolute Coefficient Value",
        help="Label for the x-axis."
    )
    parser.add_argument(
        "--ylabel",
        type=str,
        default="Features",
        help="Label for the y-axis."
    )
    parser.add_argument(
        "--figsize_width",
        type=int,
        default=12,
        help="Width of the figure in inches."
    )
    parser.add_argument(
        "--figsize_height",
        type=int,
        default=8,
        help="Height of the figure in inches."
    )
    parser.add_argument(
        "--fontsize_title",
        type=int,
        default=16,
        help="Font size for the plot title."
    )
    parser.add_argument(
        "--fontsize_labels",
        type=int,
        default=12,
        help="Font size for axis labels."
    )
    parser.add_argument(
        "--fontsize_ticks",
        type=int,
        default=10,
        help="Font size for axis ticks."
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Dots per inch for saving the PNG file."
    )

    args = parser.parse_args()

    plot_feature_importance(
        input_csv_path=args.input_csv,
        output_png_path=args.output_png,
        title=args.title,
        xlabel=args.xlabel,
        ylabel=args.ylabel,
        figsize=(args.figsize_width, args.figsize_height),
        fontsize_title=args.fontsize_title,
        fontsize_labels=args.fontsize_labels,
        fontsize_ticks=args.fontsize_ticks,
        dpi=args.dpi
    )