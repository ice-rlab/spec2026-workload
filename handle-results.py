#!/usr/bin/env python3

import argparse
import os
import pathlib
import re
import sys

import pandas as pd

# All time measurements are in seconds.

SPEC26_SUITES = {
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


def read_reftime_file(path: pathlib.Path) -> float:
    """
    Read a SPEC reftime file.

    Different benchmarks may have one or more numeric entries. For this
    workload aggregator, treat multiple entries as pieces of the benchmark and
    sum them into one reference runtime.
    """
    text = path.read_text()

    values = []
    for line in text.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        # Extract numeric tokens robustly.
        for tok in re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", line):
            values.append(float(tok))

    if not values:
        raise RuntimeError(f"No numeric reference time found in {path}")

    return sum(values)


def load_spec26_reftime_baseline(suite: str, dataset: str) -> pd.DataFrame:
    """
    Load reference times from $SPEC_26_DIR/benchspec/CPU/*/data/<dataset>/reftime.
    """
    spec_dir_env = os.environ.get("SPEC_26_DIR")
    if not spec_dir_env:
        raise RuntimeError(
            "SPEC_26_DIR is not set. Set it or pass a baseline CSV as --dataset."
        )

    spec_dir = pathlib.Path(spec_dir_env)
    rows = {}

    for bmark in SPEC26_SUITES[suite]:
        reftime = spec_dir / "benchspec" / "CPU" / bmark / "data" / dataset / "reftime"

        if not reftime.exists():
            raise RuntimeError(f"Missing reftime file for {bmark}: {reftime}")

        rows[bmark] = read_reftime_file(reftime)

    return pd.DataFrame.from_dict(rows, orient="index", columns=["RealTime"])


def load_baseline(suite: str, dataset: str) -> pd.DataFrame:
    """
    dataset can be:
      - test/train/ref: load from SPEC_26_DIR reftime files
      - path/to/baseline.csv: load previous output CSV as baseline
    """
    if dataset in ("test", "train", "ref"):
        return load_spec26_reftime_baseline(suite, dataset)

    baseline_path = pathlib.Path(dataset)
    if not baseline_path.exists():
        raise RuntimeError(f"Baseline CSV does not exist: {dataset}")

    baseline = pd.read_csv(baseline_path, index_col=0)

    if "RealTime" not in baseline.columns:
        raise RuntimeError(f"Baseline CSV must contain a RealTime column: {dataset}")

    return baseline


def load_output_csvs(out_dir: pathlib.Path) -> pd.DataFrame:
    csv_files = sorted(out_dir.glob("*/output/*.csv"))

    if not csv_files:
        # Also support being pointed directly at a single workload output dir.
        csv_files = sorted((out_dir / "output").glob("*.csv"))

    if not csv_files:
        raise RuntimeError(f"No CSV files found under {out_dir}")

    dfs = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)

        if "name" not in df.columns:
            # Handles CSVs written with benchmark name as index.
            df = pd.read_csv(csv_file, index_col=0)
            df = df.reset_index().rename(columns={"index": "name"})

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def handle_speed(out_dir: pathlib.Path, suite: str, dataset: str) -> pd.DataFrame:
    baseline = load_baseline(suite, dataset)
    raw = load_output_csvs(out_dir)

    required_cols = {"name", "RealTime"}
    missing = required_cols - set(raw.columns)
    if missing:
        raise RuntimeError(f"Missing required columns in output CSVs: {sorted(missing)}")

    # For speed suites, if multiple rows exist for the same benchmark, treat them
    # as split workload pieces and sum their runtime.
    grouped = raw.groupby("name", as_index=True).agg({
        "RealTime": "sum",
        "UserTime": "sum" if "UserTime" in raw.columns else "first",
        "KernelTime": "sum" if "KernelTime" in raw.columns else "first",
    })

    grouped = grouped.loc[grouped.index.intersection(baseline.index)].copy()

    missing_bmarks = sorted(set(SPEC26_SUITES[suite]) - set(grouped.index))
    if missing_bmarks:
        print(
            "WARNING: missing benchmark results:",
            " ".join(missing_bmarks),
            file=sys.stderr,
        )

    grouped["score"] = baseline.loc[grouped.index, "RealTime"] / grouped["RealTime"]
    grouped.sort_index(inplace=True)
    return grouped


def handle_rate(out_dir: pathlib.Path, suite: str, dataset: str) -> pd.DataFrame:
    baseline = load_baseline(suite, dataset)
    raw = load_output_csvs(out_dir)

    required_cols = {"name", "RealTime"}
    missing = required_cols - set(raw.columns)
    if missing:
        raise RuntimeError(f"Missing required columns in output CSVs: {sorted(missing)}")

    name_groups = raw.groupby("name")

    # For rate, the benchmark runtime is the slowest copy.
    slowest = raw[name_groups["RealTime"].transform("max") == raw["RealTime"]].copy()
    slowest = slowest.drop_duplicates(subset=["name"])
    slowest.set_index("name", inplace=True)

    # Count copies. Prefer explicit copy column if present, otherwise count rows.
    if "copy" in raw.columns:
        ncopy = name_groups["copy"].nunique().rename("ncopy")
    else:
        ncopy = name_groups.size().rename("ncopy")

    res = pd.concat([slowest, ncopy], axis=1)
    res = res.loc[res.index.intersection(baseline.index)].copy()

    missing_bmarks = sorted(set(SPEC26_SUITES[suite]) - set(res.index))
    if missing_bmarks:
        print(
            "WARNING: missing benchmark results:",
            " ".join(missing_bmarks),
            file=sys.stderr,
        )

    res["score"] = (
        baseline.loc[res.index, "RealTime"] / res["RealTime"]
    ) * res["ncopy"]

    res.sort_index(inplace=True)
    return res


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Aggregate results from a run of a SPEC CPU 2026 suite"
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
        required=True,
        help=(
            "Dataset used: test, train, ref. "
            "Alternatively, pass a path to a previous results.csv to use as baseline."
        ),
    )

    parser.add_argument(
        "outputPath",
        type=pathlib.Path,
        help="Output directory to process",
    )

    args = parser.parse_args()

    if args.suite.endswith("speed"):
        res_df = handle_speed(args.outputPath, suite=args.suite, dataset=args.dataset)
    elif args.suite.endswith("rate"):
        res_df = handle_rate(args.outputPath, suite=args.suite, dataset=args.dataset)
    else:
        raise RuntimeError(f"Unhandled suite: {args.suite}")

    results_csv = args.outputPath / "results.csv"
    results_pdf = args.outputPath / "results.pdf"

    with open(results_csv, "w") as f:
        f.write(res_df.to_csv())

    plot = res_df["score"].plot(kind="bar", title=f"SPEC CPU 2026 {args.suite} Score")
    plot.get_figure().savefig(results_pdf, bbox_inches="tight")

    print("Output available in:", args.outputPath)