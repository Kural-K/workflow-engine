import re, operator

def _resolve(token, data):
    token = token.strip()
    if token in data:
        return data[token]
    if (token.startswith("'") and token.endswith("'")) or (token.startswith('"') and token.endswith('"')):
        return token[1:-1]
    try: return int(token)
    except ValueError: pass
    try: return float(token)
    except ValueError: pass
    if token.lower() == 'true': return True
    if token.lower() == 'false': return False
    return token

OPS = {'==': operator.eq, '!=': operator.ne, '<=': operator.le, '>=': operator.ge, '<': operator.lt, '>': operator.gt}

def _eval_string_fn(expr, data):
    pattern = r'(contains|startsWith|endsWith)\(\s*(\w+)\s*,\s*(["\'])(.*?)\3\s*\)'
    m = re.match(pattern, expr.strip())
    if not m:
        raise ValueError("Invalid string function: " + expr)
    fn = m.group(1)
    field = m.group(2)
    val = m.group(4)
    fv = str(data.get(field, ''))
    if fn == 'contains': return val in fv
    if fn == 'startsWith': return fv.startswith(val)
    if fn == 'endsWith': return fv.endswith(val)
    return False

def _eval_comparison(expr, data):
    expr = expr.strip()
    if re.match(r'(contains|startsWith|endsWith)\(', expr):
        return _eval_string_fn(expr, data)
    for op_str in ('==', '!=', '<=', '>=', '<', '>'):
        parts = expr.split(op_str, 1)
        if len(parts) == 2:
            left = _resolve(parts[0].strip(), data)
            right = _resolve(parts[1].strip(), data)
            try: left, right = float(left), float(right)
            except (TypeError, ValueError): left, right = str(left), str(right)
            return OPS[op_str](left, right)
    raise ValueError("Cannot parse: " + expr)

def _split_logical(expr, delimiter):
    depth, parts, current, i = 0, [], [], 0
    d_len = len(delimiter)
    while i < len(expr):
        if expr[i] == '(':
            depth += 1
            current.append(expr[i])
        elif expr[i] == ')':
            depth -= 1
            current.append(expr[i])
        elif depth == 0 and expr[i:i+d_len] == delimiter:
            parts.append(''.join(current).strip())
            current = []
            i += d_len
            continue
        else:
            current.append(expr[i])
        i += 1
    parts.append(''.join(current).strip())
    return parts

def _eval_expr(expr, data):
    expr = expr.strip()
    if expr.startswith('(') and expr.endswith(')'):
        return _eval_expr(expr[1:-1], data)
    or_parts = _split_logical(expr, '||')
    if len(or_parts) > 1:
        return any(_eval_expr(p, data) for p in or_parts)
    and_parts = _split_logical(expr, '&&')
    if len(and_parts) > 1:
        return all(_eval_expr(p, data) for p in and_parts)
    return _eval_comparison(expr, data)

def evaluate_condition(condition, data):
    if condition.strip().upper() == 'DEFAULT':
        return True
    return _eval_expr(condition, data)

def evaluate_rules(rules, data):
    evaluated = []
    for rule in sorted(rules, key=lambda r: r.priority):
        try:
            result = evaluate_condition(rule.condition, data)
        except Exception as e:
            evaluated.append({"rule": rule.condition, "result": False, "error": str(e)})
            continue
        evaluated.append({"rule": rule.condition, "result": result})
        if result:
            return {
                "matched_rule_id": str(rule.id),
                "condition": rule.condition,
                "next_step_id": rule.next_step_id,
                "evaluated": evaluated
            }
    return {"matched_rule_id": None, "condition": None, "next_step_id": None, "evaluated": evaluated}
