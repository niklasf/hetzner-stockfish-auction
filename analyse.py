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

def default_bench(threads, frequency) -> int:
    return (threads - 1) * frequency * 130_000

def bench(cpu: str) -> float:
    # https://openbenchmarking.org/test/pts/stockfish
    match cpu:
        case "Intel Core i7-6700":
            return default_bench(8, 3.4)
            return 3_410_450
        case "Intel Core i7-7700":
            return default_bench(8, 3.6)
        case "Intel Xeon E3-1275v5":
            return default_bench(8, 3.6)
        case "Intel Xeon E3-1275V6":
            return default_bench(8, 3.8)
        case "Intel Xeon E5-1650V3":
            return default_bench(12, 3.5)
        case "Intel Core i7-8700":
            return default_bench(12, 3.2)
        case "AMD Ryzen 5 3600":
            return default_bench(12, 3.6)
            return 7791827
        case "Intel XEON E-2176G":
            return default_bench(12, 3.7)
        case "AMD Ryzen 7 1700X" | "AMD Ryzen 7 PRO 1700X":
            return default_bench(16, 3.4)
        case "Intel XEON E-2276G":
            return default_bench(12, 3.8)
        case "Intel Core i9-9900K":
            return default_bench(16, 3.6)
        case "AMD Ryzen 7 3700X":
            return default_bench(16, 3.6)
            return 9973067
        case "Intel Core i5-12500":
            return default_bench(12, 3)
        case "Intel Xeon W-2145":
            return default_bench(16, 3.7)
        case "AMD Ryzen 7 7700":
            return default_bench(16, 3.8)
            return 15938015
        case "Intel Xeon E3-1270V3":
            return default_bench(8, 3.5)
        case "Intel Xeon E3-1271V3":
            return default_bench(8, 3.6)
        case "AMD Ryzen 9 3900":
            return default_bench(24, 3.1)
        case "AMD Ryzen Threadripper 2950X":
            return default_bench(32, 3.5)
        case "Intel Core i9-13900":
            return default_bench(32, 1.5)  # Underestimating performance cores
        case "Intel Core i9-12900K":
            return default_bench(24, 2.4)  # Underestimating performance cores
        case "AMD Ryzen 9 5950X":
            return default_bench(32, 3.4)
            return 21243912
        case "Intel Xeon Gold 5412U":
            return default_bench(48, 2.1)
        case "AMD EPYC 7401P":
            return default_bench(48, 2.0)
        case "Intel Xeon W-2295":
            return default_bench(36, 3)
        case "Intel Xeon W-2245":
            return default_bench(16, 3.9)
        case "AMD EPYC 7502" | "AMD EPYC 7502P":
            return default_bench(64, 2.5)
        case _:
            return float("inf")

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
