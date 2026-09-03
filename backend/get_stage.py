import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres.rwrgjcujhmvdboggmctf:rAGHWANI301205@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres')
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT case_id, state_json FROM investigation_cases WHERE case_id IN ('CASE-MOCK--001', 'CASE-2025-00042')"))
        rows = res.fetchall()
        for row in rows:
            state = row[1]
            if isinstance(state, str):
                state = json.loads(state)
            print(f"{row[0]} current_stage in state_json: {state.get('current_stage')}")
                
    await engine.dispose()

asyncio.run(main())
