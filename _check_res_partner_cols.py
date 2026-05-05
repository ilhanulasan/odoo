import sys
env.cr.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'res_partner'
      AND column_name IN ('route_id', 'annual_fee', 'currency_id')
""")
print("columns:", env.cr.fetchall())
m = env["ir.module.module"].search([("name", "=", "contacts_portal_type")], limit=1)
if m:
    print("contacts_portal_type state:", m.state)
else:
    print("contacts_portal_type: not found in ir.module.module")
m2 = env["ir.module.module"].search([("name", "=", "shuttle_management")], limit=1)
if m2:
    print("shuttle_management state:", m2.state)
else:
    print("shuttle_management: not found")
