"""Math agent with optional sympy support and a safe fallback for arithmetic."""

try:
    from sympy import sympify, Eq, solve
    try:
        from sympy.core.sympify import SympifyError
    except Exception:
        # sympy older/newer versions may differ; provide a base Exception fallback
        class SympifyError(Exception):
            pass
    _HAS_SYMPY = True
except Exception:
    # define SympifyError as a local fallback so code can reference it safely
    class SympifyError(Exception):
        pass
    sympify = None
    Eq = None
    solve = None
    _HAS_SYMPY = False

from functools import lru_cache
import re
import ast
import operator as _operator


# Use a cached helper for potentially expensive symbolic work
@lru_cache(maxsize=256)
def _compute_math_cached(query: str) -> str:
    """Cached computation for math queries. Returns a string response.

    Caching key is the raw query string. This is purposely simple and safe.
    """
    q = query.strip()
    if not q:
        return "Please provide a math expression or a simple equation."

    # Normalize common math notations to make parsing more robust
    def _normalize(expr: str) -> str:
        # replace unicode minus, multiply signs, etc.
        expr = expr.replace('\u2212', '-')  # unicode minus
        expr = expr.replace('\u00d7', '*')  # multiplication sign
        expr = expr.replace('\u00f7', '/')  # division sign
        # caret to python power
        expr = expr.replace('^', '**')
        # implicit multiplication: convert patterns like '2x' or ')x' to '2*x' or ')*x'
        expr = re.sub(r"(?P<num>\d)\s*(?P<var>[a-zA-Z(\\])", r"\g<num>*\g<var>", expr)
        # convert common unicode pi to 'pi' for sympy if available
        expr = expr.replace('\u03c0', 'pi')
        return expr

    q_norm = _normalize(q)

    if _HAS_SYMPY:
        try:
            if "=" in q_norm:
                left, right = q_norm.split("=", 1)
                expr_left = sympify(left)
                expr_right = sympify(right)
                eq = Eq(expr_left, expr_right)
                vars = list(eq.free_symbols)
                if not vars:
                    return f"Equation simplifies to: {eq}; no variables to solve for."
                sol = solve(eq, *vars)
                return f"Equation: {eq}\nSolution: {sol}"
            else:
                expr = sympify(q_norm)
                simplified = expr.simplify()
                return f"Expression: {expr}\nSimplified: {simplified}"
        except SympifyError:
            return "I couldn't parse that math expression. Try something simpler like '2+2' or '3*x+1=10'."
        except Exception as e:
            return f"Error processing math query: {e}"
    else:
        # Fallback numeric evaluation (safe-ish)
        try:
            # Normalize before attempting numeric evaluation
            if "=" in q_norm:
                left, right = q_norm.split("=", 1)
                # safe numeric eval using AST
                left_val = _safe_eval(left)
                right_val = _safe_eval(right)
                return f"Equation numeric test: {left_val} == {right_val} -> {left_val == right_val} (sympy not installed)"
            else:
                # allow digits, operators, parentheses, spaces, and decimal point
                allowed = set("0123456789+-*/(). eE")
                if any(ch not in allowed for ch in q_norm):
                    return "Sympy not available and expression contains unsupported characters. Install sympy for full support."
                val = _safe_eval(q_norm)
                return f"Expression numeric result: {val} (install sympy for symbolic simplification)"
        except Exception:
            return "Unable to evaluate expression without sympy. Install sympy or provide a simpler arithmetic expression."


