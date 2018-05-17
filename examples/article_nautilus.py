# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018  Vesa Ojalehto
"""
Script to generate results in [1]

Here, the DM solved the River pollution problem by Narula
and Weistroffer[1], with four objectives and two variables. The problem
describes a (hypothetical) pollution problem of a river, where a
fishery and a city are polluting water. For more information see
:class:`NarulaWeistroffer.RiverPollution`


References
----------

[1] *to be published*

[2] Narula, S. & Weistroffer,
    H. A flexible method for nonlinear multicriteria decision-making problems Systems,
    Man and Cybernetics, IEEE Transactions on, 1989 , 19 , 883-887.

"""

import argparse
import os

from prompt_toolkit import prompt

from desdeo.core.ResultFactory import IterationPointFactory
from desdeo.method.NAUTILUS import ENAUTILUS, NAUTILUSv1
from desdeo.optimization.OptimizationMethod import PointSearch, SciPyDE
from desdeo.optimization.OptimizationProblem import AchievementProblem
from desdeo.problem.Problem import PreGeneratedProblem
from desdeo.utils import misc, tui
from desdeo.utils.misc import Tee
from NarulaWeistroffer import RiverPollution

#: Predefined weights for E-NAUTILUS
# TODO: Give weights in an input file
WEIGHTS = {
    "20": [
        [0.1, 0.1, 0.1, 0.7],
        [0.1, 0.1, 0.366667, 0.433333],
        [0.1, 0.1, 0.633333, 0.166667],
        [0.1, 0.1, 0.7, 0.1],
        [0.1, 0.366667, 0.1, 0.433333],
        [0.1, 0.366667, 0.366667, 0.166667],
        [0.1, 0.366667, 0.433333, 0.1],
        [0.1, 0.633333, 0.1, 0.166667],
        [0.1, 0.633333, 0.166667, 0.1],
        [0.1, 0.7, 0.1, 0.1],
        [0.366667, 0.1, 0.1, 0.433333],
        [0.366667, 0.1, 0.366667, 0.166667],
        [0.366667, 0.1, 0.433333, 0.1],
        [0.366667, 0.366667, 0.1, 0.166667],
        [0.366667, 0.366667, 0.166667, 0.1],
        [0.366667, 0.433333, 0.1, 0.1],
        [0.633333, 0.1, 0.1, 0.166667],
        [0.633333, 0.1, 0.166667, 0.1],
        [0.633333, 0.166667, 0.1, 0.1],
        [0.7, 0.1, 0.1, 0.1],
    ],
    "10": [
        [0.1, 0.1, 0.1, 0.7],
        [0.1, 0.1, 0.5, 0.3],
        [0.1, 0.1, 0.7, 0.1],
        [0.1, 0.5, 0.1, 0.3],
        [0.1, 0.5, 0.3, 0.1],
        [0.1, 0.7, 0.1, 0.1],
        [0.5, 0.1, 0.1, 0.3],
        [0.5, 0.1, 0.3, 0.1],
        [0.5, 0.3, 0.1, 0.1],
        [0.7, 0.1, 0.1, 0.1],
    ],
}


def main(logfile=False):
    """ Solve River Pollution problem with NAUTILUS V1 and E-NAUTILUS Methods
    """
    # Duplicate output to log file
    if logfile:
        Tee(logfile)

    # SciPy breaks box constraints
    nautilus_v1 = NAUTILUSv1(RiverPollution(), SciPyDE)
    nadir = nautilus_v1.problem.nadir
    ideal = nautilus_v1.problem.ideal

    preferences = (2,
                   [[10, 30, 10, 10],
                    "c"]
                   )

    solution = tui.iter_nautilus(nautilus_v1, preferences)

    current_iter = nautilus_v1.current_iter

    # TODO: Move to tui module

    if current_iter > 0:
        weights = prompt(
            u"Weights (10 or 20): ",
            default=u"20",
            validator=tui.NumberValidator())

        factory = IterationPointFactory(
            SciPyDE(AchievementProblem(RiverPollution())))
        points = misc.new_points(factory, solution, WEIGHTS[weights])

        method_e = ENAUTILUS(PreGeneratedProblem(points=points), PointSearch)
        method_e.current_iter = current_iter
        method_e.zh_prev = solution
        print("E-NAUTILUS\nselected iteration point: %s:" % ",".join(
            map(str, method_e.zh_prev)))

    while method_e.current_iter > 0:
        if solution is None:
            solution = method_e.problem.nadir
            # Generate new points
        # print solution

        method_e.problem.nadir = nadir
        method_e.problem.ideal = ideal
        tui.iter_enautilus(method_e)
        solution = method_e.zh_prev
    method_e.print_current_iteration()
    _ = prompt(u"Press ENTER to exit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    logfile = f"{os.path.splitext(os.path.basename(__file__))[0]}.log"
    parser.add_argument('--logfile', '-l',
                        action='store',
                        nargs='?',
                        const=logfile,
                        default=False,
                        help=f"Store intarctions to {logfile} or user specified LOGFILE")

    main(**(vars(parser.parse_args())))
