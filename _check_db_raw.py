import odoo
from odoo.tools import config

config.parse_config(["-c", "odoo.conf", "-d", "v21", "--no-http"])

cr = odoo.sql_db.db_connect("v21").cursor()
try:
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'res_partner'
          AND column_name IN ('route_id', 'annual_fee', 'currency_id')
        ORDER BY column_name
    """)
    print("columns:", cr.fetchall())

    cr.execute("""
        SELECT name, state
        FROM ir_module_module
        WHERE name IN ('contacts_portal_type', 'shuttle_management')
        ORDER BY name
    """)
    print("modules:", cr.fetchall())
finally:
    cr.close()
