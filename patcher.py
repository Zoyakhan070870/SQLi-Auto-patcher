import re

def auto_patch(code):
    """
    Detects simple SQL injection vulnerabilities and replaces them
    with parameterized queries using ? placeholders.
    """

    query_vars = {}

    # Pattern to match simple queries like: query = "SELECT ... WHERE x = " + var
    pattern_assign = re.compile(
        r'(\w+)\s*=\s*([\'"])(.*?WHERE\s+.*?=)\s*["\']?\s*\+\s*(\w+)\s*["\']?',
        re.IGNORECASE
    )

    def replace_assignment(match):
        var_name, quote, query_part, user_input = match.groups()
        if query_part.strip().endswith("'") or query_part.strip().endswith('"'):
            query_part = query_part.strip()[:-1]
        query_vars[var_name] = [user_input]  # store as list for future flexibility
        safe_query = f'{quote}{query_part.strip()} ?{quote}'
        return f'{var_name} = {safe_query}'

    code = pattern_assign.sub(replace_assignment, code)

    # Update cursor.execute(query) → cursor.execute(query, (var,))
    pattern_execute = re.compile(r'cursor\.execute\s*\(\s*(\w+)\s*\)')

    def replace_execute(match):
        var_name = match.group(1)
        if var_name in query_vars:
            args = ", ".join(query_vars[var_name])
            return f'cursor.execute({var_name}, ({args},))'
        return match.group(0)

    code = pattern_execute.sub(replace_execute, code)

    # Additional regex patterns for more complex injection vulnerabilities
    # Handling 'OR 1=1', 'UNION SELECT', etc.
    additional_patterns = [
        r'(\b(select|insert|update|delete|drop|union|alter)\b.*?(\bfrom|where|group|having|limit)\b)',
        r"('(\s*|\s*--\s*|\s*#\s*)')",
        r"(--|\#|\;|\/\*)"
    ]

    for pattern in additional_patterns:
        code = re.sub(pattern, '', code)  # You can modify this to sanitize or escape further if needed

    return code
