import pytest
from graftlib.lex_cell import (
    lex_cell,
    AssignmentToken,
    EndArrayToken,
    EndFunctionDefToken,
    EndParamListToken,
    LabelToken,
    ListSeparatorToken,
    ModifyToken,
    NumberToken,
    OperatorToken,
    ParamListPreludeToken,
    StartArrayToken,
    StartFunctionDefToken,
    StartParamListToken,
    StatementSeparatorToken,
    StringToken,
    SymbolToken,
)

# --- Utils ---


def lexed(inp):
    return list(lex_cell(inp))


# --- Lexing ---


def test_Empty_file_produces_nothing():
    assert lexed("") == []


def test_Open_bracket_produces_open_bracket_token():
    assert lexed("(") == [StartParamListToken()]


def test_Close_bracket_produces_close_bracket_token():
    assert lexed(")") == [EndParamListToken()]


def test_Open_brace_produces_open_brace_token():
    assert lexed("{") == [StartFunctionDefToken()]


def test_Close_brace_produces_close_brace_token():
    assert lexed("}") == [EndFunctionDefToken()]


def test_Multiple_brackets_become_multiple_tokens():
    assert lexed("()") == [StartParamListToken(), EndParamListToken()]


def test_Single_letter_becomes_a_symbol_token():
    assert lexed("a") == [SymbolToken("a")]


def test_Multiple_letters_become_a_symbol_token():
    assert lexed("foo") == [SymbolToken("foo")]


def test_A_caret_becomes_a_label_token():
    assert lexed("^") == [LabelToken()]
    assert (
        lexed("a^b") ==
        [
            SymbolToken("a"),
            LabelToken(),
            SymbolToken("b"),
        ]
    )


def test_A_symbol_followed_by_a_bracket_becomes_two_tokens():
    assert lexed("foo(") == [SymbolToken("foo"), StartParamListToken()]


def test_Items_separated_by_spaces_become_separate_tokens():
    assert (
        lexed("foo bar ( ") ==
        [
            SymbolToken("foo"),
            StatementSeparatorToken(),
            SymbolToken("bar"),
            StatementSeparatorToken(),
            StartParamListToken(),
            StatementSeparatorToken(),
        ]
    )


def test_Items_separated_by_newlines_become_separate_tokens():
    assert (
        lexed("foo\nbar") ==
        [
            SymbolToken("foo"),
            StatementSeparatorToken(),
            SymbolToken("bar")
        ]
    )


def test_Symbols_may_contain_numbers_and_underscores():
    assert (
        lexed("foo2_bar (") ==
        [
            SymbolToken("foo2_bar"),
            StatementSeparatorToken(),
            StartParamListToken()
        ]
    )


def test_Symbols_may_start_with_underscores():
    assert (
        lexed("_foo2_bar (") ==
        [
            SymbolToken("_foo2_bar"),
            StatementSeparatorToken(),
            StartParamListToken()
        ]
    )


def test_Integers_are_parsed_into_number_tokens():
    assert lexed("128") == [NumberToken("128")]


def test_Floating_points_are_parsed_into_number_tokens():
    assert lexed("12.8") == [NumberToken("12.8")]


def test_Leading_decimal_point_produces_number_token():
    assert lexed(".812") == [NumberToken(".812")]


def test_Double_quoted_values_produce_string_tokens():
    assert lexed('"foo"') == [StringToken('foo')]


def test_Single_quoted_values_produce_string_tokens():
    assert lexed("'foo'") == [StringToken('foo')]


def test_Different_quote_types_allow_the_other_type_inside():
    assert lexed("'f\"oo'") == [StringToken('f"oo')]
    assert lexed('"f\'oo"') == [StringToken("f'oo")]


def test_Empty_quotes_produce_an_empty_string_token():
    assert lexed('""') == [StringToken('')]


def test_An_unfinished_string_is_an_error():
    with pytest.raises(
        Exception,
        message=r'A string ran off the end of the program.'
    ):
        lexed('"foo')


def test_Commas_produce_comma_tokens():
    assert lexed(",") == [ListSeparatorToken()]


def test_Equals_produces_an_equals_token():
    assert lexed("=") == [AssignmentToken()]


def test_Spaces_produce_separator_tokens():
    assert lexed(" ") == [StatementSeparatorToken()]
    assert lexed("  ") == [StatementSeparatorToken()]
    assert lexed(" \n  ") == [StatementSeparatorToken()]


def test_Colons_produce_colon_tokens():
    assert lexed(":") == [ParamListPreludeToken()]


def test_Arithmetic_operators_produce_operation_tokens():
    assert lexed("+") == [OperatorToken("+")]
    assert lexed("-") == [OperatorToken("-")]
    assert lexed("*") == [OperatorToken("*")]
    assert lexed("/") == [OperatorToken("/")]
    assert lexed("<") == [OperatorToken("<")]
    assert lexed(">") == [OperatorToken(">")]
    assert lexed("<=") == [OperatorToken("<=")]
    assert lexed(">=") == [OperatorToken(">=")]
    assert lexed("==") == [OperatorToken("==")]


def test_Modify_operators_modify_tokens():
    assert lexed("+=") == [ModifyToken("+=")]
    assert lexed("-=") == [ModifyToken("-=")]
    assert lexed("*=") == [ModifyToken("*=")]
    assert lexed("/=") == [ModifyToken("/=")]


def test_Multiple_token_types_can_be_combined():
    assert (
        lexed('frobnicate("Hello"+name,4/5.0) ') ==
        [
            SymbolToken("frobnicate"),
            StartParamListToken(),
            StringToken("Hello"),
            OperatorToken("+"),
            SymbolToken("name"),
            ListSeparatorToken(),
            NumberToken("4"),
            OperatorToken("/"),
            NumberToken("5.0"),
            EndParamListToken(),
            StatementSeparatorToken(),
        ]
    )


def test_A_complex_example_program_lexes():
    example = """
        double={:(x)2*x}
        num1=3
        ^
        num2=double(num)
        answer=if(greater_than(num2,5),{"LARGE!"},{"small."})
        print(answer)
    """
    lexed(example)


def test_Tabs_are_an_error():
    with pytest.raises(
        Exception,
        message=r'Tab characters are not allowed in Graft.'
    ):
        lexed("aaa\tbbb")


def test_Square_brackets_produce_array_tokens():
    assert (
        lexed("[3,4]") ==
        [
            StartArrayToken(),
            NumberToken("3"),
            ListSeparatorToken(),
            NumberToken("4"),
            EndArrayToken(),
        ]
    )
