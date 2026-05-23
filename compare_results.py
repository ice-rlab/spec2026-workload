#!/usr/bin/env python3

import argparse
import pathlib

import pandas as pd
import matplotlib
from matplotlib import pyplot as plt

# Color/style setup.
# Newer matplotlib versions renamed seaborn styles to seaborn-v0_8-*.
try:
    plt.style.use("seaborn-v0_8-colorblind")
except OSError:
    plt.style.use("seaborn-colorblind")

# LaTeX-like default font.
plt.rc("font", family="serif")
plt.rc("font", serif="Latin Modern Roman")
matplotlib.rcParams.update({"font.size": 18})


SPEC26_BENCHES = {
    "intspeed": [
        "801.xz_s",
        "807.ntest_s",
        "817.flac_s",
        "821.gcc_s",
        "823.llvm_s",
        "827.cppcheck_s",
        "829.abc_s",
        "834.vpr_s",
        "835.gem5_s",
        "838.diamond_s",
        "846.minizinc_s",
        "853.ns3_s",
        "854.graph500_s",
    ],
    "intrate": [
        "706.stockfish_r",
        "707.ntest_r",
        "708.sqlite_r",
        "710.omnetpp_r",
        "714.cpython_r",
        "721.gcc_r",
        "723.llvm_r",
        "727.cppcheck_r",
        "729.abc_r",
        "734.vpr_r",
        "735.gem5_r",
        "750.sealcrypto_r",
        "753.ns3_r",
        "777.zstd_r",
    ],
    "fpspeed": [
        "800.pot3d_s",
        "803.sph_exa_s",
        "809.cactus_s",
        "811.tealeaf_s",
        "816.nab_s",
        "820.cloverleaf_s",
        "822.palm_s",
        "849.fotonik3d_s",
        "857.namd_s",
        "865.roms_s",
        "867.nest_s",
        "872.marian_s",
        "881.neutron_s",
    ],
    "fprate": [
        "709.cactus_r",
        "722.palm_r",
        "731.astcenc_r",
        "736.ocio_r",
        "737.gmsh_r",
        "748.flightdm_r",
        "749.fotonik3d_r",
        "765.roms_r",
        "766.femflow_r",
        "767.nest_r",
        "772.marian_r",
        "782.lbm_r",
    ],
}


SPEC26_CLEAN_NAME = {
    # Integer speed
    "801.xz_s": "xz",
    "807.ntest_s": "ntest",
    "817.flac_s": "flac",
    "821.gcc_s": "gcc",
    "823.llvm_s": "llvm",
    "827.cppcheck_s": "cppcheck",
    "829.abc_s": "abc",
    "834.vpr_s": "vpr",
    "835.gem5_s": "gem5",
    "838.diamond_s": "diamond",
    "846.minizinc_s": "minizinc",
    "853.ns3_s": "ns3",
    "854.graph500_s": "graph500",

    # Integer rate
    "706.stockfish_r": "stockfish",
    "707.ntest_r": "ntest",
    "708.sqlite_r": "sqlite",
    "710.omnetpp_r": "omnetpp",
    "714.cpython_r": "cpython",
    "721.gcc_r": "gcc",
    "723.llvm_r": "llvm",
    "727.cppcheck_r": "cppcheck",
    "729.abc_r": "abc",
    "734.vpr_r": "vpr",
    "735.gem5_r": "gem5",
    "750.sealcrypto_r": "sealcrypto",
    "753.ns3_r": "ns3",
    "777.zstd_r": "zstd",

    # Floating-point speed
    "800.pot3d_s": "pot3d",
    "803.sph_exa_s": "sph_exa",
    "809.cactus_s": "cactus",
    "811.tealeaf_s": "tealeaf",
    "816.nab_s": "nab",
    "820.cloverleaf_s": "cloverleaf",
    "822.palm_s": "palm",
    "849.fotonik3d_s": "fotonik3d",
    "857.namd_s": "namd",
    "865.roms_s": "roms",
    "867.nest_s": "nest",
    "872.marian_s": "marian",
    "881.neutron_s": "neutron",

    # Floating-point rate
    "709.cactus_r": "cactus",
    "722.palm_r": "palm",
    "731.astcenc_r": "astcenc",
    "736.ocio_r": "ocio",
    "737.gmsh_r": "gmsh",
    "748.flightdm_r": "flightdm",
    "749.fotonik3d_r": "fotonik3d",
    "765.roms_r": "roms",
    "766.femflow_r": "femflow",
    "767.nest_r": "nest",
    "772.marian_r": "marian",
    "782.lbm_r": "lbm",
}


