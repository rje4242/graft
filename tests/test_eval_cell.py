import itertools

from typing import Iterable, List, Optional, Tuple, Union

from graftlib.dot import Dot
from graftlib.env import Env
from graftlib.graftrun import graftrun, graftrun_debug
from graftlib.eval_cell import eval_cell
from graftlib.lex_cell import lex_cell
from graftlib.line import Line
from graftlib.make_graft_env import make_graft_env
from graftlib.numbervalue import NumberValue
from graftlib.pt import Pt
from graftlib.parse_cell import parse_cell
from graftlib.round_ import round_float, round_stroke


def round_strokes(strokes: Iterable[List[Union[Dot, Line]]]) -> (
        Iterable[List[Union[Dot, Line]]]):
    for par_strokes in strokes:
        yield [round_stroke(stroke) for stroke in par_strokes]


def round_value(v):
    if type(v) == float:
        return round_float(v)
    elif type(v) == int:
        return float(v)
    elif type(v) == NumberValue:
        return NumberValue(round_value(v.value))
    elif type(v) == Pt:
        return round_pt(v)
    elif type(v) in (Line, Dot):
        return round_stroke(v)
    else:
        return v


def rounded_dict(env):
    """
    Return a map of name->value of names visible in
    env and its parents, excluding any values that
    are equal to the default environment.
    Float values are rounded.
    """

    default_env = make_graft_env()
    ret = {}

    def add_items(env):
        if env.parent() is not None:
            add_items(env.parent())
        for k, v in env.local_items().items():
            v = round_value(v)
            if (
                k in default_env.local_items() and
                round_value(default_env.local_items()[k]) == v
            ):
                if k in ret:
                    del ret[k]
            else:
                ret[k] = v

    add_items(env)
    return ret


def round_debug(strokes: Iterable[List[Tuple[Optional[Line], Env]]]) -> (
        Iterable[List[Tuple[Optional[Union[Dot, Line]], Env]]]):
    for par_strokes in strokes:
        yield [
            (
                None if stroke is None else round_stroke(stroke),
                rounded_dict(env)
            ) for (stroke, env) in par_strokes
        ]


def do_eval(chars: Iterable[str], n: int, rand=None, max_forks=10):
    return list(
        round_strokes(
            graftrun(
                parse_cell(lex_cell(chars)),
                n,
                rand,
                max_forks,
                eval_cell,
            )
        )
    )


def do_eval_debug(chars: Iterable[str], n: int, rand=None, max_forks=10):
    return list(
        itertools.islice(
            round_debug(
                graftrun_debug(
                    parse_cell(lex_cell(chars)),
                    n,
                    rand,
                    max_forks,
                    eval_cell,
                )
            ),
            0,
            n
        )
    )


def test_calling_s_moves_forward():
    assert (
        do_eval("S() S()", 2) ==
        [
            [Line(Pt(0.0, 0.0), Pt(0.0, 10.0))],
            [Line(Pt(0.0, 10.0), Pt(0.0, 20.0))],
        ]
    )


def test_setting_a_variable():
    assert (
        do_eval_debug("d=3", 1) ==
        [[(None, {"d": NumberValue(3)})]]
    )


def test_changing_a_variable():
    assert (
        do_eval_debug("d=3 d=d+4", 2) ==
        [
            [(None, {"d": NumberValue(3.0)})],
            [(None, {"d": NumberValue(7.0)})],
        ]
    )


def test_incrementing_a_variable_adds_ten():
    assert do_eval("d+=10", 100) == []  # Does terminate even though no strokes

    assert (
        do_eval_debug("d+=10", 1) ==
        [[(None, {"d": NumberValue(10.0)})]]
    )


def test_subtracting_from_a_variable():
    assert do_eval("d-=10", 1) == []

    assert (
        do_eval_debug("d-=10", 1) ==
        [[(None, {"d": NumberValue(-10.0)})]]
    )


