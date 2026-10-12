"""Visualization utilities and LaTeX asset rendering for PS-C1.

Generates:
- Processor coupling graphs (Processor A, B, D)
- Ideal VQE convergence plots
- A/B/D compiled metric comparisons
- Error mitigation before-and-after progression (achieving chemical accuracy)
- 4-qubit molecular routing overhead charts (showing SWAP and depth bottlenecks)
- Placement sensitivity graphs
- High-resolution LaTeX asset equations for the submission package
"""
from pathlib import Path
from typing import Dict, List
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "results" / "figures"
ASSETS_DIR = ROOT / "assets" / "qff_phase1_latex_images"


def plot_processor_graph(proc: dict, ax, highlight_nodes: List[int] = None):
    """Draw a network graph of a processor topology."""
    G = nx.Graph()
    G.add_nodes_from(range(proc["num_qubits"]))
    G.add_edges_from([tuple(e) for e in proc["coupling_map"]])
    
    pos = nx.kamada_kawai_layout(G)
    colors = []
    for n in G.nodes():
        if highlight_nodes and n in highlight_nodes:
            colors.append("#ff7f0e")  # Orange for active core
        else:
            colors.append("#1f77b4" if n < 4 else "#aec7e8")

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=colors, node_size=650, alpha=0.9)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#7f7f7f", width=1.5)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=11, font_color="white", font_weight="bold")
    ax.set_title(f"{proc['name'].replace('_', ' ').title()}\n({proc['num_qubits']} Qubits, {len(proc['coupling_map'])} Edges)", fontsize=12)
    ax.axis("off")


def save_processor_graphs(procs: Dict[str, dict]):
    """Save combined coupling map figure for Processors A, B, and D."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(1, len(procs), figsize=(5.5 * len(procs), 4.8), dpi=150)
    if len(procs) == 1:
        axs = [axs]
    for ax, (name, proc) in zip(axs, procs.items()):
        core = [0, 1, 2, 3] if name == "processor_D" else None
        plot_processor_graph(proc, ax, highlight_nodes=core)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "processor_A_B_graphs.png", bbox_inches="tight")
    plt.close(fig)


def plot_vqe_convergence(histories: Dict[str, list], exact_energy: float):
    """Plot energy convergence during ideal VQE optimization."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    for label, hist in histories.items():
        ax.plot(hist, label=label, lw=1.8)
    ax.axhline(exact_energy, color="black", linestyle="--", lw=1.5, label=f"Exact FCI ({exact_energy:.4f} Ha)")
    ax.set_xlabel("Optimizer Iteration (COBYLA)", fontsize=11)
    ax.set_ylabel("Energy (Hartree)", fontsize=11)
    ax.set_title("VQE Optimization Convergence for H₂ Ground State", fontsize=12)
    ax.legend(frameon=True, fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "vqe_convergence.png", bbox_inches="tight")
    plt.close(fig)


def plot_error_mitigation_results(df_mit: pd.DataFrame, chem_acc: float):
    """Bar chart demonstrating error reduction to reach chemical accuracy."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=150)
    stages = df_mit["stage"].tolist()
    errors_mha = (df_mit["energy_error_hartree"] * 1000.0).tolist()
    colors = ["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4"]

    bars = ax.bar(stages, errors_mha, color=colors[:len(stages)], width=0.55, edgecolor="black", alpha=0.85)
    ax.axhline(chem_acc * 1000.0, color="crimson", linestyle="--", lw=2, label=f"Chemical Accuracy ({chem_acc*1000:.1f} mHa)")

    for bar, val in zip(bars, errors_mha):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.6, f"{val:.2f} mHa",
                ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_ylabel("Absolute Energy Error |E - E_exact| (mHa)", fontsize=11)
    ax.set_title("Impact of Quantum Error Mitigation on Ground-State Energy (PS-C1)", fontsize=12)
    ax.set_ylim(0, max(errors_mha) * 1.25)
    ax.legend(frameon=True, fontsize=10, loc="upper right")
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "error_mitigation_comparison.png", bbox_inches="tight")
    plt.close(fig)


def plot_4qubit_routing_overhead(df_routing: pd.DataFrame):
    """Bar chart comparing CX count, SWAP insertions, and depth on Processors A, B, D."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.2), dpi=150)
    procs = [p.replace("processor_", "Proc ") for p in df_routing["architecture"]]

    # CX count
    axs[0].bar(procs, df_routing["compiled_cx"], color="#1f77b4", edgecolor="black", alpha=0.85)
    axs[0].axhline(6, color="green", linestyle="--", label="Logical CX (6)")
    axs[0].set_ylabel("Compiled Two-Qubit (CX) Gates", fontsize=11)
    axs[0].set_title("CX Gate Overhead", fontsize=12)
    axs[0].legend(fontsize=9)
    axs[0].grid(axis="y", linestyle=":", alpha=0.6)

    # SWAP count
    axs[1].bar(procs, df_routing["swap_count"], color="#ff7f0e", edgecolor="black", alpha=0.85)
    axs[1].set_ylabel("SWAP Gates Inserted", fontsize=11)
    axs[1].set_title("Routing SWAP Overhead", fontsize=12)
    axs[1].grid(axis="y", linestyle=":", alpha=0.6)

    # Depth
    axs[2].bar(procs, df_routing["compiled_depth"], color="#2ca02c", edgecolor="black", alpha=0.85)
    axs[2].set_ylabel("Compiled Circuit Depth", fontsize=11)
    axs[2].set_title("Circuit Depth", fontsize=12)
    axs[2].grid(axis="y", linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(FIG_DIR / "routing_overhead_4q.png", bbox_inches="tight")
    plt.close(fig)


def render_latex_assets():
    """Render the 6 mandatory LaTeX equation assets required in Phase 1 Section 5.1."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    eq_specs = {
        "eq_qubit_state.png": r"$|\psi\rangle = \alpha |0\rangle + \beta |1\rangle, \quad |\alpha|^2 + |\beta|^2 = 1$",
        "eq_bell_state.png": r"$|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$",
        "eq_graph.png": r"$G = (V, E), \quad E \subseteq \{\{u, v\} : u, v \in V\}$",
        "eq_bell_fidelity.png": r"$F(|\Phi^+\rangle, \rho) = \frac{1}{4}\left(1 + \langle XX\rangle - \langle YY\rangle + \langle ZZ\rangle\right)$",
        "eq_zz_expectation.png": r"$\langle Z_i Z_j \rangle = \frac{N_{00} + N_{11} - N_{01} - N_{10}}{N_{\mathrm{shots}}}$",
        "eq_standard_error.png": r"$\sigma_{\bar{E}} = \frac{\sigma}{\sqrt{N_{\mathrm{runs}}}} = \sqrt{\frac{\mathrm{Var}(E)}{N_{\mathrm{runs}}}}$"
    }

    for fname, latex in eq_specs.items():
        fig = plt.figure(figsize=(4.5, 0.9), dpi=200)
        fig.text(0.5, 0.5, latex, fontsize=15, ha="center", va="center")
        plt.axis("off")
        plt.savefig(ASSETS_DIR / fname, bbox_inches="tight", transparent=True)
        plt.close(fig)
