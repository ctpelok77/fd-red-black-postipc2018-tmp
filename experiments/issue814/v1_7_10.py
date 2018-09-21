#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""This experiment is only here for completeness because it was referred
to on the tracker. Don't use it as given here: the different experiments
that are aggregated here used different timeouts, so the results will be
misleading."""

import os

from lab.environments import LocalEnvironment, BaselSlurmEnvironment

import common_setup
from common_setup import IssueConfig, IssueExperiment
from relativescatter import RelativeScatterPlotReport

DIR = os.path.dirname(os.path.abspath(__file__))
BENCHMARKS_DIR = os.environ["DOWNWARD_BENCHMARKS"]
REVISIONS = ["issue814-base", "issue814-v1", "issue814-v7", "issue814-v10"]
if common_setup.is_test_run():
    BUILDS = ["release32"]
else:
    BUILDS = ["debug64", "release32", "release64"]
CONFIGS = [
    IssueConfig(
        build + "-{heuristic}".format(**locals()),
        ["--evaluator", "h={heuristic}()".format(**locals()), "--search", "lazy_greedy([h],preferred=[h])"],
        build_options=[build],
        driver_options=["--build", build, "--overall-time-limit", "30m"])
    for build in BUILDS
    for heuristic in ["add", "ff"]
]
SUITE = common_setup.DEFAULT_SATISFICING_SUITE
ENVIRONMENT = BaselSlurmEnvironment(
    partition="infai_2",
    email="malte.helmert@unibas.ch",
    export=["PATH", "DOWNWARD_BENCHMARKS"])

if common_setup.is_test_run():
    SUITE = IssueExperiment.DEFAULT_TEST_SUITE
    ENVIRONMENT = LocalEnvironment(processes=1)

exp = IssueExperiment(
    revisions=REVISIONS,
    configs=CONFIGS,
    environment=ENVIRONMENT,
)
exp.add_suite(BENCHMARKS_DIR, SUITE)

exp.add_parser(exp.EXITCODE_PARSER)
exp.add_parser(exp.TRANSLATOR_PARSER)
exp.add_parser(exp.SINGLE_SEARCH_PARSER)
exp.add_parser(exp.PLANNER_PARSER)
exp.add_parser(os.path.join(DIR, "parser.py"))

## The following steps are to actually run the experiment.
# exp.add_step('build', exp.build)
# exp.add_step('start', exp.start_runs)
# exp.add_fetcher(name='fetch')

## Alternatively, the following steps fetch the results from the other experiments.
exp.add_fetcher('data/issue814-v1-eval')
exp.add_fetcher('data/issue814-v7-eval')
exp.add_fetcher('data/issue814-v10-eval')

exp.add_absolute_report_step()
exp.add_comparison_table_step(
    attributes=IssueExperiment.DEFAULT_TABLE_ATTRIBUTES +
    ["simplify_before", "simplify_after", "simplify_time"])

for attribute in ["memory", "total_time"]:
    for config in CONFIGS:
        exp.add_report(
            RelativeScatterPlotReport(
                attributes=[attribute],
                filter_algorithm=["{}-{}".format(rev, config.nick) for rev in REVISIONS],
                get_category=lambda run1, run2: run1.get("domain")),
            outfile="{}-{}-{}-{}-{}.png".format(exp.name, attribute, config.nick, *REVISIONS))

exp.run_steps()
