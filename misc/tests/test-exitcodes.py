#! /usr/bin/env python

from __future__ import print_function

from collections import defaultdict
import itertools
import os
import subprocess
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
REPO_BASE = os.path.dirname(os.path.dirname(DIR))

sys.path.insert(0, REPO_BASE)
from driver import returncodes

BENCHMARKS_DIR = os.path.join(REPO_BASE, "misc", "tests", "benchmarks")
DRIVER = os.path.join(REPO_BASE, "fast-downward.py")

TRANSLATE_TASKS = {
    "small": "gripper/prob01.pddl",
    "large": "satellite/p25-HC-pfile5.pddl",
}

"""A constant function that can be used as a factory for defaultdict."""
def constant_factory(value):
    return itertools.repeat(value).next

TRANSLATE_TESTS = [
    ("small", [], [], defaultdict(constant_factory(returncodes.SUCCESS))),
    ("large", ["--translate-time-limit", "1s"], [], defaultdict(constant_factory(returncodes.TRANSLATE_OUT_OF_TIME))),
    # Since we cannot enforce memory limits on macOS, we make sure that we get
    # the DRIVER_UNSUPPORTED exit code in that case.
    ("large", ["--translate-memory-limit", "50M"], [], defaultdict(constant_factory(returncodes.TRANSLATE_OUT_OF_MEMORY), darwin=returncodes.DRIVER_UNSUPPORTED)),
]

SEARCH_TASKS = {
    "strips": "miconic/s1-0.pddl",
    "axioms": "philosophers/p01-phil2.pddl",
    "cond-eff": "miconic-simpleadl/s1-0.pddl",
    "large": "satellite/p25-HC-pfile5.pddl",
}

MERGE_AND_SHRINK = ('astar(merge_and_shrink('
    'merge_strategy=merge_stateless(merge_selector='
        'score_based_filtering(scoring_functions=[goal_relevance,'
        'dfp,total_order(atomic_ts_order=reverse_level,'
        'product_ts_order=new_to_old,atomic_before_product=false)])),'
    'shrink_strategy=shrink_bisimulation(greedy=false),'
    'label_reduction=exact('
        'before_shrinking=true,'
        'before_merging=false),'
    'max_states=50000,threshold_before_merge=1'
'))')

