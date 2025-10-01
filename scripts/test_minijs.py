#!/usr/bin/env python3
from novel_downloader.libs.mini_js import MiniJS


def _assert_raises(expr: str, exc_type: type[BaseException], msg_part: str) -> None:
    m = MiniJS()
    try:
        m.eval(expr)
    except Exception as e:
        assert isinstance(
            e, exc_type
        ), f"Expected {exc_type.__name__}, got {type(e).__name__}"
        assert msg_part in str(
            e
        ), f"Expected message containing {msg_part!r}, got {str(e)!r}"
    else:
        raise AssertionError(f"Expected {exc_type.__name__} for: {expr}")


# ---------- arithmetic / exponentiation ----------
def test_exponent():
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


# ---------- bitwise / shifts ----------
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


# ---------- numbers / floats / Infinity / NaN ----------
def test_numbers_and_floats():
    m = MiniJS()
    assert m.eval(".5 + 1.") == 1.5
    assert m.eval("1e3 + 2e2") == 1200
    assert m.eval("Infinity > 1e308") is True
    assert m.eval("NaN == NaN") is False
    assert m.eval("NaN != NaN") is True


# ---------- typeof / delete / in ----------
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

    # delete variable => error
    _assert_raises("let q=1; delete q", SyntaxError, "Cannot delete variable")


# ---------- logical / nullish / compound logical assignment ----------
def test_logical_and_nullish():
    m = MiniJS()
    assert m.eval("null ?? 5") == 5
    assert m.eval("undefined ?? 5") == 5
    assert m.eval("0 ?? 5") == 0
    assert m.eval("'' ?? 'x'") == ""

    assert m.eval("0 || (1 && 2)") == 2
    assert m.eval("(null ?? 0) || 5") == 5
    assert m.eval("null ?? 0 || 5") == 5

    # ||= &&= ??=
    assert m.eval("let a=0; a ||= 5; a") == 5
    assert m.eval("let b=1; b ||= 5; b") == 1
    assert m.eval("let c=1; c &&= 9; c") == 9
    assert m.eval("let d=0; d &&= 9; d") == 0
    assert m.eval("let e=null; e ??= 'd'; e") == "d"
    assert m.eval("let f2=0; f2 ??= 8; f2") == 0


# ---------- optional chaining / calls ----------
def test_optional_chaining_and_calls():
    m = MiniJS()
    assert m.eval("let o=null; o?.x") is None
    assert m.eval("let p={x:1}; p?.x") == 1
    assert m.eval("let f=null; f?.(1)") is None
    assert m.eval("let q={inc:function(x){return x+1;}}; q?.inc(4)") == 5
    assert (
        m.eval(
            "function make(){ return { add:function(x){ return x+2; } }; } make()?.add(3)"  # noqa: E501
        )
        == 5
    )


# ---------- arrays / objects / indexing / compound assignment ----------
def test_arrays_objects():
    m = MiniJS()
    assert m.eval("let a=[1,2]; a[0]+=5; a[0]") == 6
    assert m.eval("let o={x:1}; o.x += 3; o.x") == 4
    assert m.eval("let d={'k':3}; d['k']*=2; d['k']") == 6
    assert m.eval("let z={x:1}; z['x'] === z.x") is True


# ---------- equality / relational ----------
def test_equality_relational():
    m = MiniJS()
    assert m.eval("1 == 1") is True
    assert m.eval("1 != 2") is True
    assert m.eval("1 === 1") is True
    assert m.eval("1 !== 1") is False
    assert m.eval("2 < 3") is True
    assert m.eval("3 >= 3") is True
    assert m.eval("3 <= 2") is False


# ---------- conditional (ternary) and strings ----------
def test_conditional_and_strings():
    m = MiniJS()
    assert m.eval("(null ?? 0) ? 'ok' : 'no'") == "no"
    assert m.eval("'line\\nnext'") == "line\nnext"
    assert m.eval("'\\x41\\u0042'") == "AB"
    assert m.eval("'smile:\\u{1F600}'") == "smile:" + chr(0x1F600)
    # unknown escape: lenient handling drops backslash
    assert m.eval("'\\q'") == "q"


# ---------- comments (line/block, unicode in comments) ----------
def test_comments():
    m = MiniJS()
    assert m.eval("// hello world\n42") == 42
    assert m.eval("/* multi\nline */ 7") == 7
    assert m.eval("/* unicode: 你好 */ 6") == 6
    # CRLF after comment (ensure no crash)
    assert m.eval("// crlf\r\n9") == 9


# ---------- functions: decl, expr, IIFE, closures, arg count ----------
def test_functions_and_iife_and_closure():
    m = MiniJS()
    # decl + call
    assert m.eval("function add(a,b){ return a+b; } add(2,3)") == 5
    # expr + call
    assert m.eval("let f=function(x){return x*2;}; f(4)") == 8
    # classic IIFE
    assert m.eval("(function(a,b){ return a*b; })(3,4)") == 12
    # alt IIFE variant inside parens then call inside
    assert m.eval("(function(a,b){ return a+b; }(1, 2))") == 3
    # closure
    code = (
        "function maker(a){ "
        "  return function(b){ return a + b; }; "
        "} "
        "let f = maker(3); "
        "f(4)"
    )
    assert m.eval(code) == 7
    # arg count mismatch
    try:
        m.eval("function g(x,y){ return x+y; } g(1)")
    except Exception as e:
        assert "Expected 2 arguments" in str(e)


def test_identifier_with_dollar_and_underscore():
    m = MiniJS()
    assert m.eval("(function($){ return $ + 1; })(2)") == 3
    assert m.eval("let let$ = 10; let$ + 2") == 12
    code = "(function(_, $, aa, ab){ return _ + $ + aa + ab; })(1,2,3,4)"
    assert m.eval(code) == 10


# ---------- environment persistence / cleaning / last expr ----------
def test_env_and_clean_and_last_expr():
    m = MiniJS()
    assert m.eval("let x=10;") is None
    assert m.eval("x+1") == 11
    assert m.eval("let y=1; y; 2") == 2
    m.clean_env()
    try:
        m.eval("x")
    except Exception as e:
        assert "is not defined" in str(e)


# ---------- error paths ----------
def test_error_paths():
    # member access on non-object
    _assert_raises("(1).x", TypeError, "Member access on non-object")
    _assert_raises("'a'.x", TypeError, "Member access on non-object")
    # call on non-function
    _assert_raises("let x=3; x(1)", TypeError, "non-function")
    # index on unsupported type
    _assert_raises("'a'[0]", TypeError, "Indexing on unsupported type")


def main() -> int:
    test_exponent()
    test_arithmetic_and_parens()
    test_bitwise_and_shifts()
    test_numbers_and_floats()
    test_typeof_delete_in()
    test_logical_and_nullish()
    test_optional_chaining_and_calls()
    test_arrays_objects()
    test_equality_relational()
    test_conditional_and_strings()
    test_comments()
    test_functions_and_iife_and_closure()
    test_identifier_with_dollar_and_underscore()
    test_env_and_clean_and_last_expr()
    test_error_paths()
    print("All MiniJS tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
