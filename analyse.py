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

# SIMD multipliers relative to AVX2 baseline
# (all CPUs in this dataset support at least AVX2)
_SIMD_AVX2    = 1.00
_SIMD_AVX512  = 1.10  # ~10% practical gain; throttling limits theoretical benefit
_SIMD_VNNI512 = 1.35  # VNNI4 dot-product for NNUE evaluation (Sapphire Rapids)

def default_bench(threads, frequency, simd=_SIMD_AVX2) -> int:
    return int(threads * frequency * 130_000 * simd)

def bench(cpu: str) -> float:
    # https://openbenchmarking.org/test/pts/stockfish
    # Values marked "measured" are from pts/stockfish results (previously dead code).
    # Others are scaled estimates from measured anchor points (±15-20% uncertainty).
    match cpu:
        case "Intel Core i7-6700":               # Skylake AVX2, 8t @ 3.4GHz — measured
            return 3_410_450
        case "Intel Core i7-7700":               # Kaby Lake AVX2, 8t @ 3.6GHz — scaled from i7-6700
            return 3_610_000
        case "Intel Xeon E3-1275v5":             # Skylake AVX2, 8t @ 3.6GHz — same die as i7-6700
            return 3_600_000
        case "Intel Xeon E3-1275V6":             # Kaby Lake AVX2, 8t @ 3.8GHz — scaled from i7-7700
            return 3_810_000
        case "Intel Xeon E5-1650V3":             # Haswell AVX2, 12t @ 3.5GHz — ~7% less IPC than Skylake
            return 7_000_000
        case "Intel Core i7-8700":               # Coffee Lake AVX2, 12t @ 3.2GHz
            return 4_700_000
        case "AMD Ryzen 5 3600":                 # Zen2 AVX2, 12t @ 3.6GHz — measured
            return 7_791_827
        case "Intel XEON E-2176G":               # Coffee Lake AVX2, 12t @ 3.7GHz
            return 5_430_000
        case "AMD Ryzen 7 1700X" | "AMD Ryzen 7 PRO 1700X":  # Zen1 AVX2, 16t @ 3.4GHz
            return 8_450_000
        case "Intel XEON E-2276G":               # Coffee Lake AVX2, 12t @ 3.8GHz
            return 5_580_000
        case "Intel Core i9-9900K":              # Coffee Lake AVX2, 16t @ 3.6GHz
            return 8_000_000
        case "AMD Ryzen 7 3700X":                # Zen2 AVX2, 16t @ 3.6GHz — measured
            return 9_973_067
        case "Intel Core i5-12500":              # Alder Lake AVX2 (no AVX-512), 12t hybrid
            return 5_500_000
        case "Intel Xeon W-2145":                # Skylake-W AVX-512, 16t @ 3.7GHz
            return 8_000_000
        case "AMD Ryzen 7 7700":                 # Zen4 AVX-512, 16t @ 3.8GHz — measured
            return 15_938_015
        case "Intel Xeon E3-1270V3":             # Haswell AVX2, 8t @ 3.5GHz
            return 3_270_000
        case "Intel Xeon E3-1271V3":             # Haswell AVX2, 8t @ 3.6GHz
            return 3_360_000
        case "AMD Ryzen 9 3900":                 # Zen2 AVX2, 24t @ 3.1GHz — scaled from 3700X
            return 12_900_000
        case "AMD Ryzen Threadripper 2950X":     # Zen+ AVX2, 32t @ 3.5GHz
            return 17_500_000
        case "Intel Core i9-13900":              # Raptor Lake AVX2 (no AVX-512), 32t — ~5GHz eff. boost
            return 28_000_000
        case "Intel Core i9-12900K":             # Alder Lake AVX2 (no AVX-512), 24t — ~5GHz eff. boost
            return 16_000_000
        case "AMD Ryzen 9 5950X":                # Zen3 AVX2, 32t @ 3.4GHz — measured
            return 21_243_912
        case "Intel Xeon Gold 5412U":            # Sapphire Rapids AVX-512+VNNI4, 48t @ 2.1GHz
            return 40_000_000
        case "AMD EPYC 7401P":                   # Zen1 AVX2, 48t @ 2.0GHz — scaled from 1700X
            return 17_000_000
        case "Intel Xeon W-2295":                # Cascade Lake-W AVX-512, 36t @ 3.0GHz
            return 20_000_000
        case "Intel Xeon W-2245":                # Cascade Lake-W AVX-512, 16t @ 3.9GHz
            return 12_000_000
        case "AMD EPYC 7502" | "AMD EPYC 7502P": # Rome Zen2 AVX2, 64t @ 2.5GHz — scaled from 3700X
            return 27_800_000
        case _:
            return float("inf")  # unknown CPUs sort to top as a flag to add them

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
