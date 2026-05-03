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


# SIMD multipliers relative to AVX2 baseline, calibrated from speedtest measurements.
# AMD (Zen4/5): two 256-bit pipes emulating AVX-512, modest gain.
#   Zen4: avx512 +5.4%, vnni512 +6.9%, avx512icl +6.0%
#   Zen5: avx512 +8.3%, vnni512 +10.7%, avx512icl +13.3%
# Intel consumer hybrid (Raptor Lake / Alder Lake): avxvnni is best supported arch;
#   avx512 / avx512icl NOT supported. avxvnni is 128-bit VEX-encoded VNNI, much
#   smaller gain than full 512-bit VNNI.
#   i9-13900 measured: avxvnni +1.69% over avx2.
# Intel native AVX-512 (Skylake-W, Cascade Lake-W, Sapphire Rapids):
#   W-2295 (Cascade Lake-W) measured avx512 +7.07% over avx2 → confirms _SIMD_AVX512 = 1.07.
#   vnni512 was -0.96% vs avx512 on Cascade Lake-W; avx512 is best build for this arch.
# Build selection rule:
#   AMD pre-Zen5: PEXT/PDEP is microcode-emulated → bmi2 is SLOWER than avx2; use avx2
#                 (confirmed: EPYC 7502P bmi2 was 8.9% slower; 9950X/Zen5 bmi2 was +1.1%)
#   AMD Zen5+:    PEXT/PDEP is hardware → bmi2 fine, but avx512icl/vnni512 still better
#   Intel:        PEXT/PDEP is hardware since Haswell → bmi2 fine
_SIMD_AVX2     = 1.00
_SIMD_AVXVNNI  = 1.017  # Intel consumer Raptor/Alder Lake, measured on i9-13900
_SIMD_AVX512   = 1.07   # AMD Zen4+Zen5 avg; confirmed Intel native AVX-512 (W-2295 Cascade Lake-W)
_SIMD_VNNI512  = 1.10   # AMD Zen4+Zen5 avg best build; Intel 512-bit VNNI (SPR) unmeasured


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
        case "Intel Core i5-12500":       # Alder Lake, avxvnni best (no AVX-512), 12t pure P-cores
            return 5_870_000              # ~ × ratio(12) × _SIMD_AVXVNNI; no E-cores
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
        case "Intel Core i9-13900":       # Raptor Lake, avxvnni best (no AVX-512), 8P+16E=32t
            return 18_662_000             # ★ speedtest avxvnni, 31t (1 reserved)
                                          # E-cores contribute ~3.5M total; P-cores ~15.4M
        case "Intel Core i9-12900K":      # Alder Lake, avxvnni best (no AVX-512), 8P+8E=24t
            return 16_707_000             # ~ derived from i9-13900: P-core×0.97 + 8×E-thread
        case "AMD Ryzen 9 5950X":         # Zen3, AVX2, 32t @ 3.4 GHz
            return 22_805_000             # ○ × ratio(32)
        case "Intel Xeon Gold 5412U":     # Sapphire Rapids, avx512icl, 47t @ 2.1 GHz
            return 27_400_562             # ★ avx512icl (vnni512 was 3.3% slower)
        case "AMD EPYC 7401P":            # Zen1, AVX2, 48t @ 2.0 GHz
            return 18_323_000             # ~ × ratio(48)
        case "Intel Xeon W-2295":         # Cascade Lake-W, AVX-512 native, 36t @ 3.0 GHz
            return 17_187_000             # ★ speedtest avx512, 35t (1 reserved)
        case "Intel Xeon W-2245":         # Cascade Lake-W, AVX-512 native, 16t @ 3.9 GHz
            return 9_577_000              # ~ W-2295 anchor × (15t/35t) × (3.9/3.0 GHz)
        case "AMD EPYC 7502":            # Rome/Zen2, AVX2, 64t @ 2.5 GHz
            return 33_787_000             # ★ speedtest avx2, 63t (1 reserved); bmi2 was 8.7% slower
        case "AMD EPYC 7502P":           # Rome/Zen2, AVX2, 64t @ 2.5 GHz
            return 34_275_000             # ★ speedtest avx2, 63t (1 reserved)
        case _:
            return float("inf")  # unknown CPU — flags at top of output for follow-up


def main():
    data = json.load(open("live_data_sb_EUR.json"))

    candidates = []

    for server in data["server"]:
        candidates.append(Candidate(
            id=server["id"],
            ram_size=server["ram_size"],
            price=server["price"] * 1.19 + 2.02,
            bench=bench(server["cpu"]),
            description=" | ".join(server["description"]),
        ))

    candidates.sort(key=lambda c: c.bench / c.price)

    for c in candidates:
        print(f"{c.bench / c.price:.0f} nps/€", f"{c.price:.2f} €", c.description, sep=" | ")


if __name__ == "__main__":
    main()
