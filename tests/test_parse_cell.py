import pytest
from graftlib.lex_cell import lex_cell
from graftlib.labeltree import LabelTree
from graftlib.parse_cell import (
    parse_cell,
    ArrayTree,
    AssignmentTree,
    FunctionCallTree,
    FunctionDefTree,
    ModifyTree,
    NegativeTree,
    NumberTree,
    OperationTree,
    StringTree,
    SymbolTree,
)

# --- Utils ---


def parsed(inp):
    return list(parse_cell(lex_cell(inp)))


# --- Parsing ---


def test_Empty_file_produces_nothing():
    assert parsed("") == []


def test_Number_is_parsed_as_expression():
    assert parsed("56") == [NumberTree("56")]


def test_Negative_number_is_parsed_as_expression():
    assert parsed("-56") == [NegativeTree(NumberTree("56"))]


def test_Sum_of_numbers_is_parsed_as_expression():
    assert (
        parsed("32+44") ==
        [
            OperationTree("+", NumberTree("32"), NumberTree("44"))
        ]
    )


def test_Sum_of_negative_numbers_is_parsed_as_expression():
    assert (
        parsed("32+-44") ==
        [
            OperationTree(
                "+",
                NumberTree("32"),
                NegativeTree(NumberTree("44")),
            )
        ]
    )


def test_Difference_of_symbol_and_number_is_parsed_as_expression():
    assert (
        parsed("foo-44") ==
        [
            OperationTree("-", SymbolTree("foo"), NumberTree("44"))
        ]
    )


def test_Modify_symbol_is_parsed_as_expression():
    assert (
        parsed("foo-=44") ==
        [
            ModifyTree("-=", SymbolTree("foo"), NumberTree("44"))
        ]
    )


def test_Modify_by_negative_is_parsed_as_expression():
    assert (
        parsed("foo*=-44") ==
        [
            ModifyTree(
                "*=",
                SymbolTree("foo"), NegativeTree(NumberTree("44"))
            )
        ]
    )


def test_Modify_nonsymbol_is_an_error():
    with pytest.raises(
        Exception,
        match=r"You can't modify \(\*=\) anything except a symbol\."
    ):
        parsed("3*=44")


def test_Multiplication_of_symbols_is_parsed_as_expression():
    assert (
        parsed("foo*bar") ==
        [
            OperationTree("*", SymbolTree("foo"), SymbolTree("bar"))
        ]
    )


def test_Multiplication_of_negative_symbols_is_parsed_as_expression():
    assert (
        parsed("foo*-bar") ==
        [
            OperationTree(
                "*",
                SymbolTree("foo"),
                NegativeTree(SymbolTree("bar"))
            )
        ]
    )


def test_Variable_assignment_gets_parsed():
    assert (
        parsed("x=3") ==
        [
            AssignmentTree(SymbolTree("x"), NumberTree("3"))
        ]
    )


def test_Variable_assignment_to_negative_gets_parsed():
    assert (
        parsed("x=--3") ==
        [
            AssignmentTree(
                SymbolTree("x"),
                NegativeTree(NegativeTree(NumberTree("3"))),
            )
        ]
    )


def test_Function_call_with_no_args_gets_parsed():
    assert (
        parsed("print()") ==
        [
            FunctionCallTree(SymbolTree("print"), [])
        ]
    )


def test_Label_is_parsed():
    assert (
        parsed("12 ^ 3") ==
        [NumberTree(value='12'), LabelTree(), NumberTree(value='3')]
    )


def test_Comparisons_are_parsed():
    assert (
        parsed("12<3") ==
        [OperationTree("<", NumberTree("12"), NumberTree("3"))]
    )
    assert (
        parsed("12>x") ==
        [OperationTree(">", NumberTree("12"), SymbolTree("x"))]
    )
    assert (
        parsed("x<=1") ==
        [OperationTree("<=", SymbolTree("x"), NumberTree("1"))]
    )
    assert (
        parsed("y>=x") ==
        [OperationTree(">=", SymbolTree("y"), SymbolTree("x"))]
    )
    assert (
        parsed("y==x") ==
        [OperationTree("==", SymbolTree("y"), SymbolTree("x"))]
    )


def test_Function_call_with_various_args_gets_parsed():
    assert (
        parsed("print('a',3,4/12)") ==
        [
            FunctionCallTree(
                SymbolTree("print"),
                [
                    StringTree("a"),
                    NumberTree("3"),
                    OperationTree("/", NumberTree("4"), NumberTree("12"))
                ]
            )
        ]
    )


def test_Multiple_function_calls_with_no_args_get_parsed():
    assert (
        parsed("print()()") ==
        [
            FunctionCallTree(FunctionCallTree(SymbolTree("print"), []), [])
        ]
    )


def test_Multiple_function_calls_with_various_args_get_parsed():
    assert (
        parsed("print('a',3,4/12)(512)()") ==
        [
            FunctionCallTree(
                FunctionCallTree(
                    FunctionCallTree(
                        SymbolTree("print"),
                        [
                            StringTree("a"),
                            NumberTree("3"),
                            OperationTree(
                                "/",
                                NumberTree("4"),
                                NumberTree("12")
                            )
                        ]
                    ),
                    [
                        NumberTree("512")
                    ]
                ),
                []
            )
        ]
    )


def test_Assigning_to_a_number_is_an_error():
    with pytest.raises(
        Exception,
        match=r"You can't assign to anything except a symbol."
    ):
        parsed("3=x")


