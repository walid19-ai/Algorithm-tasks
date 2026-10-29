import argparse
import heapq
import random
from dataclasses import dataclass


@dataclass
class Task:
    name: str
    priority: int
    burst: int = 1
    arrival: int = 0
    remaining: int = 0
    start: int = -1
    finish: int = -1

    def __post_init__(self):
        self.remaining = self.burst

    def __str__(self):
        return f"{self.name}(p={self.priority})"


class MaxHeap:
    def __init__(self):
        self._a = []
        self._seq = 0


    @staticmethod
    def _parent(i):
        return (i - 1) // 2

    @staticmethod
    def _left(i):
        return 2 * i + 1

    @staticmethod
    def _right(i):
        return 2 * i + 2

    def _key(self, i):
        return self._a[i][0], self._a[i][1]

    def _swap(self, i, j):
        self._a[i], self._a[j] = self._a[j], self._a[i]

    def _sift_up(self, i):
        while i > 0 and self._key(i) > self._key(self._parent(i)):
            self._swap(i, self._parent(i))
            i = self._parent(i)

    def _sift_down(self, i):
        n = len(self._a)
        while True:
            largest = i
            l, r = self._left(i), self._right(i)
            if l < n and self._key(l) > self._key(largest):
                largest = l
            if r < n and self._key(r) > self._key(largest):
                largest = r
            if largest == i:
                return
            self._swap(i, largest)
            i = largest


    def insert(self, task):
        self._seq += 1
        self._a.append((task.priority, -self._seq, task))
        self._sift_up(len(self._a) - 1)

    def extract_max(self):
        if not self._a:
            raise IndexError("extract_max from an empty heap")
        top = self._a[0][2]
        last = self._a.pop()
        if self._a:
            self._a[0] = last
            self._sift_down(0)
        return top

    def peek(self):
        if not self._a:
            raise IndexError("peek at an empty heap")
        return self._a[0][2]

    def is_empty(self):
        return not self._a

    def __len__(self):
        return len(self._a)

    def snapshot(self):
        return [str(item[2]) for item in self._a]


def simulate(tasks, verbose=True):
    pending = sorted(tasks, key=lambda t: t.arrival)
    heap = MaxHeap()
    finished = []
    time = 0
    i = 0
    timeline = []

    while i < len(pending) or not heap.is_empty():

        while i < len(pending) and pending[i].arrival <= time:
            heap.insert(pending[i])
            if verbose:
                print(f"t={time:>2}  INSERT       {pending[i]}  burst={pending[i].burst}")
            i += 1

        if heap.is_empty():
            time = pending[i].arrival
            continue

        task = heap.extract_max()
        if task.start < 0:
            task.start = time
        task.remaining -= 1
        timeline.append(task.name)
        if verbose:
            print(f"t={time:>2}  EXTRACT-MAX  {task}  runs 1 unit "
                  f"(remaining={task.remaining})")
        time += 1

        if task.remaining > 0:
            heap.insert(task)
        else:
            task.finish = time
            finished.append(task)
            if verbose:
                print(f"t={time:>2}  DONE         {task.name}")

    return finished, timeline


def print_report(finished, timeline):
    print("\nGantt chart (one letter group per time unit):")
    print(" ".join(timeline))
    print(f"\n{'Task':<8}{'Prio':>5}{'Arrive':>8}{'Burst':>7}"
          f"{'Finish':>8}{'Turnaround':>12}{'Waiting':>9}")
    total_wait = 0
    for t in sorted(finished, key=lambda x: x.finish):
        turnaround = t.finish - t.arrival
        waiting = turnaround - t.burst
        total_wait += waiting
        print(f"{t.name:<8}{t.priority:>5}{t.arrival:>8}{t.burst:>7}"
              f"{t.finish:>8}{turnaround:>12}{waiting:>9}")
    print(f"\nAverage waiting time: {total_wait / len(finished):.2f}")


def demo():
    tasks = [
        Task("Backup", priority=2, burst=4, arrival=0),
        Task("Browser", priority=5, burst=3, arrival=1),
        Task("Antivirus", priority=3, burst=2, arrival=2),
        Task("Kernel", priority=9, burst=2, arrival=3),
        Task("Music", priority=5, burst=2, arrival=4),
    ]
    finished, timeline = simulate(tasks)
    print_report(finished, timeline)


HELP = """Commands:
  insert <name> <priority>   add a task
  extract                    remove and show the highest-priority task
  peek                       show the highest-priority task
  show                       print the heap array
  size                       number of tasks waiting
  quit
"""


def interactive():
    heap = MaxHeap()
    print(HELP)
    while True:
        try:
            line = input("scheduler> ").strip().split()
        except EOFError:
            break
        if not line:
            continue
        cmd, args = line[0].lower(), line[1:]
        try:
            if cmd == "insert" and len(args) == 2:
                heap.insert(Task(args[0], int(args[1])))
                print(f"inserted {args[0]} (priority {args[1]})")
            elif cmd == "extract":
                print("running:", heap.extract_max())
            elif cmd == "peek":
                print("next:", heap.peek())
            elif cmd == "show":
                print(heap.snapshot())
            elif cmd == "size":
                print(len(heap))
            elif cmd in ("quit", "exit"):
                break
            else:
                print(HELP)
        except ValueError:
            print("priority must be an integer")
        except IndexError as e:
            print("error:", e)


def self_test():
    rng = random.Random(1)
    for _ in range(200):
        mine = MaxHeap()
        ref = []
        n = rng.randint(0, 60)
        for k in range(n):
            p = rng.randint(0, 20)
            mine.insert(Task(f"t{k}", p))
            heapq.heappush(ref, (-p, k))
        while ref:
            exp_p, exp_k = heapq.heappop(ref)
            got = mine.extract_max()
            assert (got.priority, got.name) == (-exp_p, f"t{exp_k}"), (got, exp_p, exp_k)
        assert mine.is_empty()


    try:
        MaxHeap().extract_max()
        raise AssertionError("expected IndexError")
    except IndexError:
        pass
    print("All self-tests passed.")


def main():
    parser = argparse.ArgumentParser(description="Task Scheduler (max-heap)")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        self_test()
    elif args.interactive:
        interactive()
    else:
        demo()


if __name__ == "__main__":
    main()
