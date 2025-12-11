"""
Visualize normalized dataset features and labels from `data/normalized_dataset_v2.csv`.

Generates:
- Bar charts of summed counts for skill flags (`feat_skill_*`) and certifications (`feat_cert_*`).
- Bar chart of job domain flags (`feat_job_*`).
- Histograms for numeric features (counts, lengths, etc.).
- Correlation heatmap for numeric features.

Outputs are saved under `plots/normalized/`.
"""

from __future__ import annotations # Enables postponed evaluation of type annotations.

import argparse # Imports the argparse module for parsing command-line arguments.
import os # Imports the os module for path manipulation.
from pathlib import Path # Imports the Path class for object-oriented filesystem paths.
from typing import List # Imports List for type hinting.

import numpy as np # Imports numpy for numerical operations.
import pandas as pd # Imports pandas for data manipulation and analysis.
import matplotlib.pyplot as plt # Imports matplotlib for plotting.
import seaborn as sns # Imports seaborn for enhanced visualizations.


def list_columns_by_prefix(df: pd.DataFrame, prefix: str) -> List[str]:
    # Returns a list of column names from the DataFrame that start with the given prefix.
    return [c for c in df.columns if c.startswith(prefix)]


def ensure_out_dir(path: Path) -> None:
    # Creates the specified directory and any necessary parent directories if they don't exist.
    path.mkdir(parents=True, exist_ok=True)


def plot_bar_counts(df: pd.DataFrame, cols: List[str], title: str, out_file: Path) -> None:
    # If no columns are provided, the function returns early.
    if not cols:
        return
    # Calculates the sum of each column and stores it in a dictionary.
    counts = {c: int(df[c].sum()) for c in cols}
    # Sorts the items by count in descending order.
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    # Extracts labels (column names) from the sorted items.
    labels = [k for k, _ in items]
    # Extracts values (counts) from the sorted items.
    values = [v for _, v in items]

    # Creates a figure and an axes object for the plot.
    fig, ax = plt.subplots(figsize=(max(10, len(labels) * 0.25), 6))
    # Creates a bar plot with the labels and values.
    ax.bar(labels, values, color="#4C78A8")
    # Sets the title of the plot.
    ax.set_title(title)
    # Sets the label for the y-axis.
    ax.set_ylabel("Count")
    # Rotates x-axis tick labels for better readability.
    ax.tick_params(axis="x", rotation=90)
    # Adjusts plot to prevent labels from overlapping.
    fig.tight_layout()
    # Saves the figure to the specified output file.
    fig.savefig(out_file, dpi=150)
    # Closes the figure to free up memory.
    plt.close(fig)


def plot_histograms(df: pd.DataFrame, cols: List[str], title: str, out_file: Path) -> None:
    # If no columns are provided, the function returns early.
    if not cols:
        return
    # Calculates the number of columns.
    n = len(cols)
    # Sets the number of columns per row for the subplot grid.
    cols_per_row = 4
    # Calculates the number of rows needed for the subplot grid.
    rows = int(np.ceil(n / cols_per_row))
    # Creates a figure and a grid of subplots.
    fig, axes = plt.subplots(rows, cols_per_row, figsize=(cols_per_row * 4, rows * 3))
    # Flattens the axes array for easier iteration.
    axes = np.array(axes).reshape(rows, cols_per_row)
    # Iterates through each column to create a histogram.
    for i, c in enumerate(cols):
        # Calculates the row and column index for the current subplot.
        r, k = divmod(i, cols_per_row)
        # Gets the current axes object.
        ax = axes[r][k]
        # Creates a histogram with 50 bins and no KDE, with a specified color.
        sns.histplot(df[c], bins=50, kde=False, ax=ax, color="#72B7B2")
        try:
            # Adds a rug plot to show individual data points.
            sns.rugplot(x=pd.to_numeric(df[c], errors="coerce"), ax=ax, height=0.05, color="#333", alpha=0.2)
        except Exception:
            pass # Ignores errors during rug plot creation.
        # Sets the title of the subplot.
        ax.set_title(c)
    # Hides any unused subplots in the grid.
    for j in range(n, rows * cols_per_row):
        r, k = divmod(j, cols_per_row)
        axes[r][k].axis("off")
    # Sets the main title for the entire figure.
    fig.suptitle(title)
    # Adjusts subplot parameters for a tight layout.
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    # Saves the figure to the specified output file.
    fig.savefig(out_file, dpi=150)
    # Closes the figure to free up memory.
    plt.close(fig)


def plot_corr_heatmap(df: pd.DataFrame, cols: List[str], title: str, out_file: Path) -> None:
    # If no columns are provided, the function returns early.
    if not cols:
        return
    # Computes the correlation matrix for the specified columns.
    corr = df[cols].corr()
    # Creates a figure and an axes object for the plot.
    fig, ax = plt.subplots(figsize=(max(8, len(cols) * 0.5), max(6, len(cols) * 0.5)))
    # Creates a heatmap of the correlation matrix.
    sns.heatmap(corr, cmap="viridis", ax=ax)
    # Sets the title of the plot.
    ax.set_title(title)
    # Adjusts plot to prevent labels from overlapping.
    fig.tight_layout()
    # Saves the figure to the specified output file.
    fig.savefig(out_file, dpi=150)
    # Closes the figure to free up memory.
    plt.close(fig)