def TODO_FAILS_test_subtracting_a_negative():
    assert (
        do_eval_debug("d-=-2", 1) ==
        [[(None, {"d": NumberValue(2.0)})]]
    )


def test_dividing():
    assert (
        do_eval_debug("s/=2", 1) ==
        [[(None, {"s": NumberValue(5.0)})]]
    )


def TODO_FAILS_test_adding_a_negative_subtracts():
    assert (
        do_eval_debug("d+=-2", 1) ==
        [[(None, {"d": NumberValue(-2.0)})]]
    )


def test_multiplying_a_variable():
    assert (
        do_eval_debug("d=2 d*=3.1", 2) ==
        [
            [(None, {"d": NumberValue(2.0)})],
            [(None, {"d": NumberValue(6.2)})],
        ]
    )


def test_turn_right_and_move():
    assert do_eval("d+=90 s=25 S()", 1) == [[Line(Pt(0, 0), Pt(25, 0))]]


def test_turn_right_and_jump():
    assert (
        do_eval_debug("d+=90 s=25 J() S()", 4) ==
        [
            [(
                None,
                {"d": NumberValue(90.0)},
            )],
            [(
                None,
                {"d": NumberValue(90.0), "s": NumberValue(25.0)},
            )],
            [(
                None,
                {
                    "x": NumberValue(25.0),
                    "d": NumberValue(90.0),
                    "s": NumberValue(25.0),
                    "xprev": NumberValue(0.0),
                    "yprev": NumberValue(0.0)
                },
            )],
            [(
                Line(Pt(25.0, 0.0), Pt(50.0, 0.0)),
                {
                    "x": NumberValue(50.0),
                    "d": NumberValue(90.0),
                    "s": NumberValue(25.0),
                    "xprev": NumberValue(25.0),
                    "yprev": NumberValue(0.0),
                },
            )],
        ]
    )


def test_turn_random_and_move():
    def r(_a, _b):
        return 9

    assert (
        do_eval("d+=R()*10 S()", n=1, rand=r) ==
        [[Line(Pt(0, 0), Pt(10, 0))]]
    )


def test_bare_number_does_nothing():
    assert do_eval("3", n=1) == []


def test_bare_random_does_nothing():
    def r(_a, _b):
        return 90
    assert do_eval("R()", n=1, rand=r) == []


def test_draw_in_different_colour():
    assert (
        do_eval("r=0.9 g=0.5 b=0.1 a=0.5 S() a=0.1 S()", 2) ==
        [
            [Line(Pt(0.0, 0.0), Pt(0, 10.0), color=(0.9, 0.5, 0.1, 0.5))],
            [Line(Pt(0.0, 10.0), Pt(0, 20.0), color=(0.9, 0.5, 0.1, 0.1))],
        ]
    )


def test_draw_in_different_size():
    assert (
        do_eval("z=20 S() r=5 S()", 2) ==
        [
            [Line(Pt(0.0, 0.0), Pt(0, 10.0), size=20.0)],
            [Line(
                Pt(0.0, 10.0),
                Pt(0.0, 20.0),
                size=20.0,
                color=(5.0, 0.0, 0.0, 100.0),
            )],
        ]
    )


def test_repeating_commands():
    assert (
        do_eval("T(3,S)", 3) ==
        [
            [Line(Pt(0.0, 0.0), Pt(0.0, 10.0))],
            [Line(Pt(0.0, 10.0), Pt(0.0, 20.0))],
            [Line(Pt(0.0, 20.0), Pt(0.0, 30.0))],
        ]
    )


def test_repeating_multiple_commands():
    assert (
        do_eval("T(3,{d+=90 S()})", 3) ==
        [
            [Line(Pt(0.0, 0.0), Pt(10.0, 0.0))],
            [Line(Pt(10.0, 0.0), Pt(10.0, -10.0))],
            [Line(Pt(10.0, -10.0), Pt(0.0, -10.0))],
        ]
    )


