import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

async def fetch():
    engine = create_async_engine("postgresql+asyncpg://postgres.rwrgjcujhmvdboggmctf:rAGHWANI301205@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
    
    last_state = ""
    for _ in range(60):
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT state_json->>'current_stage' as current_stage, state_json->'errors' as errors, state_json->'context_intelligence'->>'status' as ctx_status, state_json->'investigation_reasoning'->>'status' as reason_status, state_json->'evidence_compliance_validation'->>'status' as comp_status, state_json->'decision_optimization'->>'status' as dec_status, state_json->'investigation_report'->>'status' as rep_status FROM investigation_cases WHERE case_id = 'CASE-MOCK--001'"))
            row = res.fetchone()
            if row:
                current = json.dumps(dict(row._mapping))
                if current != last_state:
                    print(json.dumps(dict(row._mapping), indent=2), flush=True)
                    last_state = current
                    
                if dict(row._mapping).get("current_stage") == "DONE":
                    print("Completed!")
                    return
        time.sleep(5)
    print("Timeout")

asyncio.run(fetch())
