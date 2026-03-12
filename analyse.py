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

# 1 thread is reserved for plumbing (OS, Stockfish I/O thread, etc.).
# The remaining threads run slightly super-linearly: dropping 1 thread from N costs
# less than 1/N of performance because synchronization overhead is reduced.
# Measured on avx512icl build:
#   Ryzen 7 7700:  16t=18,361,890 → 15t=17,878,551 (-2.6% vs -6.25% linear)
#   Ryzen 9 9950X: 32t=38,357,048 → 31t=37,954,386 (-1.1% vs -3.1% linear)
# Model: ratio(N) = (N-1)/N × (1 + 0.651/N), fit to both data points.
#
# All bench() values below reflect (threads-1) usage with the best applicable
# Stockfish build, in Nodes/second as reported by: stockfish speedtest
# using Stockfish dev-20260307-b3a810a1.

# Constant calibrated so default_bench(16, 3.8) ≈ Ryzen 7 7700 speedtest-avx2 at 15t
# = 17,315,222 / 15 / 3.8 ≈ 314,000. (Using avx2 so SIMD multiplier applies on top.)
_NODES_PER_THREAD_GHZ = 314_000

def default_bench(threads, frequency, simd=_SIMD_AVX2) -> int:
    # 1 thread reserved for plumbing
    return int((threads - 1) * frequency * _NODES_PER_THREAD_GHZ * simd)

def bench(cpu: str) -> float:
    # Nodes/second with 1 thread reserved for plumbing, best applicable SIMD build.
    #
    # Directly measured (★): from speedtest files in speedtest/
    # Scaled from pts/stockfish (○): old openbenchmarking.org value × 1.086
    #   (avx2 speedtest / pts-stockfish for Ryzen 7 7700) × ratio(N)
    # Estimated (~): architectural scaling × ratio(N), ±15-20%
    #
    # ratio(N) = (N-1)/N × (1 + 0.651/N) — superlinear scaling model
    match cpu:
        case "Intel Core i7-6700":        # Skylake, AVX2, 8t @ 3.4 GHz
            return 3_505_000              # ○ × ratio(8)=0.946
        case "Intel Core i7-7700":        # Kaby Lake, AVX2, 8t @ 3.6 GHz
            return 3_709_000              # ~ × ratio(8)
        case "Intel Xeon E3-1275v5":      # Skylake, AVX2, 8t @ 3.6 GHz
            return 3_700_000              # ~ × ratio(8)
        case "Intel Xeon E3-1275V6":      # Kaby Lake, AVX2, 8t @ 3.8 GHz
            return 3_915_000              # ~ × ratio(8)
        case "Intel Xeon E5-1650V3":      # Haswell, AVX2, 12t @ 3.5 GHz
            return 7_347_000              # ~ × ratio(12)=0.966
        case "Intel Core i7-8700":        # Coffee Lake, AVX2, 12t @ 3.2 GHz
            return 4_932_000              # ~ × ratio(12)
        case "AMD Ryzen 5 3600":          # Zen2, AVX2, 12t @ 3.6 GHz
            return 8_178_000              # ○ × ratio(12)
        case "Intel XEON E-2176G":        # Coffee Lake, AVX2, 12t @ 3.7 GHz
            return 5_699_000              # ~ × ratio(12)
        case "AMD Ryzen 7 1700X" | "AMD Ryzen 7 PRO 1700X":  # Zen1, AVX2, 16t @ 3.4 GHz
            return 8_953_000              # ~ × ratio(16)=0.976
        case "Intel XEON E-2276G":        # Coffee Lake, AVX2, 12t @ 3.8 GHz
            return 5_856_000              # ~ × ratio(12)
        case "Intel Core i9-9900K":       # Coffee Lake, AVX2, 16t @ 3.6 GHz
            return 8_476_000              # ~ × ratio(16)
        case "AMD Ryzen 7 3700X":         # Zen2, AVX2, 16t @ 3.6 GHz
            return 10_567_000             # ○ × ratio(16)
        case "Intel Core i5-12500":       # Alder Lake, AVX2 only (no AVX-512), 12t hybrid
            return 5_772_000              # ~ × ratio(12)
        case "Intel Xeon W-2145":         # Skylake-W, AVX-512 native, 16t @ 3.7 GHz
            return 9_070_000              # ~ avx2 × 1.086 × _SIMD_AVX512 × ratio(16)
        case "AMD Ryzen 7 7700":          # Zen4, AVX-512, 16t @ 3.8 GHz
            return 17_879_000             # ★ speedtest avx512icl, 15t (1 reserved)
        case "Intel Xeon E3-1270V3":      # Haswell, AVX2, 8t @ 3.5 GHz
            return 3_360_000              # ~ × ratio(8)
        case "Intel Xeon E3-1271V3":      # Haswell, AVX2, 8t @ 3.6 GHz
            return 3_453_000              # ~ × ratio(8)
        case "AMD Ryzen 9 3900":          # Zen2, AVX2, 24t @ 3.1 GHz
            return 13_789_000             # ~ × ratio(24)=0.984
        case "AMD Ryzen Threadripper 2950X":  # Zen+, AVX2, 32t @ 3.5 GHz
            return 18_786_000             # ~ × ratio(32)=0.989
        case "Intel Core i9-13900":       # Raptor Lake, AVX2 only (no AVX-512), 32t hybrid
            return 30_057_000             # ~ boost-clock estimate × ratio(32)
        case "Intel Core i9-12900K":      # Alder Lake, AVX2 only (no AVX-512), 24t hybrid
            return 17_104_000             # ~ boost-clock estimate × ratio(24)
        case "AMD Ryzen 9 5950X":         # Zen3, AVX2, 32t @ 3.4 GHz
            return 22_805_000             # ○ × ratio(32)
        case "Intel Xeon Gold 5412U":     # Sapphire Rapids, VNNI4 native, 48t @ 2.1 GHz
            return 47_439_000             # ~ base × 1.086 × _SIMD_VNNI512 × ratio(48)=0.992
        case "AMD EPYC 7401P":            # Zen1, AVX2, 48t @ 2.0 GHz
            return 18_323_000             # ~ × ratio(48)
        case "Intel Xeon W-2295":         # Cascade Lake-W, AVX-512 native, 36t @ 3.0 GHz
            return 23_003_000             # ~ base × 1.086 × _SIMD_AVX512 × ratio(36)=0.990
        case "Intel Xeon W-2245":         # Cascade Lake-W, AVX-512 native, 16t @ 3.9 GHz
            return 13_604_000             # ~ base × 1.086 × _SIMD_AVX512 × ratio(16)
        case "AMD EPYC 7502" | "AMD EPYC 7502P":  # Rome/Zen2, AVX2, 64t @ 2.5 GHz
            return 30_022_000             # ~ × ratio(64)=0.994
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
        ))

    candidates.sort(key=lambda c: c.bench / c.price)

    for c in candidates:
        print(c.id, c.bench / c.price, f"{c.price} €", c.description, sep=" | ")

if __name__ == "__main__":
    main()