# def TODO_FAILS_REQUIRES_MONADIC_STROKES():
# #test_repeating_multiple_commands_where_strokes_are_not_last():
#     assert (
#         do_eval("T(3,{S() d+=90})", 3) ==
#         [
#             [Line(Pt(0.0, 0.0), Pt(0.0, 10.0))],
#             [Line(Pt(0.0, 10.0), Pt(10.0, 10.0))],
#             [Line(Pt(10.0, 10.0), Pt(10.0, 0.0))],
#         ]
#     )


def test_space_to_separate_statements():
    assert do_eval("s s S()", 1) == [[Line(Pt(0.0, 0.0), Pt(0.0, 10.0))]]


def test_pass_symbol_to_operator():
    assert do_eval("s=90 d+=s S()", 1) == [[Line(Pt(0.0, 0.0), Pt(90.0, 0.0))]]


def test_define_custom_variable():
    assert (
        do_eval("aa=180 d+=aa S()", 1) ==
        [[Line(Pt(0.0, 0.0), Pt(0.0, -10.0))]]
    )


def test_multiply_by_variable():
    assert (
        do_eval("aa=2 s*=aa S()", 1) ==
        [[Line(Pt(0.0, 0.0), Pt(0.0, 20.0))]]
    )


def test_move_in_a_circle():
    assert (
        do_eval("S() d+=10", 36) ==
        [
            [Line(Pt(0.0, 0.0), Pt(0.0, 10.0))],
            [Line(start=Pt(x=0.0, y=10.0), end=Pt(x=1.7, y=19.8))],
            [Line(start=Pt(x=1.7, y=19.8), end=Pt(x=5.2, y=29.2))],
            [Line(start=Pt(x=5.2, y=29.2), end=Pt(x=10.2, y=37.9))],
            [Line(start=Pt(x=10.2, y=37.9), end=Pt(x=16.6, y=45.6))],
            [Line(start=Pt(x=16.6, y=45.6), end=Pt(x=24.2, y=52.0))],
            [Line(start=Pt(x=24.2, y=52.0), end=Pt(x=32.9, y=57.0))],
            [Line(start=Pt(x=32.9, y=57.0), end=Pt(x=42.3, y=60.4))],
            [Line(start=Pt(x=42.3, y=60.4), end=Pt(x=52.2, y=62.2))],
            [Line(start=Pt(x=52.2, y=62.2), end=Pt(x=62.2, y=62.2))],
            [Line(start=Pt(x=62.2, y=62.2), end=Pt(x=72.0, y=60.4))],
            [Line(start=Pt(x=72.0, y=60.4), end=Pt(x=81.4, y=57.0))],
            [Line(start=Pt(x=81.4, y=57.0), end=Pt(x=90.1, y=52.0))],
            [Line(start=Pt(x=90.1, y=52.0), end=Pt(x=97.7, y=45.6))],
            [Line(start=Pt(x=97.7, y=45.6), end=Pt(x=104.1, y=37.9))],
            [Line(start=Pt(x=104.1, y=37.9), end=Pt(x=109.1, y=29.2))],
            [Line(start=Pt(x=109.1, y=29.2), end=Pt(x=112.6, y=19.8))],
            [Line(start=Pt(x=112.6, y=19.8), end=Pt(x=114.3, y=10.0))],
            [Line(start=Pt(x=114.3, y=10.0), end=Pt(x=114.3, y=0.0))],
            [Line(start=Pt(x=114.3, y=0.0), end=Pt(x=112.6, y=-9.8))],
            [Line(start=Pt(x=112.6, y=-9.8), end=Pt(x=109.1, y=-19.2))],
            [Line(start=Pt(x=109.1, y=-19.2), end=Pt(x=104.1, y=-27.9))],
            [Line(start=Pt(x=104.1, y=-27.9), end=Pt(x=97.7, y=-35.6))],
            [Line(start=Pt(x=97.7, y=-35.6), end=Pt(x=90.1, y=-42.0))],
            [Line(start=Pt(x=90.1, y=-42.0), end=Pt(x=81.4, y=-47.0))],
            [Line(start=Pt(x=81.4, y=-47.0), end=Pt(x=72.0, y=-50.4))],
            [Line(start=Pt(x=72.0, y=-50.4), end=Pt(x=62.2, y=-52.2))],
            [Line(start=Pt(x=62.2, y=-52.2), end=Pt(x=52.2, y=-52.2))],
            [Line(start=Pt(x=52.2, y=-52.2), end=Pt(x=42.3, y=-50.4))],
            [Line(start=Pt(x=42.3, y=-50.4), end=Pt(x=32.9, y=-47.0))],
            [Line(start=Pt(x=32.9, y=-47.0), end=Pt(x=24.2, y=-42.0))],
            [Line(start=Pt(x=24.2, y=-42.0), end=Pt(x=16.6, y=-35.6))],
            [Line(start=Pt(x=16.6, y=-35.6), end=Pt(x=10.2, y=-27.9))],
            [Line(start=Pt(x=10.2, y=-27.9), end=Pt(x=5.2, y=-19.2))],
            [Line(start=Pt(x=5.2, y=-19.2), end=Pt(x=1.7, y=-9.8))],
            [Line(start=Pt(x=1.7, y=-9.8), end=Pt(x=-0.0, y=-0.0))],
        ]
    )


