#!/usr/bin/env python3

import json
import dataclasses

@dataclasses.dataclass
class Candidate:
    id: int
    ram_size: int
    price: int
    bench: float
    description: str

# SIMD multipliers relative to AVX2 baseline, calibrated from speedtest measurements
# on Ryzen 7 7700 (Zen4) and Ryzen 9 9950X (Zen5):
#   Zen4: avx512 +5.4%, vnni512 +6.9%, avx512icl +6.0%
#   Zen5: avx512 +8.3%, vnni512 +10.7%, avx512icl +13.3%
# AMD Zen4/5 implement AVX-512 as two 256-bit pipes, limiting gain vs native.
# Intel native AVX-512 (Skylake-W, Cascade Lake-W, Sapphire Rapids) is unmeasured;
# using same factors as conservative estimate.
_SIMD_AVX2    = 1.00
_SIMD_AVX512  = 1.07   # avg across Zen4+Zen5 avx512 builds
_SIMD_VNNI512 = 1.10   # avg across Zen4+Zen5 best builds; Intel VNNI may be higher

# Constant calibrated to return Nodes/second matching stockfish speedtest output.
# Anchor: Ryzen 7 7700 (16t, 3.8 GHz base), speedtest avx2 = 17,315,222 N/s
# → 17,315,222 / (16 × 3.8) ≈ 284,790 → 285,000
# Cross-check: Ryzen 9 9950X (32t, 4.3 GHz base), predicted 39.2M vs measured 33.9M (+16%)
# — overestimate expected since all-core boost is well below base for 32-thread load.
_NODES_PER_THREAD_GHZ = 285_000

def default_bench(threads, frequency, simd=_SIMD_AVX2) -> int:
    return int(threads * frequency * _NODES_PER_THREAD_GHZ * simd)

