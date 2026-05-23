#!/bin/bash

set -ex

if [ $# -lt 2 ]; then
    echo "usage: build-spec.sh <intrate|intspeed|fprate|fpspeed> <ref|test|train> [benchmark]"
    echo ""
    echo "examples:"
    echo "  build-spec.sh intrate test"
    echo "  build-spec.sh intrate test 706.stockfish_r"
    echo "  build-spec.sh fpspeed ref 803.sph_exa_s"
    exit 1
fi

SUITE=$1
INPUT=$2
BENCHMARK=${3:-}

case "${SUITE}" in
    intrate|intspeed|fprate|fpspeed)
        ;;
    *)
        echo "ERROR: bad suite '${SUITE}'"
        echo "Expected one of: intrate intspeed fprate fpspeed"
        exit 1
        ;;
esac

case "${INPUT}" in
    ref|test|train)
        ;;
    *)
        echo "ERROR: bad input '${INPUT}'"
        echo "Expected one of: ref test train"
        exit 1
        ;;
esac

if [ -n "${BENCHMARK}" ]; then
    echo "Building SPEC CPU 2026 ${SUITE} benchmark ${BENCHMARK} with ${INPUT} inputs"
    make spec-benchmark INPUT="${INPUT}" SUITE="${SUITE}" BENCHMARK="${BENCHMARK}"
else
    echo "Building SPEC CPU 2026 ${SUITE} with ${INPUT} inputs"
    make "spec-${SUITE}" INPUT="${INPUT}"
fi