def test_draw_a_dot():
    assert do_eval("D()", 1) == [[Dot(Pt(0.0, 0.0))]]
    assert do_eval("x=20 y=15 D()", 1) == [[Dot(Pt(20.0, 15.0))]]


def test_go_then_line():
    assert (
        do_eval("x=10 y=15 x=20 y=16 L()", 1) ==
        [[Line(Pt(10.0, 15.0), Pt(20.0, 16.0))]]
    )


def test_go_then_line_negatives():
    assert (
        do_eval("x=-10 y=-15 x+=-10 y+=-1 L()", 1) ==
        [[Line(Pt(-10.0, -15.0), Pt(-20.0, -16.0))]]
    )


def test_go_then_line_modified():
    assert (
        do_eval("x=10 y=15 x+=10 y+=1 L()", 1) ==
        [[Line(Pt(10.0, 15.0), Pt(20.0, 16.0))]]
    )


def test_repeat_starts_at_beginning_if_no_label():
    assert (
        do_eval("d=90 d+=90 S()", 2) ==
        [
            [Line(Pt(0.0, 0.0), Pt(0.0, -10.0))],
            [Line(Pt(0.0, -10.0), Pt(0.0, -20.0))],
        ]
    )


def test_repeat_starts_at_label_if_present():
    assert (
        do_eval("d=90 ^ d+=90 S()", 2) ==
        [
            [Line(Pt(0.0, 0.0), Pt(0.0, -10.0))],
            [Line(Pt(0.0, -10.0), Pt(-10.0, -10.0))],
        ]
    )


def test_fork_draws_lines_in_parallel():
    assert (
        do_eval("F() S()", 1) ==
        [
            [
                Line(Pt(0.0, 0.0), Pt(0.0, 10.0)),
                Line(Pt(0.0, 0.0), Pt(0.0, 10.0)),
            ],
        ]
    )


def fork_ids(debug_time_step):
    return list(
        env_vars["f"].value if "f" in env_vars else 0
        for _, env_vars in debug_time_step
    )


def test_fork_increments_the_fork_id():
    result = do_eval_debug("F() d+=10 F() d+=10", 4)
    assert fork_ids(result[0]) == [0]
    assert fork_ids(result[1]) == [0, 1]
    assert fork_ids(result[2]) == [0, 1]
    assert fork_ids(result[3]) == [0, 1, 2, 3]
    assert len(result) == 4