def load_files(files, suite):
    dfs = []

    for name, path in files.items():
        new_df = pd.read_csv(path, index_col=0)
        new_df.index.rename("Benchmark", inplace=True)

        # Keep only benchmarks expected for this suite if present.
        expected = SPEC26_BENCHES[suite]
        present = [b for b in expected if b in new_df.index]
        if present:
            new_df = new_df.loc[present]

        new_df = (
            new_df
            .assign(Experiment=name)
            .set_index("Experiment", append=True)
            .swaplevel(0, 1)
        )

        dfs.append(new_df)

    full_df = pd.concat(dfs)
    full_df.rename(index=SPEC26_CLEAN_NAME, inplace=True)
    return full_df


def make_hatches(ax, df):
    hatch_patterns = ["//", "--", "x", "\\", "||", "+", "o", "."]
    hatches = []

    while len(hatches) < len(ax.patches):
        for hatch in hatch_patterns:
            hatches.extend([hatch] * len(df.index))

    for i, bar in enumerate(ax.patches):
        bar.set_hatch(hatches[i])

    ax.legend()


def plot_res(res_df, suite, output_path):
    scores = res_df.loc[pd.IndexSlice[:, :], "score"].unstack(level=0)

    plot = scores.plot(kind="bar")
    make_hatches(plot, scores)

    plot.set_ylabel("SPEC CPU 2026 Score")
    plot.set_title(f"SPEC CPU 2026 {suite}")
    plot.set_xticklabels(scores.index, rotation=45, ha="right")

    plot.get_figure().savefig(output_path, bbox_inches="tight", format="pdf")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare results from multiple SPEC CPU 2026 workload runs"
    )

    parser.add_argument(
        "-s",
        "--suite",
        required=True,
        choices=["intspeed", "intrate", "fpspeed", "fprate"],
        help="Which SPEC CPU 2026 suite was run.",
    )

    parser.add_argument(
        "-d",
        "--dataset",
        required=False,
        default=None,
        help=(
            "Dataset used, e.g. test/train/ref. Kept for CLI compatibility; "
            "this script only compares already-produced results.csv files."
        ),
    )

    parser.add_argument(
        "-n",
        "--names",
        nargs="?",
        default=None,
        type=lambda s: [item for item in s.split(",")],
        help=(
            "Comma-separated list of names to display for results. "
            "If omitted, the parent directory name is used."
        ),
    )

    parser.add_argument(
        "-o",
        "--output",
        default="result.pdf",
        type=pathlib.Path,
        help="Output PDF path. Default: result.pdf",
    )

    parser.add_argument(
        "resultPaths",
        nargs="+",
        type=pathlib.Path,
        help="Paths to results.csv files produced by handle-results.py",
    )

    args = parser.parse_args()

    if args.names is None:
        args.names = [p.parent.name for p in args.resultPaths]

    if len(args.names) != len(args.resultPaths):
        raise RuntimeError(
            f"Number of names ({len(args.names)}) does not match number of "
            f"result paths ({len(args.resultPaths)})"
        )

    datasets = {
        name: path
        for name, path in zip(args.names, args.resultPaths)
    }

    res_df = load_files(datasets, suite=args.suite)
    plot_res(res_df, suite=args.suite, output_path=args.output)

    print("Output available in:", args.output)