import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres.rwrgjcujhmvdboggmctf:rAGHWANI301205@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres')
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT case_id, state_json FROM investigation_cases ORDER BY created_at DESC LIMIT 1"))
        row = res.fetchone()
        if not row:
            print('No mock cases found')
            return
        
        case_id, state_json = row
        state = state_json if isinstance(state_json, dict) else json.loads(state_json)
        
        print(f'CASE ID: {case_id}')
        print(f'CURRENT STAGE: {state.get("current_stage")}')
        print('--- ERRORS ---')
        print(json.dumps(state.get('errors', []), indent=2))
        
        print('--- CONTEXT INTELLIGENCE ---')
        ctx = state.get('context_intelligence')
        print(json.dumps(ctx, indent=2)[:500] if ctx else "None")
        
        print('--- REASONING ---')
        reasoning = state.get('investigation_reasoning')
        print(f'Status: {reasoning.get("status") if reasoning else None}')
        
        print('--- COMPLIANCE ---')
        compliance = state.get('evidence_compliance_validation')
        print(f'Status: {compliance.get("status") if compliance else None}')
        
        print('--- DECISION ---')
        decision = state.get('decision_optimization')
        print(f'Status: {decision.get("status") if decision else None}')
        
        print('--- REPORTING ---')
        report = state.get('investigation_report')
        print(f'Status: {report.get("status") if report else None}')

asyncio.run(main())
