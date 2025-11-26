import pytest

from novel_downloader.libs.mini_js import MiniJS

# ---------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------


def _assert_raises(expr: str, exc_type: type[BaseException], msg_part: str) -> None:
    """Helper to ensure MiniJS raises the expected error."""
    m = MiniJS()
    with pytest.raises(exc_type) as exc_info:
        m.eval(expr)
    assert msg_part in str(exc_info.value), (
        f"Expected message containing {msg_part!r}, got {str(exc_info.value)!r}"
    )


# ---------------------------------------------------------------------
# Arithmetic / exponentiation
# ---------------------------------------------------------------------


def test_exponentiation():
    m = MiniJS()
    assert m.eval("2 ** 3 ** 2") == 512
    assert m.eval("-2 ** 2") == -4
    assert m.eval("(-2) ** 2") == 4
    assert m.eval("let p=2; p **= 3; p") == 8


def test_arithmetic_and_parens():
    m = MiniJS()
    assert m.eval("2 + 3 * 4") == 14
    assert m.eval("2 * (3 + 4)") == 14
    assert m.eval("10 % 4") == 2
    assert m.eval("let x=10; x %= 6; x") == 4
    assert m.eval("1 / 2") == 0.5


# ---------------------------------------------------------------------
# Bitwise / shifts
# ---------------------------------------------------------------------


def test_bitwise_and_shifts():
    m = MiniJS()
    assert m.eval("5 & 3") == 1
    assert m.eval("5 | 2") == 7
    assert m.eval("5 ^ 1") == 4
    assert m.eval("~0") == -1
    assert m.eval("1 << 5") == 32
    assert m.eval("-2 >> 1") == -1
    assert m.eval("-1 >>> 1") == 2147483647
    assert m.eval("let u=-1; u >>>= 1; u") == 2147483647
    assert m.eval("let a=1; a <<= 3; a") == 8
    assert m.eval("let b=8; b >>= 2; b") == 2
    assert m.eval("let c=8; c &= 6; c") == 0
    assert m.eval("let d=8; d |= 5; d") == 13
    assert m.eval("let e=8; e ^= 1; e") == 9


# ---------------------------------------------------------------------
# Numbers / floats / Infinity / NaN
# ---------------------------------------------------------------------


def test_numbers_and_floats():
    m = MiniJS()
    assert m.eval(".5 + 1.") == 1.5
    assert m.eval("1e3 + 2e2") == 1200
    assert m.eval("Infinity > 1e308") is True
    assert m.eval("NaN == NaN") is False
    assert m.eval("NaN != NaN") is True


# ---------------------------------------------------------------------
# typeof / delete / in
# ---------------------------------------------------------------------


def test_typeof_delete_in():
    m = MiniJS()
    assert m.eval("typeof 1") == "number"
    assert m.eval("typeof 'a'") == "string"
    assert m.eval("typeof true") == "boolean"
    assert m.eval("typeof null") == "undefined"
    assert m.eval("typeof undefined") == "undefined"
    assert m.eval("typeof {a:1}") == "object"
    assert m.eval("typeof (function(x){ return x; })") == "function"
    assert m.eval("typeof notDefinedVar") == "undefined"

    assert m.eval("('x' in {x:1,y:2})") is True
    assert m.eval("2 in [10,20,30]") is True
    assert m.eval("3 in [10,20,30]") is False

    assert m.eval("let o={a:1,b:2}; delete o.a; ('a' in o)") is False
    assert m.eval("let a=[1,2,3]; delete a[1]; a[1] ?? 9") == 9

    _assert_raises("let q=1; delete q", SyntaxError, "Cannot delete variable")


# ---------------------------------------------------------------------
# Logical / nullish
# ---------------------------------------------------------------------


def test_logical_and_nullish():
    m = MiniJS()
    assert m.eval("null ?? 5") == 5
    assert m.eval("undefined ?? 5") == 5
    assert m.eval("0 ?? 5") == 0
    assert m.eval("'' ?? 'x'") == ""
    assert m.eval("0 || (1 && 2)") == 2
    assert m.eval("(null ?? 0) || 5") == 5
    assert m.eval("null ?? 0 || 5") == 5
    assert m.eval("let a=0; a ||= 5; a") == 5
    assert m.eval("let b=1; b ||= 5; b") == 1
    assert m.eval("let c=1; c &&= 9; c") == 9
    assert m.eval("let d=0; d &&= 9; d") == 0
    assert m.eval("let e=null; e ??= 'd'; e") == "d"
    assert m.eval("let f2=0; f2 ??= 8; f2") == 0


