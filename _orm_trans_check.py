# -*- coding: utf-8 -*-
# shell-file to query translations via ORM
translations = env["ir.translation"].search([("src", "=", "Factory Employee")])
print('found', len(translations))
for t in translations:
    print(t.lang, t.src, t.value, t.module, t.name)
