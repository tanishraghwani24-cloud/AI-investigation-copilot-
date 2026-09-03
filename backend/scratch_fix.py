import glob

for filepath in glob.glob('app/agents/tests/test_context_agent_*.py'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('await context_agent(state)["context_intelligence"]', '(await context_agent(state))["context_intelligence"]')
    content = content.replace('await context_agent(state_a)["context_intelligence"]', '(await context_agent(state_a))["context_intelligence"]')
    content = content.replace('await context_agent(state_b)["context_intelligence"]', '(await context_agent(state_b))["context_intelligence"]')
    content = content.replace('await context_agent(state_no_docs)["context_intelligence"]', '(await context_agent(state_no_docs))["context_intelligence"]')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
print('Fixed coroutine indexing in context_agent tests.')