# ---------------------------------------------------------------------
# Optional chaining / calls
# ---------------------------------------------------------------------


def test_optional_chaining_and_calls():
    m = MiniJS()
    assert m.eval("let o=null; o?.x") is None
    assert m.eval("let p={x:1}; p?.x") == 1
    assert m.eval("let f=null; f?.(1)") is None
    assert m.eval("let q={inc:function(x){return x+1;}}; q?.inc(4)") == 5
    code = (
        "function make(){ return { add:function(x){ return x+2; } }; } make()?.add(3)"  # noqa: E501
    )
    assert m.eval(code) == 5


# ---------------------------------------------------------------------
# Arrays / objects / indexing
# ---------------------------------------------------------------------


def test_arrays_and_objects():
    m = MiniJS()
    assert m.eval("let a=[1,2]; a[0]+=5; a[0]") == 6
    assert m.eval("let o={x:1}; o.x += 3; o.x") == 4
    assert m.eval("let d={'k':3}; d['k']*=2; d['k']") == 6
    assert m.eval("let z={x:1}; z['x'] === z.x") is True


# ---------------------------------------------------------------------
# Equality / relational
# ---------------------------------------------------------------------


def test_equality_and_relational():
    m = MiniJS()
    assert m.eval("1 == 1") is True
    assert m.eval("1 != 2") is True
    assert m.eval("1 === 1") is True
    assert m.eval("1 !== 1") is False
    assert m.eval("2 < 3") is True
    assert m.eval("3 >= 3") is True
    assert m.eval("3 <= 2") is False


# ---------------------------------------------------------------------
# Conditional / strings
# ---------------------------------------------------------------------


def test_conditional_and_strings():
    m = MiniJS()
    assert m.eval("(null ?? 0) ? 'ok' : 'no'") == "no"
    assert m.eval("'line\\nnext'") == "line\nnext"
    assert m.eval("'\\x41\\u0042'") == "AB"
    assert m.eval("'smile:\\u{1F600}'") == "smile:" + chr(0x1F600)
    assert m.eval("'\\q'") == "q"  # lenient escape


# ---------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------


def test_comments():
    m = MiniJS()
    assert m.eval("// hello world\n42") == 42
    assert m.eval("/* multi\nline */ 7") == 7
    assert m.eval("/* unicode: 你好 */ 6") == 6
    assert m.eval("// crlf\r\n9") == 9


# ---------------------------------------------------------------------
# Functions / closures
# ---------------------------------------------------------------------


def test_functions_and_closures():
    m = MiniJS()
    assert m.eval("function add(a,b){ return a+b; } add(2,3)") == 5
    assert m.eval("let f=function(x){return x*2;}; f(4)") == 8
    assert m.eval("(function(a,b){ return a*b; })(3,4)") == 12
    assert m.eval("(function(a,b){ return a+b; }(1, 2))") == 3
    code = (
        "function maker(a){ return function(b){ return a + b; }; } "
        "let f = maker(3); f(4)"
    )
    assert m.eval(code) == 7
    _assert_raises(
        "function g(x,y){ return x+y; } g(1)", Exception, "Expected 2 arguments"
    )


def test_identifier_with_dollar_and_underscore():
    m = MiniJS()
    assert m.eval("(function($){ return $ + 1; })(2)") == 3
    assert m.eval("let let$ = 10; let$ + 2") == 12
    code = "(function(_, $, aa, ab){ return _ + $ + aa + ab; })(1,2,3,4)"
    assert m.eval(code) == 10


# ---------------------------------------------------------------------
# Env persistence / cleanup
# ---------------------------------------------------------------------


def test_env_and_cleanup():
    m = MiniJS()
    assert m.eval("let x=10;") is None
    assert m.eval("x+1") == 11
    assert m.eval("let y=1; y; 2") == 2
    m.clean_env()
    _assert_raises("x", Exception, "is not defined")


# ---------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------


def test_error_paths():
    _assert_raises("(1).x", TypeError, "Member access on non-object")
    _assert_raises("'a'.x", TypeError, "Member access on non-object")
    _assert_raises("let x=3; x(1)", TypeError, "non-function")
    _assert_raises("'a'[0]", TypeError, "Indexing on unsupported type")
