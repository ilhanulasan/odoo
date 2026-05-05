import odoo
from odoo.tools import config
config.parse_config(["-c","odoo.conf","-d","v21","--no-http"]) 
cr = odoo.sql_db.db_connect("v21").cursor()
try:
    cr.execute("""
        SELECT lang, src, value, module, name
        FROM ir_translation
        WHERE src = 'Factory Employee' OR src ILIKE '%Factory Employee%' OR value ILIKE '%Fabrika%'
        ORDER BY lang, module
    """)
    rows = cr.fetchall()
    print('translations found:', len(rows))
    for r in rows:
        print(r)
finally:
    cr.close()