def test_forking_at_fork_limit_increases_fork_id():
    result = do_eval_debug("F() d+=10 F() d+=10", n=4, rand=None, max_forks=2)
    assert fork_ids(result[0]) == [0]
    assert fork_ids(result[1]) == [0, 1]
    assert fork_ids(result[2]) == [0, 1]
    assert fork_ids(result[3]) == [2, 3]  # More forks, but old ones are gone
    assert len(result) == 4


def test_fork_repeated_creates_multiple_forks():
    result = do_eval_debug("T(5, F) d+=10", n=2)
    assert fork_ids(result[0]) == [0]
    assert fork_ids(result[1]) == [0, 1, 2, 3, 4, 5]
    assert len(result) == 2


def test_fork_repeated_past_fork_limit_gets_max_fork_id():
    result = do_eval_debug("T(5, F) d+=10", n=2, rand=None, max_forks=1)
    assert fork_ids(result[0]) == [0]
    assert fork_ids(result[1]) == [5]
    assert len(result) == 2


def test_does_not_lock_if_no_lines_emitted():
    do_eval("d+=10", n=100)


def test_past_fork_limit_lines_still_move_you():
    assert (
        do_eval("F() S()", n=4, rand=None, max_forks=1) ==
        [
            [Line(Pt(0.0, 0.0), Pt(0.0, 10.0))],
            [Line(Pt(0.0, 10.0), Pt(0.0, 20.0))],
            [Line(Pt(0.0, 20.0), Pt(0.0, 30.0))],
            [Line(Pt(0.0, 30.0), Pt(0.0, 40.0))],
        ]
    )


def test_parallel_past_fork_limit_lines_still_move_you():
    # Fork into 2 lines, then proceed forwards, forking
    # each time.  Should essentially act as if no forking
    # was happening.
    assert (
        do_eval("F() d=f d*=90 ^ S() F()", n=4, rand=None, max_forks=2) ==
        [
            [
                Line(Pt(0.0, 0.0), Pt(0.0, 10.0)),
                Line(Pt(0.0, 0.0), Pt(10.0, 0.0)),
            ],
            [
                Line(Pt(0.0, 10.0), Pt(0.0, 20.0)),
                Line(Pt(10.0, 0.0), Pt(20.0, 0.0)),
            ],
            [
                Line(Pt(0.0, 20.0), Pt(0.0, 30.0)),
                Line(Pt(20.0, 0.0), Pt(30.0, 0.0)),
            ],
            [
                Line(Pt(0.0, 30.0), Pt(0.0, 40.0)),
                Line(Pt(30.0, 0.0), Pt(40.0, 0.0)),
            ],
        ]
    )


def test_multi_fork_produces_lines_in_sync_with_each_other():
    actuals = do_eval(
        "T(20, F) ^ S()",
        n=21,
        rand=None,
        max_forks=20
    )

    def assert_line(n):
        assert (
            actuals[n] ==
            [Line(Pt(0.0, n * 10.0), Pt(0., (n + 1) * 10.0))] * 20
        )

    assert_line(0)
    assert_line(1)
    assert_line(2)
    # ...
    assert_line(16)
    assert_line(17)
    assert_line(18)
    assert_line(19)
    assert_line(20)


def test_strokes_inside_functions_work():
    assert (
        do_eval("P={S()} P()", n=1) ==
        [[Line(Pt(0.0, 0.0), Pt(0.0, 10.0))]]
    )


def test_if_executes_if_1():
    assert (
        do_eval("If(1,S,{})", 1) ==
        [[Line(Pt(0.0, 0.0), Pt(0.0, 10.0))]]
    )


def test_if_executes_if_minus_1():
    assert (
        do_eval("If(-1,S,{})", 1) ==
        [[Line(Pt(0.0, 0.0), Pt(0.0, 10.0))]]
    )


def test_if_executes_if_nonzero():
    assert (
        do_eval("If(20,S,{})", 1) ==
        [[Line(Pt(0.0, 0.0), Pt(0.0, 10.0))]]
    )


