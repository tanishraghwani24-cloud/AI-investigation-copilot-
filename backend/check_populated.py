import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres.rwrgjcujhmvdboggmctf:rAGHWANI301205@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres')
    async with engine.begin() as conn:
        for case in ['CASE-MOCK--001', 'CASE-2025-00042']:
            res = await conn.execute(text(f"SELECT state_json FROM investigation_cases WHERE case_id = '{case}'"))
            row = res.fetchone()
            if not row: continue
            state = row[0]
            if isinstance(state, str):
                state = json.loads(state)
            
            print(f"--- {case} ---")
            for field in ['context_intelligence', 'investigation_reasoning', 'evidence_compliance_validation', 'decision_optimization']:
                obj = state.get(field)
                if obj is None:
                    print(f"{field}: None")
                else:
                    print(f"{field}: status={obj.get('status')}")
                
    await engine.dispose()

asyncio.run(main())
