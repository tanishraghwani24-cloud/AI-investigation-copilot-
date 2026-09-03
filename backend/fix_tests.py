import os
import re

def fix_file(f):
    try:
        with open(f, 'r', encoding='utf-8') as file:
            c = file.read()
    except Exception as e:
        print(f"Error reading {f}: {e}")
        return
        
    changed = False
    
    # 1. Clean up messy nesting of `__import__("asyncio").run(` completely
    # First, let's just strip all `__import__("asyncio").run(` and the matching closing parens
    # This is slightly tricky, so let's just use regex for the known patterns
    while '__import__("asyncio").run(__import__("asyncio").run(' in c:
        c = c.replace('__import__("asyncio").run(__import__("asyncio").run(', '__import__("asyncio").run(')
        c = c.replace('))))', ')))')
        changed = True
        
    # Also fix the specific `result = __import__("asyncio").run(run_investigation(state)))` syntax error
    if 'run_investigation(state)))' in c:
        c = c.replace('run_investigation(state)))', 'run_investigation(state))')
        changed = True

    # 2. Add `__import__("asyncio").run(` to unawaited context_agent and run_investigation calls
    def wrap_with_asyncio(func_name, code):
        pattern = r'(?<!__import__\("asyncio"\)\.run\()(' + func_name + r'\([^)]+\))'
        new_code = re.sub(pattern, r'__import__("asyncio").run(\1)', code)
        return new_code

    new_c = wrap_with_asyncio('context_agent', c)
    new_c = wrap_with_asyncio('run_investigation', new_c)
    if new_c != c:
        c = new_c
        changed = True
        
    if changed:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(c)

for root, _, files in os.walk('app/agents/tests'):
    for n in files:
        if n.endswith('.py'):
            fix_file(os.path.join(root, n))

for root, _, files in os.walk('app/graph/tests'):
    for n in files:
        if n.endswith('.py'):
            fix_file(os.path.join(root, n))
