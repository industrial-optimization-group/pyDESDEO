# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2016  Vesa Ojalehto
"""
"""
import sys

import numpy as np

try:
    from prompt_toolkit import prompt

    tui = True
except ImportError:
    tui = False

from prompt_toolkit.validation import Validator, ValidationError

from desdeo.preference.PreferenceInformation import (
    RelativeRanking,
    DirectSpecification,
    PercentageSpecifictation,
)

COMMANDS = ["c", "C", "q"]


class IterValidator(Validator):

    def __init__(self, method):
        super().__init__()
        self.range = map(str, range(1, len(method.zhs) + 1)) + ["q"]

    def validate(self, document):
        text = document.text
        if text not in self.range + COMMANDS:
            raise ValidationError(
                message="Ns %s is not valid iteration point" % text, cursor_position=0
            )


class VectorValidator(Validator):

    def __init__(self, method, preference=None):
        super().__init__()
        self.nfun = len(method.problem.nadir)
        self.preference = preference
        self.method = method

    def validate(self, document):
        for c in COMMANDS:
            if c in document.text:
                if c == "q":
                    sys.exit("User exit")
                return
        values = document.text.split(",")
        if len(values) != self.nfun:
            raise ValidationError(
                message="Problem requires %i items in the vector" % self.nfun,
                cursor_position=0,
            )
        if self.preference:
            err = self.preference.check_input(values, self.method.problem)
            if err:
                raise ValidationError(message=err, cursor_position=0)


class NumberValidator(Validator):

    def __init__(self, ranges=None):
        super().__init__()
        if ranges:
            self.ranges = ranges
        else:
            self.ranges = [1, None]

    def validate(self, document):
        text = document.text
        i = 0
        if text and not text.isdigit():
            # Get index of fist non numeric character.
            # We want to move the cursor here.
            for i, c in enumerate(text):
                if not c.isdigit():
                    break

            raise ValidationError(
                message="This input contains non-numeric characters", cursor_position=i
            )
        v = int(text)
        if self.ranges[0] and v < self.ranges[0]:
            raise ValidationError(
                message="The number must be greater than %i" % self.ranges[0],
                cursor_position=0,
            )

        if self.ranges[1] and v > self.ranges[1]:
            raise ValidationError(
                message="The number must be smaller than %i" % self.ranges[1],
                cursor_position=0,
            )


def select_iter(method, default=1, no_print=False):
    if not no_print:
        method.printCurrentIteration()
    if tui:
        text = prompt(u"Select iteration point Ns: ", validator=IterValidator(method))
    else:
        text = str(default)
        # This is not a tui, so go to next
        if method.current_iter == 3:
            text = "c"

    if "q" in text:
        sys.exit("User exit")
    elif text in COMMANDS:
        return text
    print("Selected iteration point: %s" % method.zhs[int(text) - 1])
    print("Reachable points: %s" % method.zh_reach[int(text) - 1])
    return method.zhs[int(text) - 1], method.zh_los[int(text) - 1]


def ask_pref(method, prev_pref):
    rank = prompt(
        u"Ranking: ",
        default=u",".join(map(str, prev_pref)),
        validator=VectorValidator(method),
    )
    if rank == "e":
        return rank
    pref = RelativeRanking(map(float, rank.split(",")))
    method.nextIteration(pref)
    method.printCurrentIteration()


def iter_nautilus(method):
    solution = None
    if tui:
        print("Preference elicitation options:")
        print("\t1 - Percentages")
        print("\t2 - Relative ranks")
        print("\t3 - Direct")

        pref_sel = int(
            prompt(
                u"Reference elicitation ",
                default=u"%s" % (1),
                validator=NumberValidator([1, 3]),
            )
        )
    else:
        pref_sel = 2

    PREFCLASSES = [PercentageSpecifictation, RelativeRanking, DirectSpecification]
    preference_class = PREFCLASSES[pref_sel - 1]

    print("Nadir: %s" % method.problem.nadir)
    print("Ideal: %s" % method.problem.ideal)

    if tui:
        method.user_iters = method.current_iter = int(
            prompt(
                u"Ni: ",
                default=u"%s" % (method.current_iter),
                validator=NumberValidator(),
            )
        )
    else:
        method.current_iter = method.user_iters = 4
    print("Ni:", method.user_iters)
    pref = preference_class(method, None)
    default = u",".join(map(str, pref.default_input()))
    pref = preference_class(method, pref.default_input())

    MCDA_prefs = [
        [2.0, 2.0, 1.0, 1.0],
        [2.0, 2.0, 1.0, 1.0],
        [2.0, 3.0, 1.0, 4.0],
        [1.0, 1.0, 2.0, 2.0],
    ]
    mi = 0
    while method.current_iter:

        method.printCurrentIteration()
        default = u",".join(map(str, pref.pref_input))

        if tui:
            pref_input = prompt(
                u"Preferences: ",
                default=default,
                validator=VectorValidator(method, pref),
            )
        else:
            # This is not a tui, so go to next
            pref_input = ",".join(map(str, MCDA_prefs[mi]))
            # pref_input = default
            # if method.current_iter == 5:
            #    pref_input = "c"
        brk = False
        for c in COMMANDS:
            if c in pref_input:
                brk = True
        if brk:
            solution = method.zh
            break
        pref = preference_class(
            method, np.fromstring(pref_input, dtype=np.float, sep=",")
        )
        solution, _ = method.nextIteration(pref)
        mi += 1
    return solution


def iter_enautilus(method):
    if tui:
        method.user_iters = method.current_iter = int(
            prompt(
                u"Ni: ",
                default=u"%i" % method.current_iter,
                validator=NumberValidator(),
            )
        )
        method.Ns = int(prompt(u"Ns: ", default=u"5", validator=NumberValidator()))
    else:
        method.user_iters = 5
        method.Ns = 5
    print("Nadir: %s" % method.problem.nadir)
    print("Ideal: %s" % method.problem.ideal)

    method.nextIteration()
    points = None

    while method.current_iter:
        # method.printCurrentIteration()
        pref = select_iter(method, 1)
        if pref in COMMANDS:
            break
        if tui:
            method.Ns = int(
                prompt(
                    u"Ns: ", default=u"%s" % (method.Ns), validator=NumberValidator()
                )
            )
        else:
            pass
        points = method.nextIteration(pref)

    if not method.current_iter:
        method.zh_prev = select_iter(method, 1)[0]
        method.current_iter -= 1
    return points
