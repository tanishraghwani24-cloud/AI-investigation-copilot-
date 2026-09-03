import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres.rwrgjcujhmvdboggmctf:rAGHWANI301205@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres')
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT state_json FROM investigation_cases WHERE case_id = 'CASE-MOCK--001'"))
        row = res.fetchone()
        state = row[0]
        if isinstance(state, str):
            state = json.loads(state)
        context = state.get('context_intelligence')
        print("Context Intelligence:")
        if context:
            print(json.dumps(context, indent=2))
        else:
            print("None")
                
    await engine.dispose()

asyncio.run(main())
