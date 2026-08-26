"""
Data Visualization for MP3 AI Benchmark.
Generates Pareto frontiers, WER vs Bitrate curves, token usage vs VAD, and radar comparisons.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Any

from config import PLOTS_DIR


class BenchmarkVisualizer:
    """Renders charts from benchmark experiment data."""

    def __init__(self, style: str = "whitegrid"):
        sns.set_theme(style=style)
        plt.rcParams["font.sans-serif"] = "DejaVu Sans"
        plt.rcParams["font.family"] = "sans-serif"

    def plot_all(self, results: List[Dict[str, Any]]) -> List[Path]:
        """Generates all benchmark charts."""
        if not results:
            return []

        df = pd.DataFrame(results)
        generated_plots = []

        p1 = self.plot_wer_vs_bitrate(df)
        if p1:
            generated_plots.append(p1)

        p2 = self.plot_tokens_and_vad(df)
        if p2:
            generated_plots.append(p2)

        p3 = self.plot_pareto_frontier(df)
        if p3:
            generated_plots.append(p3)

        p4 = self.plot_latency_breakdown(df)
        if p4:
            generated_plots.append(p4)

        return generated_plots

    def plot_wer_vs_bitrate(self, df: pd.DataFrame) -> Path:
        """Plots WER (%) vs Bitrate to locate the quality breaking threshold."""
        bitrate_df = df[df["category"] == "Bitrate Sweep"].copy()
        if bitrate_df.empty:
            return None

        # Clean bitrate numeric value
        bitrate_df["bitrate_num"] = bitrate_df["bitrate"].str.replace("k", "").astype(int)
        bitrate_df = bitrate_df.sort_values(by="bitrate_num")

        fig, ax1 = plt.subplots(figsize=(10, 6))

        color = "#1f77b4"
        ax1.set_xlabel("Bitrate do MP3 (kbps)", fontsize=12, fontweight="bold")
        ax1.set_ylabel("Word Error Rate - WER (%) [Menor é Melhor]", color=color, fontsize=12, fontweight="bold")
        line1 = ax1.plot(
            bitrate_df["bitrate_num"],
            bitrate_df["wer"],
            marker="o",
            linewidth=2.5,
            markersize=8,
            color=color,
            label="WER (%)"
        )
        ax1.tick_params(axis="y", labelcolor=color)
        ax1.set_ylim(-5, max(100, bitrate_df["wer"].max() + 10))

        # Secondary axis for file size
        ax2 = ax1.twinx()
        color2 = "#ff7f0e"
        ax2.set_ylabel("Tamanho do MP3 (KB) [Menor é Melhor]", color=color2, fontsize=12, fontweight="bold")
        line2 = ax2.plot(
            bitrate_df["bitrate_num"],
            bitrate_df["processed_size_kb"],
            marker="s",
            linestyle="--",
            linewidth=2,
            color=color2,
            label="Tamanho (KB)"
        )
        ax2.tick_params(axis="y", labelcolor=color2)

        plt.title("Impacto do Bitrate MP3 na Acurácia do Gemini (WER) vs. Tamanho", fontsize=14, fontweight="bold", pad=15)
        fig.tight_layout()

        out_path = PLOTS_DIR / "01_wer_vs_bitrate.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        return out_path

    def plot_tokens_and_vad(self, df: pd.DataFrame) -> Path:
        """Compares token consumption and duration with and without VAD silence stripping."""
        fig, ax = plt.subplots(figsize=(12, 6))

        # Select representative treatments
        subset = df.head(10).copy()
        bars = ax.bar(subset["treatment_label"], subset["total_tokens"], color="#2ca02c", alpha=0.85, edgecolor="black")

        ax.set_ylabel("Total de Tokens Consumidos", fontsize=12, fontweight="bold")
        ax.set_title("Consumo de Tokens por Tratamento de Áudio (Gemini Multimodal)", fontsize=14, fontweight="bold", pad=15)
        plt.xticks(rotation=45, ha="right", fontsize=10)

        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{int(height)}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center", va="bottom", fontsize=9, fontweight="bold")

        fig.tight_layout()
        out_path = PLOTS_DIR / "02_token_consumption.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        return out_path

    def plot_pareto_frontier(self, df: pd.DataFrame) -> Path:
        """Plots Pareto Frontier: Bandwidth Saved (%) vs. Accuracy (100 - WER)."""
        fig, ax = plt.subplots(figsize=(11, 7))

        df["accuracy"] = 100.0 - df["wer"]

        scatter = sns.scatterplot(
            data=df,
            x="bandwidth_saved_pct",
            y="accuracy",
            hue="category",
            s=150,
            style="category",
            ax=ax
        )

        for _, row in df.iterrows():
            ax.annotate(
                row["treatment_id"].split("_")[1],
                (row["bandwidth_saved_pct"], row["accuracy"]),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8
            )

        ax.set_xlabel("Economia de Largura de Banda / Compressão (%) [Maior é Melhor]", fontsize=12, fontweight="bold")
        ax.set_ylabel("Acurácia de Reconhecimento (%) [Maior é Melhor]", fontsize=12, fontweight="bold")
        ax.set_title("Fronteira de Pareto: Eficiência de Compressão vs. Qualidade da IA", fontsize=14, fontweight="bold", pad=15)
        ax.set_ylim(-5, 105)
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

        fig.tight_layout()
        out_path = PLOTS_DIR / "03_pareto_frontier.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        return out_path

    def plot_latency_breakdown(self, df: pd.DataFrame) -> Path:
        """Breakdown of Preprocessing Time vs API Latency."""
        fig, ax = plt.subplots(figsize=(12, 6))

        labels = df["treatment_label"]
        preprocess = df["preprocess_latency_sec"]
        api = df["api_latency_sec"]

        ax.bar(labels, preprocess, label="Pré-processamento MP3 (Local)", color="#3498db")
        ax.bar(labels, api, bottom=preprocess, label="Latência API Gemini (Nuvem)", color="#e74c3c")

        ax.set_ylabel("Tempo em Segundos (s)", fontsize=12, fontweight="bold")
        ax.set_title("Decomposição de Latência (Local vs. Nuvem)", fontsize=14, fontweight="bold", pad=15)
        plt.xticks(rotation=45, ha="right", fontsize=9)
        ax.legend()

        fig.tight_layout()
        out_path = PLOTS_DIR / "04_latency_breakdown.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        return out_path