# Safe AST evaluator for numeric expressions (no names, no calls)
def _safe_eval(expr: str):
    """Evaluate a numeric expression safely using ast.

    Supports: +, -, *, /, **, parentheses, unary +/-, floats and ints, scientific notation.
    """
    node = ast.parse(expr, mode='eval')

    def _eval(n):
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.BinOp):
            left = _eval(n.left)
            right = _eval(n.right)
            op = n.op
            ops = {
                ast.Add: _operator.add,
                ast.Sub: _operator.sub,
                ast.Mult: _operator.mul,
                ast.Div: _operator.truediv,
                ast.Pow: _operator.pow,
                ast.Mod: _operator.mod,
            }
            for t, fn in ops.items():
                if isinstance(op, t):
                    return fn(left, right)
            raise ValueError(f"Unsupported binary operator: {op}")
        if isinstance(n, ast.UnaryOp):
            operand = _eval(n.operand)
            if isinstance(n.op, ast.UAdd):
                return +operand
            if isinstance(n.op, ast.USub):
                return -operand
            raise ValueError(f"Unsupported unary operator: {n.op}")
        if isinstance(n, ast.Call):
            raise ValueError("Function calls not allowed in math expressions")
        if isinstance(n, ast.Name):
            # disallow names; user must have sympy for symbolic variables
            raise ValueError("Symbolic names not supported without sympy")
        raise ValueError(f"Unsupported expression: {ast.dump(n)}")

    return _eval(node)


def _solve_simple_linear(equation: str):
    """Attempt to solve very simple linear equations with one variable.

    Supports patterns like '2*x+3=7', '2x+3=7', 'x+3=7', '-3x+2=8'. Returns solution string or None.
    """
    expr = equation.strip()
    # remove spaces and normalize implicit multiplication (e.g., 2x -> 2*x, x2 -> x*2, )( -> )*( )x -> )*x )x or x(y) handled)
    expr = expr.replace(' ', '')
    # insert * between digit and letter or digit and '('
    expr = re.sub(r'(?<=\d)(?=[A-Za-z_(])', '*', expr)
    # insert * between letter or ')' and digit or '('
    expr = re.sub(r'(?<=[A-Za-z\)])(?=\d|\()', '*', expr)

    if '=' not in expr:
        return None
    left_s, right_s = expr.split('=', 1)

    # find candidate variable names (identifiers) excluding known math functions
    candidates = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expr)
    funcs = {'sin', 'cos', 'tan', 'log', 'ln', 'exp', 'sqrt'}
    var = None
    for c in candidates:
        if c.lower() not in funcs and not re.match(r'^e$|^pi$', c.lower()):
            var = c
            break
    if not var:
        return None

    # parse expressions into linear coefficients a*var + b
    def _parse_linear(side: str):
        try:
            node = ast.parse(side, mode='eval')
        except Exception:
            return None

        def walk(n):
            # returns (a, b) meaning a*var + b
            if isinstance(n, ast.Expression):
                return walk(n.body)
            if isinstance(n, ast.Constant):
                return (0.0, float(n.value))
            if isinstance(n, ast.Name):
                if n.id == var:
                    return (1.0, 0.0)
                # treat other names as unknown (fail)
                raise ValueError(f"Unknown name: {n.id}")
            if isinstance(n, ast.UnaryOp):
                a, b = walk(n.operand)
                if isinstance(n.op, ast.USub):
                    return (-a, -b)
                if isinstance(n.op, ast.UAdd):
                    return (a, b)
                raise ValueError("Unsupported unary op")
            if isinstance(n, ast.BinOp):
                if isinstance(n.op, (ast.Add, ast.Sub)):
                    a1, b1 = walk(n.left)
                    a2, b2 = walk(n.right)
                    if isinstance(n.op, ast.Add):
                        return (a1 + a2, b1 + b2)
                    else:
                        return (a1 - a2, b1 - b2)
                if isinstance(n.op, ast.Mult):
                    # one side must be constant
                    try:
                        a1, b1 = walk(n.left)
                        a2, b2 = walk(n.right)
                    except ValueError:
                        raise
                    # if left is constant (a1==0) and right linear, multiply
                    if abs(a1) < 1e-12 and abs(a2) >= 0:
                        const = b1
                        return (a2 * const, b2 * const)
                    if abs(a2) < 1e-12 and abs(a1) >= 0:
                        const = b2
                        return (a1 * const, b1 * const)
                    # nonlinear (var*var) or complex multiplication
                    raise ValueError("Non-linear term encountered")
                if isinstance(n.op, ast.Div):
                    a1, b1 = walk(n.left)
                    # right must be constant
                    if isinstance(n.right, ast.Constant):
                        denom = float(n.right.value)
                        if denom == 0:
                            raise ValueError("Division by zero")
                        return (a1 / denom, b1 / denom)
                    raise ValueError("Non-constant divisor")
                if isinstance(n.op, ast.Pow):
                    # any power of variable is nonlinear
                    raise ValueError("Non-linear power encountered")
            raise ValueError("Unsupported node")

        try:
            return walk(node)
        except Exception:
            return None

    left_coeffs = _parse_linear(left_s)
    right_coeffs = _parse_linear(right_s)
    if not left_coeffs or not right_coeffs:
        return None

    a_left, b_left = left_coeffs
    a_right, b_right = right_coeffs

    denom = (a_left - a_right)
    if abs(denom) < 1e-12:
        return None
    sol = (b_right - b_left) / denom
    if abs(sol - int(sol)) < 1e-8:
        sol_str = str(int(sol))
    else:
        sol_str = str(sol)
    return f"Solution: {var} = {sol_str}"


