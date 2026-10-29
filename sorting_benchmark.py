import argparse
import csv
import random
import sys
import time

import matplotlib.pyplot as plt


INSERTION_MAX_N = 10_000


def insertion_sort(arr):
    a = list(arr)
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a


def merge_sort(arr):
    a = list(arr)
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    left = merge_sort(a[:mid])
    right = merge_sort(a[mid:])
    return _merge(left, right)


def _merge(left, right):
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def quick_sort(arr):
    a = list(arr)
    _quick_sort(a, 0, len(a) - 1)
    return a


def _quick_sort(a, lo, hi):
    while lo < hi:
        p = _partition(a, lo, hi)
        if p - lo < hi - p:
            _quick_sort(a, lo, p - 1)
            lo = p + 1
        else:
            _quick_sort(a, p + 1, hi)
            hi = p - 1


def _partition(a, lo, hi):
    r = random.randint(lo, hi)
    a[r], a[hi] = a[hi], a[r]
    pivot = a[hi]
    i = lo
    for j in range(lo, hi):
        if a[j] < pivot:
            a[i], a[j] = a[j], a[i]
            i += 1
    a[i], a[hi] = a[hi], a[i]
    return i


def python_sorted(arr):
    return sorted(arr)


ALGORITHMS = {
    "Insertion sort": insertion_sort,
    "Merge sort": merge_sort,
    "Quick sort": quick_sort,
    "Python sorted()": python_sorted,
}


def make_data(kind, n, rng):
    if kind == "sorted":
        return list(range(n))
    if kind == "reversed":
        return list(range(n, 0, -1))
    if kind == "random":
        return rng.sample(range(n * 10), n)
    raise ValueError(kind)


DATA_KINDS = ["sorted", "reversed", "random"]


def time_once(func, data):
    start = time.perf_counter()
    func(data)
    return time.perf_counter() - start


def best_time(func, data, repeats):
    return min(time_once(func, data) for _ in range(repeats))


def repeats_for(n):
    if n <= 1_000:
        return 5
    if n <= 10_000:
        return 3
    return 1


def verify(sizes, rng):
    n = min(sizes[0], 500)
    for kind in DATA_KINDS:
        data = make_data(kind, n, rng)
        expected = sorted(data)
        for name, func in ALGORITHMS.items():
            if func(data) != expected:
                raise AssertionError(f"{name} failed on {kind} data")
    print("Correctness check passed for all algorithms.\n")


def run_benchmark(sizes, rng):
    results = {k: {name: [] for name in ALGORITHMS} for k in DATA_KINDS}

    for kind in DATA_KINDS:
        print(f"=== {kind.upper()} data ===")
        header = f"{'n':>8} " + " ".join(f"{name:>16}" for name in ALGORITHMS)
        print(header)
        for n in sizes:
            data = make_data(kind, n, rng)
            row = f"{n:>8} "
            for name, func in ALGORITHMS.items():
                if name == "Insertion sort" and n > INSERTION_MAX_N:
                    results[kind][name].append(None)
                    row += f"{'skipped':>16} "
                    continue
                t = best_time(func, data, repeats_for(n))
                results[kind][name].append(t)
                row += f"{t:>15.5f}s "
            print(row, flush=True)
        print()
    return results


def save_csv(sizes, results, path="benchmark_results.csv"):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["data_kind", "algorithm", "n", "seconds"])
        for kind in DATA_KINDS:
            for name in ALGORITHMS:
                for n, t in zip(sizes, results[kind][name]):
                    w.writerow([kind, name, n, "" if t is None else f"{t:.6f}"])
    print(f"Saved {path}")


def plot_results(sizes, results, path="benchmark_plot.png", show=True):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    markers = {"Insertion sort": "o", "Merge sort": "s",
               "Quick sort": "^", "Python sorted()": "d"}

    for ax, kind in zip(axes, DATA_KINDS):
        for name in ALGORITHMS:
            pts = [(n, t) for n, t in zip(sizes, results[kind][name]) if t is not None]
            if not pts:
                continue
            xs, ys = zip(*pts)
            ax.plot(xs, ys, marker=markers[name], label=name)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(f"{kind.capitalize()} input")
        ax.set_xlabel("n (number of elements)")
        ax.grid(True, which="both", alpha=0.3)
    axes[0].set_ylabel("time (seconds)")
    axes[0].legend()
    fig.suptitle("Sorting Benchmark Lab (log-log scale, best of several runs)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f"Saved {path}")
    if show:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Sorting Benchmark Lab")
    parser.add_argument("--quick", action="store_true",
                        help="use small sizes (10^2 .. 10^4) for a fast run")
    parser.add_argument("--no-show", action="store_true",
                        help="do not open the plot window, just save it")
    args = parser.parse_args()

    sys.setrecursionlimit(10_000)
    rng = random.Random(42)

    if args.quick:
        sizes = [100, 300, 1_000, 3_000, 10_000]
    else:
        sizes = [1_000, 3_000, 10_000, 30_000, 100_000]

    verify(sizes, rng)
    results = run_benchmark(sizes, rng)
    save_csv(sizes, results)
    plot_results(sizes, results, show=not args.no_show)


if __name__ == "__main__":
    main()
