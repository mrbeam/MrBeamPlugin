#!/usr/bin/env python2

# TODO profile OctoPrint

try:
    import cProfile
    import pstats
except ImportError:
    exit("Please install cProfile and pstats.")

from threading import Timer
import io
import time

BENCH_FILE = "octoprint.pstats"

AXEL_BENCH_TIME = 25
RPI3_BENCH_TIME = 180


def profile(lines=60, sortby="tottime", bench_time=None, out_file=None):
    """Run Octoprint and create a profile of it when it exits.

    Note: You can Ctrl C to shut it down as well.
    The profiler dumps the stats when octoprint exits.
    If bench_time given, the process will terminate itself such that
    OctoPrint does a clean exit
    """
    profiler = cProfile.Profile(builtins=False)
    bench(profiler.enable, dump_stats, exit_args=(profiler, lines, sortby, out_file))


def graph(out_file, img_format="svg", bench_time=None, ignore=()):
    """Run Octoprint and create a profile of it when it exits.

    Note: You can Ctrl C to shut it down as well.
    A call graph image is created when octoprint exits.
    WARNING : This can take a long time
    If bench_time given, the process will terminate itself such that
    OctoPrint does a clean exit
    """
    try:
        import pycallgraph as __pycallgraph
        from pycallgraph.output import GraphvizOutput
        from pycallgraph.globbing_filter import GlobbingFilter
    except ImportError:
        exit("Please install pycallgraph to make a function graph.")
    graphviz = GraphvizOutput(
        output_file=out_file,
        output_type=img_format,
    )
    trace_filter = GlobbingFilter(
        include=[
            "[oO]cto[pP]rint*",
            "mrbeam*",
        ],
        exclude=[
            "*._*",  # private variables, functions
            # "*.[A-Z]*", # class initialisation
            "*time.sleep",
            "*.wait",
            "pycallgraph.*",
            "pkgutil.*",
            "platform.*",
            "distutils.*",
            "logging.*",
            "ssl.*",
            "sysconfig.*",
            "SocketServer.*",
            "Queue.*",
            "cookielib.*",
            "fractions.*",
            "email.*",
            "ctypes,xml.*",
            "re_.compile",
            "functools.*",
        ]
        + list(ignore),
    )
    config = __pycallgraph.Config(verbose=False, trace_filter=trace_filter)
    call_graph = __pycallgraph.PyCallGraph(output=graphviz, config=config)
    bench(call_graph.start, call_graph.done, bench_time=bench_time)


def bench(
    start_func=None,
    exit_func=None,
    start_args=(),
    start_kwargs=None,
    exit_args=(),
    exit_kwargs=None,
    bench_time=None,
):
    """execute starting and stopping scripts around Octoprint execution
    OctoPrint uses `signal` to intercept termination kills, which it means it
    has to be launched in the main Thread.

    The exit_func is run when octoprint exits. If bench_time given, the
    process will terminate itself such that OctoPrint does a clean exit
    """

    import os
    import atexit
    import signal

    # execute exit_func after OctoPrint exits
    atexit.register(exit_func, *exit_args, **(exit_kwargs or {}))
    if bench_time is not None:
        _t = Timer(bench_time, os.kill, args=(os.getpid(), signal.SIGTERM))
        _t.start()

    if start_func is not None:
        start_func(*start_args, **(start_kwargs or {}))
    from octoprint.cli import octo

    octo(
        args=("serve",),
        prog_name="octoprint",
        auto_envvar_prefix="OCTOPRINT",
    )


def dump_stats(
    profiler,
    lines=60,
    sortby="tottime",
    filename=None,
):
    """Save the content of the given profiler."""
    print(" ##### Dumping Profile ##### ")
    profiler.disable()
    if filename:
        profiler.dump_stats(filename)
    if lines:
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats(sortby)
        stats.print_stats(lines)
        print(s.getvalue())


def read_bench(filename, sortby="tottime", lines=60, regex=None):
    """Print some lines from the Profile.

    Poor man's analysis tool - It is recommended to use RunSnakeRun.
    """
    s = io.StringIO()
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
        metavar="OUT.pstat",
        type=str,
        default=BENCH_FILE,
        help="Dump the profile to this file for further analysis.",
    )
    parser.add_argument(
        "--graph",
        "-g",
        metavar="OUT.svg",
        type=str,
        default="",
        help="SVG output file containing a graph of the function calls in octoprint_mrbeam.",
    )
    parser.add_argument(
        "-i",
        metavar='"pack1.*,pack2.*,..."',
        type=str,
        default="",
        help="comma delimited list of packages to ignore",
    )

    args = parser.parse_args()
    if args.path:
        read_bench(args.path, lines=args.lines, sortby=args.sortby)
    else:
        if args.graph:
            graph(args.graph, ignore=args.i.split(","))
        else:
            profile(
                lines=args.lines,
                sortby=args.sortby,
                bench_time=args.bench_time,
                out_file=args.out,
            )
