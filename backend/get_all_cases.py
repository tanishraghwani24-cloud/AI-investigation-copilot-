import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres.rwrgjcujhmvdboggmctf:rAGHWANI301205@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres')
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT case_id, created_at, status, state_json FROM investigation_cases ORDER BY created_at DESC"))
        rows = res.fetchall()
        for row in rows:
            case_id = row[0]
            created_at = row[1]
            status = row[2]
            state = row[3]
            if isinstance(state, str):
                state = json.loads(state)
            errors = state.get('errors', [])
            print(f"{case_id} | {created_at} | Status: {status} | Errors: {len(errors)}")
            if errors:
                print(json.dumps(errors, indent=2))
                
    await engine.dispose()

asyncio.run(main())