def test_if_does_not_execute_if_zero():
    assert (
        do_eval("If(0,S,{}) D()", 1) ==
        [[Dot(Pt(0.0, 0.0))]]
    )


def test_if_does_not_execute_if_zero_via_expression():
    assert (
        do_eval("If(1-1,S,{}) D()", 1) ==
        [[Dot(Pt(0.0, 0.0))]]
    )


def test_if_executes_if_nonzero_via_symbol():
    assert (
        do_eval("foo=-20 If(foo,S,{})", 1) ==
        [[Line(Pt(0.0, 0.0), Pt(0.0, 10.0))]]
    )


def test_lt_compares_numbers():
    assert (
        do_eval(
            """
            x=0
            If(1<2,{x+=1},{})
            If(2<1,{x+=10},{})
            If(1<1,{x+=100},{})
            D()
            """,
            n=1,
        ) ==
        [[Dot(Pt(1, 0))]]
    )


def test_gt_compares_numbers():
    assert (
        do_eval(
            """
            one=1
            two=2
            x=0
            If(one>two,{x+=1},{})
            If(two>one,{x+=10},{})
            If(one>one,{x+=100},{})
            D()
            """,
            n=1,
        ) ==
        [[Dot(Pt(10, 0))]]
    )


def test_lte_compares_numbers():
    assert (
        do_eval(
            """
            x=0
            If(1<=2,{x+=1},{})
            If(2<=1,{x+=10},{})
            If(1<=1,{x+=100},{})
            D()
            """,
            n=1,
        ) ==
        [[Dot(Pt(101, 0))]]
    )


def test_gte_compares_numbers():
    assert (
        do_eval(
            """
            one=1
            two=2
            x=0
            If(one>=two,{x+=1},{})
            If(two>=one,{x+=10},{})
            If(one>=one,{x+=100},{})
            D()
            """,
            n=1,
        ) ==
        [[Dot(Pt(110, 0))]]
    )


def test_double_equals_compares_numbers():
    assert (
        do_eval(
            """
            one=1
            two=2
            x=0
            If(one==2,{x+=1},{})
            If(2==one,{x+=10},{})
            If(one==one,{x+=100},{})
            If(one==two,{x+=1000},{})
            D()
            """,
            n=1,
        ) ==
        [[Dot(Pt(100, 0))]]
    )


def test_if_expression():
    assert (
        do_eval("foo=3 x=If(foo>0,{1},{-1}) D()", 1) ==
        [[Dot(Pt(1.0, 0.0))]]
    )


def test_For_over_array():
    assert (
        do_eval("arr=[7,2] For(arr,{:(it)x=it D()}) S()", 3) ==
        [
            [Dot(Pt(7.0, 0.0))],
            [Dot(Pt(2.0, 0.0))],
            [Line(Pt(2.0, 0.0), Pt(2.0, 10.0))],
        ]
    )


def test_For_over_double_array():
    assert (
        do_eval(
            """
            For(
                [[1,1],[2,2]],
                {:(it)
                    x=Get(it,0)
                    y=Get(it,1)
                    D()
                }
            )
            S()
            """,
            3
        ) ==
        [
            [Dot(Pt(1.0, 1.0))],
            [Dot(Pt(2.0, 2.0))],
            [Line(Pt(2.0, 2.0), Pt(2.0, 12.0))]
        ]
    )


def test_For_myrange():
    assert (
        do_eval(
            """
            myrange={:(max) i=-1 {i+=1 If(i<max,{i},{endofloop})}}
            For(myrange(5),{:(i) x=i*10 D()})
            """,
            5
        ) ==
        [
            [Dot(Pt(0.0, 0.0))],
            [Dot(Pt(10.0, 0.0))],
            [Dot(Pt(20.0, 0.0))],
            [Dot(Pt(30.0, 0.0))],
            [Dot(Pt(40.0, 0.0))],
        ]
    )