def test_Assigning_to_an_expression_is_an_error():
    with pytest.raises(
        Exception,
        match=r"You can't assign to anything except a symbol."
    ):
        parsed("x(4)=5")


def test_Empty_function_definition_gets_parsed():
    assert (
        parsed("{}") ==
        [
            FunctionDefTree([], [])
        ]
    )


def test_Missing_param_definition_with_colon_is_an_error():
    with pytest.raises(
        Exception,
        match=r"':' must be followed by '\(' in a function."
    ):
        parsed("{:print(x))")


def test_Multiple_commands_parse_into_multiple_expressions():
    program = """
    x=3
    func={:(a)print(a)}
    func(x)
    """
    assert (
        parsed(program) ==
        [
            AssignmentTree(SymbolTree('x'), NumberTree('3')),
            AssignmentTree(
                SymbolTree('func'),
                FunctionDefTree(
                    [SymbolTree('a')],
                    [
                        FunctionCallTree(
                            SymbolTree('print'), [SymbolTree('a')])
                    ]
                )
            ),
            FunctionCallTree(SymbolTree('func'), [SymbolTree('x')])
        ]
    )


def test_Empty_function_definition_with_params_gets_parsed():
    assert (
        parsed("{:(aa,bb,cc,dd)}") ==
        [
            FunctionDefTree(
                [
                    SymbolTree("aa"),
                    SymbolTree("bb"),
                    SymbolTree("cc"),
                    SymbolTree("dd"),
                ],
                []
            )
        ]
    )


def test_Trailing_comma_in_arg_list_is_ignored():
    assert (
        parsed("{:(aa,bb,)}") ==
        [
            FunctionDefTree(
                [
                    SymbolTree("aa"),
                    SymbolTree("bb"),
                ],
                []
            )
        ]
    )


def test_Function_params_that_are_not_symbols_is_an_error():
    with pytest.raises(
        Exception,
        match=(
            "Only symbols are allowed in function parameter lists. " +
            "I found: " +
            r"OperationTree\(operation='\+', " +
            r"left=SymbolTree\(value='aa'\), " +
            r"right=NumberTree\(value='3'\)\)."
            # TODO: show original code
        )
    ):
        parsed("{:(aa+3,d)}")


def test_Unended_function_call_is_an_error():
    with pytest.raises(
        Exception,
        match=r"Hit end of file - expected '\)'"
    ):
        parsed("pr(")


def test_Unended_function_params_is_an_error():
    with pytest.raises(
        Exception,
        match=r"Unexpected token: \}"
    ):
        parsed("{:(}")


def test_Unended_function_def_is_an_error():
    with pytest.raises(
        Exception,
        match=r"Hit end of file - expected '\}'"
    ):
        parsed("{")


def test_Unended_nested_function_def_is_an_error():
    with pytest.raises(
        Exception,
        match=r"Hit end of file - expected '\}'"
    ):
        parsed("x=3 f() {:(y){} print(4)")


def test_Function_definition_containing_commands_gets_parsed():
    assert (
        parsed('{print(3-4) a="x" print(a)}') ==
        [
            FunctionDefTree(
                [],
                [
                    FunctionCallTree(
                        SymbolTree("print"),
                        [
                            OperationTree(
                                '-',
                                NumberTree('3'),
                                NumberTree('4')
                            )
                        ]
                    ),
                    AssignmentTree(SymbolTree("a"), StringTree("x")),
                    FunctionCallTree(SymbolTree("print"), [SymbolTree("a")])
                ]
            )
        ]
    )


def test_Function_definition_with_params_and_commands_gets_parsed():
    assert (
        parsed('{:(x,yy)print(3-4) a="x" print(a)}') ==
        [
            FunctionDefTree(
                [
                    SymbolTree("x"),
                    SymbolTree("yy")
                ],
                [
                    FunctionCallTree(
                        SymbolTree("print"),
                        [
                            OperationTree(
                                '-',
                                NumberTree('3'),
                                NumberTree('4')
                            )
                        ]
                    ),
                    AssignmentTree(SymbolTree("a"), StringTree("x")),
                    FunctionCallTree(SymbolTree("print"), [SymbolTree("a")])
                ]
            )
        ]
    )


def test_A_complex_example_program_parses():
    example = """
        double={:(x)2*x}

        num1=3
        num2=double(num)

        answer=if(greater_than(num2,5),{"LARGE!"},{"small."})

        print(answer)
    """
    parsed(example)


def test_Spaces_are_allowed_where_unimportant():
    assert (
        parsed('''
        {:( x, y )
            x+y
            foo( 3 )
        }( 3, 4 )
        ''') ==
        [
            FunctionCallTree(
                FunctionDefTree(
                    [
                        SymbolTree("x"),
                        SymbolTree("y"),
                    ],
                    [
                        OperationTree(
                            '+',
                            SymbolTree("x"),
                            SymbolTree("y"),
                        ),
                        FunctionCallTree(
                            SymbolTree("foo"),
                            [
                                NumberTree("3"),
                            ]
                        ),
                    ]
                ),
                [
                    NumberTree("3"),
                    NumberTree("4"),
                ]
            )
        ]
    )


def test_Array_literal_parses():
    assert (
        parsed("[3,4]") ==
        [
            ArrayTree(
                [
                    NumberTree("3"),
                    NumberTree("4"),
                ],
            )
        ]
    )


def test_Trailing_comma_in_array_is_ignored():
    assert (
        parsed("[a, bb,]") ==
        [
            ArrayTree(
                [
                    SymbolTree("a"),
                    SymbolTree("bb"),
                ],
            )
        ]
    )
