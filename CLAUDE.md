# hetzner-watch

Ranks Hetzner dedicated server auction offers by Stockfish cost-efficiency (Nodes/second per €).

## What it does

- `make update` — fetches live auction data from Hetzner into `live_data_sb_EUR.json`
- `make analyse` — runs `analyse.py`, prints all servers sorted ascending by N/s per € (best value last)

## analyse.py structure

`bench(cpu)` returns estimated Stockfish throughput in **Nodes/second** for a given CPU model string, as reported by `stockfish speedtest`. Values reflect **threads-1** usage (1 thread reserved for plumbing/OS).

`default_bench(threads, frequency, simd)` is a calibrated fallback formula for CPUs not in the match statement. It is not called for any known CPU — only used manually for sanity checks.

## Calibration basis

All values are in N/s matching `stockfish dev-20260307-b3a810a1` speedtest output.

**Measured directly (★)** — from files in `speedtest/`:
- AMD Ryzen 7 7700: 17,879,000 N/s (15t avx512icl)
- AMD Ryzen 9 9950X: not in auction dataset, used for SIMD calibration only

**Scaled from pts/stockfish (○)** — openbenchmarking.org values × 1.086 × ratio(N):
- i7-6700, Ryzen 5 3600, Ryzen 7 3700X, Ryzen 9 5950X

**Estimated (~)** — architectural scaling from measured anchors, ±15–20% uncertainty:
- everything else

## SIMD multipliers (measured)

From speedtest on Ryzen 7 7700 (Zen4) and Ryzen 9 9950X (Zen5):

| Build | Zen4 | Zen5 | Used |
|-------|------|------|------|
| avx512 vs avx2 | +5.4% | +8.3% | **1.07** |
| vnni512/avx512icl vs avx2 | +6.9% | +13.3% | **1.10** |

AMD Zen4/5 implement AVX-512 as two 256-bit pipes — gains are modest.
Intel native AVX-512 (Skylake-W, Cascade Lake-W, Sapphire Rapids) applies the same factors as a conservative estimate; **unmeasured**.

**Intel consumer hybrid (Raptor Lake / Alder Lake) — critical finding:**
- These CPUs do **not** support AVX-512. Best Stockfish build is `x86-64-avxvnni`.
- avxvnni is 128-bit VEX-encoded VNNI — measured gain over avx2: only **+1.69%** (i9-13900).
- E-cores (Efficient cores) contribute negligibly to Stockfish throughput. On the i9-13900 (8P+16E), the marginal last thread adds only ~216k N/s (1.1% of total). All 16 E-cores together contribute ~3.5M N/s; the 8 P-cores contribute ~15.4M N/s.
- Consequence: i9-13900 actual = **18.7M N/s** — the old boost-clock estimate (30M) was 38% too high.
- Apply same model to i9-12900K (8P+8E): fewer E-cores, P-core ~3% slower → ~16.7M N/s.

## Plumbing thread model

Removing 1 thread costs less than 1/N performance due to reduced sync overhead (superlinear remaining scaling). Fit to two measurements:

```
ratio(N) = (N-1)/N × (1 + 0.651/N)
```

| Threads | Ratio | Performance loss |
|---------|-------|-----------------|
| 8  | 0.946 | -5.4% |
| 12 | 0.966 | -3.4% |
| 16 | 0.976 | -2.4% |
| 32 | 0.989 | -1.2% |
| 64 | 0.994 | -0.6% |

## Adding new benchmark results

When new `speedtest` results arrive for a CPU already in `bench()`:

1. Note the CPU model string (must match exactly what appears in `live_data_sb_EUR.json`)
2. Note the thread count used (should be `total_threads - 1`)
3. Note the best-build N/s (prefer avx512icl or vnni512 over avx2 where available)
4. Replace the estimated value in the match arm with the measured value; change comment marker to ★
5. If this is the first measurement for an architecture (e.g. first Intel AVX-512 result), reconsider the `_SIMD_AVX512` constant and re-derive values for architecturally similar CPUs

When adding a **new CPU** not yet in the match:
- Add a case before `case _:`
- Use `default_bench` as a starting estimate, then refine with measurement
- Verify the CPU string against the live JSON (`cpu` field)

## CPUs with highest estimation uncertainty

Priority targets for future benchmarking:

1. ~~**Intel Core i9-13900**~~ — **measured**. Was 38% overestimated; no longer top-ranked.
2. **AMD Ryzen 5 3600** — most common CPU in auction (144 servers); would validate Zen2 scaling factor affecting 3700X, Ryzen 9 3900, EPYC 7502 estimates too.
3. **Intel Xeon W-2295** — 50 servers, would provide first Intel native AVX-512 calibration data point.

## speedtest directory

Contains raw `stockfish speedtest` output files organized as:
```
speedtest/<CPU model>/speedtest-<build>.txt
speedtest/<CPU model>/speedtest-<build>-<threads>.txt   # reduced thread count
```

Files with a thread count suffix (e.g. `-15.txt`) are the relevant ones for bench() — they ran with 1 thread reserved.