def bench(cpu: str) -> float:
    # Values in Nodes/second as reported by: stockfish speedtest
    # using Stockfish dev-20260307-b3a810a1, best applicable SIMD build.
    #
    # Directly measured (★): from speedtest files in speedtest/
    # Scaled from pts/stockfish (○): old openbenchmarking.org values × 1.086
    #   (calibration factor: speedtest-avx2 / pts-stockfish for Ryzen 7 7700)
    # Estimated (~): architectural scaling from measured anchors, ±15-20%
    match cpu:
        case "Intel Core i7-6700":        # Skylake, AVX2, 8t @ 3.4 GHz
            return 3_704_000              # ○ pts/stockfish × 1.086
        case "Intel Core i7-7700":        # Kaby Lake, AVX2, 8t @ 3.6 GHz
            return 3_920_000              # ~ scaled from i7-6700 × (3.6/3.4)
        case "Intel Xeon E3-1275v5":      # Skylake, AVX2, 8t @ 3.6 GHz
            return 3_910_000              # ~ same die as i7-6700 × (3.6/3.4)
        case "Intel Xeon E3-1275V6":      # Kaby Lake, AVX2, 8t @ 3.8 GHz
            return 4_138_000              # ~ scaled from i7-7700 × (3.8/3.6)
        case "Intel Xeon E5-1650V3":      # Haswell, AVX2, 12t @ 3.5 GHz
            return 7_602_000              # ~ Haswell ~7% lower IPC than Skylake
        case "Intel Core i7-8700":        # Coffee Lake, AVX2, 12t @ 3.2 GHz
            return 5_104_000              # ~ scaled from i7-6700 lineage
        case "AMD Ryzen 5 3600":          # Zen2, AVX2, 12t @ 3.6 GHz
            return 8_462_000              # ○ pts/stockfish × 1.086
        case "Intel XEON E-2176G":        # Coffee Lake, AVX2, 12t @ 3.7 GHz
            return 5_897_000              # ~ scaled from i7-8700 × (3.7/3.2)
        case "AMD Ryzen 7 1700X" | "AMD Ryzen 7 PRO 1700X":  # Zen1, AVX2, 16t @ 3.4 GHz
            return 9_177_000              # ~ scaled from 3700X × (16/16) × (3.4/3.6) × 0.90 IPC
        case "Intel XEON E-2276G":        # Coffee Lake, AVX2, 12t @ 3.8 GHz
            return 6_060_000              # ~ scaled from E-2176G × (3.8/3.7)
        case "Intel Core i9-9900K":       # Coffee Lake, AVX2, 16t @ 3.6 GHz
            return 8_688_000              # ~ scaled from i7-8700 × (16/12) × (3.6/3.2)
        case "AMD Ryzen 7 3700X":         # Zen2, AVX2, 16t @ 3.6 GHz
            return 10_831_000             # ○ pts/stockfish × 1.086
        case "Intel Core i5-12500":       # Alder Lake, AVX2 only (no AVX-512), 12t hybrid
            return 5_973_000              # ~ P+E hybrid; effective throughput estimate
        case "Intel Xeon W-2145":         # Skylake-W, AVX-512 native, 16t @ 3.7 GHz
            return 9_296_000              # ~ avx2 base × 1.086 × _SIMD_AVX512
        case "AMD Ryzen 7 7700":          # Zen4, AVX-512, 16t @ 3.8 GHz
            return 18_504_000             # ★ speedtest vnni512 (best build for Zen4)
        case "Intel Xeon E3-1270V3":      # Haswell, AVX2, 8t @ 3.5 GHz
            return 3_551_000              # ~ scaled from i7-6700 × (3.5/3.4) × 0.93 IPC
        case "Intel Xeon E3-1271V3":      # Haswell, AVX2, 8t @ 3.6 GHz
            return 3_649_000              # ~ scaled from i7-6700 × (3.6/3.4) × 0.93 IPC
        case "AMD Ryzen 9 3900":          # Zen2, AVX2, 24t @ 3.1 GHz
            return 14_009_000             # ~ scaled from 3700X × (24/16) × (3.1/3.6)
        case "AMD Ryzen Threadripper 2950X":  # Zen+, AVX2, 32t @ 3.5 GHz
            return 19_005_000             # ~ scaled from 1700X × 2 × (3.5/3.4) × 1.03
        case "Intel Core i9-13900":       # Raptor Lake, AVX2 only (no AVX-512), 32t hybrid
            return 30_408_000             # ~ boost-clock estimate (base 1.5 GHz misleading)
        case "Intel Core i9-12900K":      # Alder Lake, AVX2 only (no AVX-512), 24t hybrid
            return 17_376_000             # ~ boost-clock estimate
        case "AMD Ryzen 9 5950X":         # Zen3, AVX2, 32t @ 3.4 GHz
            return 23_071_000             # ○ pts/stockfish × 1.086
        case "Intel Xeon Gold 5412U":     # Sapphire Rapids, VNNI4 native, 48t @ 2.1 GHz
            return 47_800_000             # ~ base × 1.086 × _SIMD_VNNI512 (Intel native may be higher)
        case "AMD EPYC 7401P":            # Zen1, AVX2, 48t @ 2.0 GHz
            return 18_462_000             # ~ scaled from 1700X × 3 × (2.0/3.4) × 1.086
        case "Intel Xeon W-2295":         # Cascade Lake-W, AVX-512 native, 36t @ 3.0 GHz
            return 23_240_000             # ~ base × 1.086 × _SIMD_AVX512
        case "Intel Xeon W-2245":         # Cascade Lake-W, AVX-512 native, 16t @ 3.9 GHz
            return 13_944_000             # ~ base × 1.086 × _SIMD_AVX512
        case "AMD EPYC 7502" | "AMD EPYC 7502P":  # Rome/Zen2, AVX2, 64t @ 2.5 GHz
            return 30_191_000             # ~ scaled from 3700X × (64/16) × (2.5/3.6) × 1.086
        case _:
            return float("inf")  # unknown CPU — flags at top of output for follow-up

def main():
    data = json.load(open("live_data_sb_EUR.json"))

    candidates = []

    for server in data["server"]:
        candidates.append(Candidate(
            id=server["id"],
            ram_size=server["ram_size"],
            price=server["price"] * 1.19,
            bench=bench(server["cpu"]),
            description=" | ".join(server["description"]),
            #description=server["cpu"],
        ))

    candidates.sort(key=lambda c: c.bench / c.price)

    for c in candidates:
        print(c.id, c.bench / c.price, f"{c.price} €", c.description, sep=" | ")

if __name__ == "__main__":
    main()
