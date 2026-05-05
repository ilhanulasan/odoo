import odoo
from odoo.tools import config
config.parse_config(["-c","odoo.conf","-d","v21","--no-http"]) 
cr = odoo.sql_db.db_connect("v21").cursor()
try:
    cr.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema='public' AND table_name ILIKE '%translation%'
        ORDER BY table_name
    """)
    print(cr.fetchall())
finally:
    cr.close()
