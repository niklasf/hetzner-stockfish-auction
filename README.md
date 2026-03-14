# hetzner-stockfish-auction

Find the most efficient auction prices for Stockfish analysis on
[Hetzner Server Auctions](https://www.hetzner.com/sb/).

Optimized for Stockfish 18 nodes/second per € at n-1 threads.

Real measurements, but otherwise heavily vibe coded.

## Usage

```bash
make update  # fetch live auction data
make         # print results
```

Example output (best results last):

```
234756 nps/€ | 76.16 € | AMD Ryzen 7 7700 | 2x RAM 32768 MB DDR5 | 2x SSD M.2 NVMe 1 TB | NIC 1 Gbit - Intel i225-LM | IPv4 | iNIC | NVME | SSD | INIC
248298 nps/€ | 138.04 € | AMD EPYC 7502P | 4x RAM 32768 MB DDR4 ECC reg. | 1x SSD U.2 NVMe 960 GB Datacenter | 1x SSD U.2 NVMe 3,84 TB Datacenter | NIC 1 Gbit - Intel I350 | IPv4 | ECC | iNIC | DC | NVME | SSD | +3.84TB | DC | NVME | SSD | ECC | INIC
```

Does not include the cost of an IPv4 address.

## License

CC0