def _extract_mcq(text: str):
    """Attempt to extract MCQ options from text.

    Returns (question_text, options_dict) where options_dict maps labels ('A','B',...) to option text.
    Returns (None, None) if no MCQ-like structure detected.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines or len(lines) < 2:
        return None, None

    option_pattern = re.compile(r'^([A-Z]|\d+)\s*[\)\.\:]\s*(.+)$')
    options = {}
    first_option_idx = None
    for i, ln in enumerate(lines):
        m = option_pattern.match(ln)
        if m:
            label = m.group(1)
            # normalize numeric labels to letters if possible
            if label.isdigit():
                # convert 1->A, 2->B, etc., only if small
                try:
                    n = int(label)
                    if 1 <= n <= 26:
                        label = chr(ord('A') + n - 1)
                except Exception:
                    pass
            opt_text = m.group(2).strip()
            options[label.upper()] = opt_text
            if first_option_idx is None:
                first_option_idx = i

    # also accept inline options like 'A) x, B) y, C) z' on single line
    if not options:
        inline_pattern = re.compile(r'([A-Z])\s*[\)\.\:]\s*([^,;]+)')
        inline = inline_pattern.findall(text)
        if inline and len(inline) >= 2:
            for lbl, txt in inline:
                options[lbl.upper()] = txt.strip()
            # question is everything before first inline label occurrence
            qpos = min((text.find(lbl + ')') if text.find(lbl + ')') >= 0 else text.find(lbl + '.') for lbl, _ in inline))
            question = text[:qpos].strip() if qpos and qpos > 10 else text
            return question, options

    if not options or len(options) < 2:
        return None, None

    # build question as the text before the first option line
    question_lines = lines[:first_option_idx] if first_option_idx is not None else lines
    question = '\n'.join(question_lines).strip()
    if not question:
        # if no leading question lines, maybe the whole text minus option labels
        question = re.sub(r'^([A-Z]|\d+)\s*[\)\.\:]', '', text)
    return question, options


def _parse_option_value(opt_text: str):
    """Try to parse an option text into a numeric or symbolic value.

    Returns (value, kind) where kind is 'numeric', 'symbolic', or 'special'.
    """
    txt = opt_text.strip()
    low = txt.lower()
    if low in ("none of the above", "none of these", "not given", "no option"):
        return (txt, 'special')

    # try to strip leading labels like 'x = 3' -> keep right side
    if '=' in txt and len(txt) < 40:
        # prefer the right-hand side if it's short
        parts = txt.split('=', 1)
        candidate = parts[1].strip()
    else:
        candidate = txt

    # try to normalize common forms: percentages, fractions, radicals
    # percentages: '75%' -> '75/100'
    if re.search(r'%$', candidate):
        try:
            num = float(candidate.strip().rstrip('%'))
            candidate = f"({num}/100)"
        except Exception:
            pass

    # simple fraction like '3/4' should be kept
    # radicals: replace '√' with 'sqrt'
    candidate = candidate.replace('√', 'sqrt')

    # try sympy first
    if _HAS_SYMPY:
        try:
            val = sympify(candidate)
            return (val, 'symbolic')
        except Exception:
            pass

    # fallback numeric parse using safe eval
    # remove commas
    candidate_clean = candidate.replace(',', '')
    # extract leading numeric expression
    m = re.search(r'[0-9\(\)\.\+\-\*/\^eE]+', candidate_clean)
    if m:
        expr = m.group(0)
        expr = expr.replace('^', '**')
        try:
            val = _safe_eval(expr)
            return (float(val), 'numeric')
        except Exception:
            pass

    return (txt, 'string')


def _match_mcq(question: str, options: dict, api_key: str = None):
    """Attempt to match MCQ options to the computed answer.

    Returns a dict with keys: 'answer' (label), 'value', 'explanation', 'confidence'.
    """
    # compute candidate answer from question
    answer_val = None
    answer_kind = None
    explanation = []

    # try to find an equation or expression in the question
    q = question.strip()
    if not q:
        return None

    # if question contains '=' and a variable, try solve
    if '=' in q and _HAS_SYMPY:
        try:
            left, right = q.split('=', 1)
            expr_l = sympify(left)
            expr_r = sympify(right)
            eq = Eq(expr_l, expr_r)
            vars = list(eq.free_symbols)
            if vars:
                sol = solve(eq, *vars)
                if sol:
                    answer_val = sol[0] if isinstance(sol, (list, tuple)) else sol
                    answer_kind = 'symbolic'
                    explanation.append(f"Solved equation: {eq} -> {sol}")
        except Exception:
            pass

    # if still none, try to find a math expression to evaluate
    if answer_val is None:
        # find candidate math-like substrings and pick the longest
        exprs = re.findall(r'[0-9\(\)\.\+\-\*/\^eE]+', q)
        exprs = sorted(exprs, key=len, reverse=True)
        if exprs:
            expr = exprs[0]
            expr = expr.replace('^', '**')
            if _HAS_SYMPY:
                try:
                    answer_val = sympify(expr)
                    answer_kind = 'symbolic'
                    explanation.append(f"Evaluated expression with sympy: {expr} -> {answer_val}")
                except Exception:
                    try:
                        v = _safe_eval(expr)
                        answer_val = float(v)
                        answer_kind = 'numeric'
                        explanation.append(f"Evaluated expression numerically: {expr} -> {answer_val}")
                    except Exception:
                        pass
            else:
                try:
                    v = _safe_eval(expr)
                    answer_val = float(v)
                    answer_kind = 'numeric'
                    explanation.append(f"Evaluated expression numerically: {expr} -> {answer_val}")
                except Exception:
                    pass

    # if still none and api_key is provided, try LLM to extract numeric answer
    if answer_val is None and api_key:
        try:
            from .llm_agent import LLMAgent
            llm = LLMAgent()
            resp = llm.handle(question, fallback_pref=None, api_key=api_key, use_web=False)
            if isinstance(resp, dict):
                resp_text = resp.get('text', '')
            else:
                resp_text = str(resp)
            # try to parse a numeric value from LLM reply
            m = re.search(r"([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)", resp_text)
            if m:
                try:
                    answer_val = float(m.group(1))
                    answer_kind = 'numeric'
                    explanation.append(f"LLM suggested numeric answer: {answer_val}")
                except Exception:
                    pass
        except Exception:
            pass

    # parse options into comparable values
    parsed = {}
    for lbl, opt in options.items():
        parsed[lbl] = _parse_option_value(opt)

    # try to match by numeric comparison first
    if answer_val is not None and answer_kind == 'numeric':
        for lbl, (val, kind) in parsed.items():
            if kind == 'numeric':
                try:
                    if abs(float(val) - float(answer_val)) < 1e-6:
                        return {'answer': lbl, 'value': answer_val, 'explanation': explanation or ['Numeric match'], 'confidence': 'high'}
                except Exception:
                    continue

    # try symbolic matching if sympy is available
    if answer_val is not None and answer_kind == 'symbolic' and _HAS_SYMPY:
        for lbl, (val, kind) in parsed.items():
            if kind == 'symbolic':
                try:
                    if (sympify(val) - sympify(answer_val)).simplify() == 0:
                        return {'answer': lbl, 'value': str(answer_val), 'explanation': explanation or ['Symbolic match'], 'confidence': 'high'}
                except Exception:
                    # try equality check
                    try:
                        if sympify(val).equals(sympify(answer_val)):
                            return {'answer': lbl, 'value': str(answer_val), 'explanation': explanation or ['Symbolic equals match'], 'confidence': 'high'}
                    except Exception:
                        continue

    # fallback: try string matching of rendered values
    if answer_val is not None:
        ans_str = str(answer_val).strip()
        for lbl, (val, kind) in parsed.items():
            try:
                if isinstance(val, (int, float)) and abs(float(val) - float(answer_val)) < 1e-6:
                    return {'answer': lbl, 'value': answer_val, 'explanation': explanation or ['Numeric fuzzy match'], 'confidence': 'medium'}
            except Exception:
                pass
            # string compare
            if str(val).strip().lower() == ans_str.lower():
                return {'answer': lbl, 'value': ans_str, 'explanation': explanation or ['String match'], 'confidence': 'medium'}

    # last resort: return top candidate by heuristic (e.g., shortest option if numeric?)
    # prefer numeric-like options
    numeric_opts = [lbl for lbl, (v, k) in parsed.items() if k == 'numeric']
    if len(numeric_opts) == 1:
        lbl = numeric_opts[0]
        return {'answer': lbl, 'value': parsed[lbl][0], 'explanation': ['Only numeric option, heuristically chosen'], 'confidence': 'low'}

    return None


class MathAgent:
    name = "Math Agent"

    def handle(self, query: str, fallback_pref: str = None, api_key: str = None, use_web: bool = False):
        q = query.strip()
        if not q:
            return "Please provide a math expression or a simple equation (e.g. '2+2' or '2*x+3=7')."

        # Check for derivative or integral requests
        if any(k in q.lower() for k in ["derivative", "derivative of", "diff", "d/dx"]):
            from .ap_stem_agent import APSTEMAgent
            return APSTEMAgent().handle(q)
        
        if any(k in q.lower() for k in ["integral", "integrate", "antiderivative"]):
            from .ap_stem_agent import APSTEMAgent
            return APSTEMAgent().handle(q)

        # quick heuristic: detect word problems (numbers + units) and provide a structured hint
        if re.search(r"\d+\s*(meters|m|feet|ft|kg|g|lbs|seconds|s|minutes|min|hours|h)", q):
            hint = (
                "This looks like a word problem with numeric quantities. Approach: 1) list symbols and units, 2) write equations, "
                "3) check units and solve. If you'd like, paste the numeric values exactly and I'll attempt to set up the equations."
            )
            # also compute cached numeric/symbolic if it looks like a direct compute
            cached = _compute_math_cached(q)
            # prefer the computed result if it seems meaningful, otherwise return hint
            if any(ch.isdigit() for ch in cached):
                return f"{hint}\n\nQuick compute:\n{cached}"
            return hint

        # If sympy is not available and the query contains alphabetic characters (variables),
        # offer to delegate to LLM if an API key is provided. Otherwise return helpful install message.
        if not _HAS_SYMPY and re.search(r"[a-zA-Z]", q):
            # Try a lightweight simple linear solver for common forms
            try_linear = _solve_simple_linear(q)
            if try_linear:
                return try_linear

            if api_key:
                try:
                    from .llm_agent import LLMAgent
                    llm = LLMAgent()
                    resp = llm.handle(query, fallback_pref=fallback_pref, api_key=api_key, use_web=use_web)
                    if isinstance(resp, dict):
                        return resp
                    return { 'text': resp }
                except Exception:
                    return "Sympy not available and expression contains symbolic variables. I attempted to use the LLM but it failed. Install sympy for full symbolic support (pip install sympy)."
            return "Sympy not available and expression contains symbolic variables. Install sympy for full support (pip install sympy) or provide a numeric expression."

        # Use cached computation for other expressions
        return _compute_math_cached(q)

