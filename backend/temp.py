import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres.rwrgjcujhmvdboggmctf:rAGHWANI301205@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres')
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT case_id, state_json FROM investigation_cases WHERE case_id LIKE 'CASE-MOCK-%' ORDER BY created_at DESC LIMIT 5"))
        rows = res.fetchall()
        import json
        for row in rows:
            case_id, state_json = row
            state = state_json if isinstance(state_json, dict) else json.loads(state_json)
            c = state.get("context_intelligence", {})
            print(f"{case_id} Context JSON: {json.dumps(c, indent=2)}")
        print('Newest cases:', [r[0] for r in rows])

asyncio.run(main())