SEARCH_TESTS = [
    ("strips", [], "astar(add())", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("strips", [], "astar(hm())", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("strips", [], "ehc(hm())", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("strips", [], "astar(ipdb())", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("strips", [], "astar(lmcut())", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("strips", [], "astar(lmcount(lm_rhw(), admissible=false))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("strips", [], "astar(lmcount(lm_rhw(), admissible=true))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("strips", [], "astar(lmcount(lm_hm(), admissible=false))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("strips", [], "astar(lmcount(lm_hm(), admissible=true))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("strips", [], MERGE_AND_SHRINK, defaultdict(constant_factory(returncodes.SUCCESS))),
    ("axioms", [], "astar(add())", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("axioms", [], "astar(hm())", defaultdict(constant_factory(returncodes.SEARCH_UNSOLVED_INCOMPLETE))),
    ("axioms", [], "ehc(hm())", defaultdict(constant_factory(returncodes.SEARCH_UNSOLVED_INCOMPLETE))),
    ("axioms", [], "astar(ipdb())", defaultdict(constant_factory(returncodes.SEARCH_UNSUPPORTED))),
    ("axioms", [], "astar(lmcut())", defaultdict(constant_factory(returncodes.SEARCH_UNSUPPORTED))),
    ("axioms", [], "astar(lmcount(lm_rhw(), admissible=false))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("axioms", [], "astar(lmcount(lm_rhw(), admissible=true))", defaultdict(constant_factory(returncodes.SEARCH_UNSUPPORTED))),
    ("axioms", [], "astar(lmcount(lm_zg(), admissible=false))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("axioms", [], "astar(lmcount(lm_zg(), admissible=true))", defaultdict(constant_factory(returncodes.SEARCH_UNSUPPORTED))),
    # h^m landmark factory explicitly forbids axioms.
    ("axioms", [], "astar(lmcount(lm_hm(), admissible=false))", defaultdict(constant_factory(returncodes.SEARCH_UNSUPPORTED))),
    ("axioms", [], "astar(lmcount(lm_hm(), admissible=true))", defaultdict(constant_factory(returncodes.SEARCH_UNSUPPORTED))),
    ("axioms", [], "astar(lmcount(lm_exhaust(), admissible=false))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("axioms", [], "astar(lmcount(lm_exhaust(), admissible=true))", defaultdict(constant_factory(returncodes.SEARCH_UNSUPPORTED))),
    ("axioms", [], MERGE_AND_SHRINK, defaultdict(constant_factory(returncodes.SEARCH_UNSUPPORTED))),
    ("cond-eff", [], "astar(add())", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("cond-eff", [], "astar(hm())", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("cond-eff", [], "astar(ipdb())", defaultdict(constant_factory(returncodes.SEARCH_UNSUPPORTED))),
    ("cond-eff", [], "astar(lmcut())", defaultdict(constant_factory(returncodes.SEARCH_UNSUPPORTED))),
    ("cond-eff", [], "astar(lmcount(lm_rhw(), admissible=false))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("cond-eff", [], "astar(lmcount(lm_rhw(), admissible=true))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("cond-eff", [], "astar(lmcount(lm_zg(), admissible=false))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("cond-eff", [], "astar(lmcount(lm_zg(), admissible=true))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("cond-eff", [], "astar(lmcount(lm_hm(), admissible=false))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("cond-eff", [], "astar(lmcount(lm_hm(), admissible=true))", defaultdict(constant_factory(returncodes.SEARCH_UNSUPPORTED))),
    ("cond-eff", [], "astar(lmcount(lm_exhaust(), admissible=false))", defaultdict(constant_factory(returncodes.SUCCESS))),
    ("cond-eff", [], "astar(lmcount(lm_exhaust(), admissible=true))", defaultdict(constant_factory(returncodes.SEARCH_UNSUPPORTED))),
    ("cond-eff", [], MERGE_AND_SHRINK, defaultdict(constant_factory(returncodes.SUCCESS))),
    # Since we cannot enforce memory limits on macOS, we make sure that we get the DRIVER_UNSUPPORTED exit code in that case.
    ("large", ["--search-memory-limit", "50M"], MERGE_AND_SHRINK, defaultdict(constant_factory(returncodes.SEARCH_OUT_OF_MEMORY), darwin=returncodes.DRIVER_UNSUPPORTED)),
    ("large", ["--search-time-limit", "1s"], MERGE_AND_SHRINK, defaultdict(constant_factory(returncodes.SEARCH_OUT_OF_TIME))),
]


def cleanup():
    subprocess.check_call([sys.executable, DRIVER, "--cleanup"])


def run_translator_tests():
    for task_type, driver_options, translate_options, expected in TRANSLATE_TESTS:
        relpath = TRANSLATE_TASKS[task_type]
        problem = os.path.join(BENCHMARKS_DIR, relpath)
        print("\nRun translator on {task_type} task:".format(**locals()))
        sys.stdout.flush()
        cmd = [sys.executable, DRIVER] + driver_options + ["--translate"] + translate_options + [problem]
        exitcode = subprocess.call(cmd)
        if exitcode != expected[sys.platform]:
            yield (cmd, expected[sys.platform], exitcode)
        cleanup()


def run_search_tests():
    for task_type, driver_options, search_options, expected in SEARCH_TESTS:
        relpath = SEARCH_TASKS[task_type]
        problem = os.path.join(BENCHMARKS_DIR, relpath)
        print("\nRun {search_options} on {task_type} task:".format(**locals()))
        sys.stdout.flush()
        cmd = [sys.executable, DRIVER] + driver_options + [problem, "--search", search_options]
        exitcode = subprocess.call(cmd)
        if not exitcode == expected[sys.platform]:
            yield (cmd, expected, exitcode)
        cleanup()


def main():
    # On Windows, ./build.py has to be called from the correct environment.
    # Since we want this script to work even when we are in a regular
    # shell, we do not build on Windows. If the planner is not yet built,
    # the driver script will complain about this.
    if os.name == "posix":
        subprocess.check_call(["./build.py"], cwd=REPO_BASE)

    failures = []
    failures += run_translator_tests()
    failures += run_search_tests()
    if failures:
        print("\nFailures:")
        for cmd, expected, exitcode in failures:
            print("{cmd} failed: expected {expected}, got {exitcode}".format(**locals()))
        sys.exit(1)

    print("\nNo errors detected.")


main()
