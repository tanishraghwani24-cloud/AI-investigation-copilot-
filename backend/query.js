const { Pool } = require('pg');
const pool = new Pool({ connectionString: 'postgresql://postgres.rwrgjcujhmvdboggmctf:rAGHWANI301205@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres' });
const query = `
SELECT 
  current_stage, 
  errors, 
  state_json->'context_intelligence'->>'status' as ctx_status, 
  state_json->'investigation_reasoning'->>'status' as reason_status, 
  state_json->'evidence_compliance_validation'->>'status' as comp_status, 
  state_json->'decision_optimization'->>'status' as dec_status, 
  state_json->'investigation_report'->>'status' as rep_status 
FROM investigation_cases 
WHERE case_id = 'CASE-MOCK--001'
`;
pool.query(query).then(res => console.log(JSON.stringify(res.rows[0], null, 2))).catch(console.error).finally(() => pool.end());
