#!/usr/bin/env python2

# TODO profile OctoPrint

try:
    import cProfile
    import pstats
except ImportError:
    print("Please install cProfile and pstats.")
    exit(1)

from threading import Timer
import StringIO
import time

BENCH_FILE = "octoprint.profile"

AXEL_BENCH_TIME = 25
RPI3_BENCH_TIME = 180


def bench(lines=60, sortby="tottime", bench_time=None, out_file=None):
    """
    Run Octoprint and create a profile of it when it exits.
    Note: You can Ctrl C to shut it down as well.
    OctoPrint uses `signal` to intercept termination kills,
    which it means it has to be launched in the main Thread.
    The profiler dumps the stats when octoprint exits.
    """

    import os
    import atexit
    from octoprint.cli import octo
    import signal

    profiler = cProfile.Profile()

    # dump_stats when OctoPrint exits
    atexit.register(dump_stats, profiler, lines, sortby, out_file)
    if bench_time is not None:
        _t = Timer(bench_time, os.kill, args=(os.getpid(), signal.SIGTERM))
        _t.start()

    # The profiler is available as a context manager for py3
    # with cProfile.Profile() as profiler:
    #     from octoprint.cli import octo
    #     octo(args=args, prog_name="octoprint", auto_envvar_prefix="OCTOPRINT")
    profiler.enable()
    octo(
        args=("serve",),
        prog_name="octoprint",
        auto_envvar_prefix="OCTOPRINT",
    )
    profiler.disable()


def dump_stats(
    profiler,
    lines=60,
    sortby="tottime",
    filename=None,
):
    """Save the content of the given profiler."""
    print(" ##### Dumping Profile ##### ")
    profiler.disable()
    s = StringIO.StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    if filename:
        stats.dump_stats(filename)
    if lines:
        stats.print_stats(lines)
        print(s.getvalue())


def read_bench(filename, sortby="tottime", lines=60, regex=None):
    """Print some lines from the Profile.
    Poor man's analysis tool - It is recommended to use RunSnakeRun.
    """
    s = StringIO.StringIO()
    stats = pstats.Stats(filename, stream=s).sort_stats(sortby)
    if regex is None:
        stats.print_stats(lines)
    else:
        stats.print_stats(regex, lines)
    print(s.getvalue())


if __name__ == "__main__":
    import argparse
    import os

    if os.environ["USER"] == "pi":
        bench_time = RPI3_BENCH_TIME
    elif os.environ["USER"] == "axel":
        bench_time = AXEL_BENCH_TIME
    # These are not used, but you can set them as defaults for --bench-time.

    parser = argparse.ArgumentParser(
        description="Profile Octoprint or - if given - read a profile from path",
    )
    parser.add_argument("path", nargs="?", default=None)
    parser.add_argument(
        "--lines", "-l", type=int, default=None, help="Number of lines to print"
    )
    parser.add_argument(
        "--sortby",
        "-s",
        type=str,
        default="tottime",
        help="Sort lines : tottime, cumsum, module, ncalls, ... See Stats.sort_stats",
    )
    parser.add_argument(
        "--bench-time", "-t", type=int, default=None, help="Duration of a benchmark"
    )
    parser.add_argument(
        "--out",
        "-o",
        type=str,
        default="octoprint.profile",
        help="Dump the profile to this file for further analysis.",
    )
    args = parser.parse_args()
    if args.path is None:
        bench(
            lines=args.lines,
            sortby=args.sortby,
            bench_time=args.bench_time,
            out_file=args.out,
        )
    else:
        read_bench(args.path, lines=args.lines, sortby=args.sortby)