def plot_feature_vs_ai_and_recruiter(
    df: pd.DataFrame,
    numeric_cols: List[str],
    ai_score_col: str,
    recruiter_decision_col: str,
    out_dir: Path,
) -> None:
    # Checks if numeric columns are provided or if AI Score/Recruiter Decision columns are missing.
    if not numeric_cols or ai_score_col not in df.columns or recruiter_decision_col not in df.columns:
        return

    # Iterates through each numeric column to create scatter and box plots.
    for col in numeric_cols:
        # Plot against AI Score
        # Creates a figure and an axes object for the scatter plot.
        fig, ax = plt.subplots(figsize=(8, 6))
        # Creates a scatter plot of the numeric column vs. AI Score.
        sns.scatterplot(data=df, x=col, y=ai_score_col, ax=ax, alpha=0.6)
        # Sets the title of the scatter plot.
        ax.set_title(f"{col} vs. {ai_score_col}")
        # Adjusts plot to prevent labels from overlapping.
        fig.tight_layout()
        # Saves the scatter plot to the output directory.
        fig.savefig(out_dir / f"{col}_vs_ai_score.png", dpi=150)
        # Closes the figure to free up memory.
        plt.close(fig)

        # Plot against Recruiter Decision
        # Creates a figure and an axes object for the box plot.
        fig, ax = plt.subplots(figsize=(8, 6))
        # Creates a box plot of the numeric column vs. Recruiter Decision.
        sns.boxplot(data=df, x=recruiter_decision_col, y=col, ax=ax)
        # Sets the title of the box plot.
        ax.set_title(f"{col} vs. {recruiter_decision_col}")
        # Adjusts plot to prevent labels from overlapping.
        fig.tight_layout()
        # Saves the box plot to the output directory.
        fig.savefig(out_dir / f"{col}_vs_recruiter_decision.png", dpi=150)
        # Closes the figure to free up memory.
        plt.close(fig)


def main():
    # Creates an argument parser with a description.
    parser = argparse.ArgumentParser(description="Plot normalized dataset features")
    # Adds an argument for the input normalized CSV file.
    parser.add_argument("--input", default=os.path.join("data", "normalized_dataset_v2.csv"), help="Path to normalized CSV")
    parser.add_argument("--out", default=os.path.join("plots", "normalized"), help="Output directory for plots")
    # Parses the command-line arguments.
    args = parser.parse_args()

    # Creates Path objects for the input file and output directory.
    in_path = Path(args.input)
    out_dir = Path(args.out)
    # Checks if the input CSV file exists.
    if not in_path.exists():
        # Raises a FileNotFoundError if the input file is not found.
        raise FileNotFoundError(f"Input CSV not found: {in_path}")

    # Ensures that the output directory exists.
    ensure_out_dir(out_dir)
    # Reads the input CSV file into a pandas DataFrame.
    df = pd.read_csv(in_path)

    # Identify columns
    # Lists skill-related columns.
    skill_cols = list_columns_by_prefix(df, "feat_skill_")
    # Lists certification-related columns.
    cert_cols = list_columns_by_prefix(df, "feat_cert_")
    # Lists job domain-related columns.
    domain_cols = list_columns_by_prefix(df, "feat_job_")

    # Defines a list of candidate numeric columns.
    numeric_candidates = [
        "feat_num_skills_matched",
        "feat_num_certifications",
        "feat_years_experience_extracted",
        "feat_text_len_chars",
        "feat_text_len_words",
        "Experience (Years)",
        "Salary Expectation ($)",
        "Projects Count",
        "AI Score (0-100)",
    ]
    # Filters the numeric candidates to include only those present in the DataFrame.
    numeric_cols = [c for c in numeric_candidates if c in df.columns]

    # Plots
    # Generates and saves bar plots for skill flags.
    plot_bar_counts(df, skill_cols, "Skill Flags (sum across resumes)", out_dir / "skill_counts.png")
    # Generates and saves bar plots for certification flags.
    plot_bar_counts(df, cert_cols, "Certification Flags (sum across resumes)", out_dir / "cert_counts.png")
    # Generates and saves bar plots for job domain flags.
    plot_bar_counts(df, domain_cols, "Job Domain Flags (sum across resumes)", out_dir / "domain_counts.png")
    # Generates and saves histograms for numeric feature distributions.
    plot_histograms(df, numeric_cols, "Numeric Feature Distributions", out_dir / "numeric_histograms.png")
    # Generates and saves a correlation heatmap for numeric features.
    plot_corr_heatmap(df, numeric_cols, "Numeric Feature Correlations", out_dir / "corr_heatmap.png")

    # New plots for AI Score and Recruiter Decision vs. each numeric feature
    # Generates and saves plots comparing numeric features against AI Score and Recruiter Decision.
    plot_feature_vs_ai_and_recruiter(
        df,
        [c for c in numeric_cols if c != "AI Score (0-100)"], # Exclude AI Score from being plotted against itself
        "AI Score (0-100)",
        "Recruiter_Decision",
        out_dir,
    )

    # Recruiter decision distribution (if present)
    # Checks if the 'Recruiter_Decision' column exists.
    if "Recruiter_Decision" in df.columns:
        # Computes value counts for 'Recruiter_Decision' and sorts them by index.
        counts = df["Recruiter_Decision"].value_counts().sort_index()
        # Creates a figure and an axes object for the bar plot.
        fig, ax = plt.subplots(figsize=(6, 4))
        # Creates a bar plot for the recruiter decision distribution.
        ax.bar(counts.index.astype(str), counts.values, color="#E45756")
        # Sets the title of the plot.
        ax.set_title("Recruiter Decision Distribution")
        # Sets the label for the y-axis.
        ax.set_ylabel("Count")
        # Adjusts plot to prevent labels from overlapping.
        fig.tight_layout()
        # Saves the recruiter decision distribution plot.
        fig.savefig(out_dir / "recruiter_decision_counts.png", dpi=150)
        # Closes the figure to free up memory.
        plt.close(fig)

    # Prints a confirmation message with the output directory.
    print(f"Saved plots to: {out_dir}")


if __name__ == "__main__":
    main() # Calls the main function when the script is executed.