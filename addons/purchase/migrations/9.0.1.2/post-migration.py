from openupgradelib import openupgrade
from openerp import api, models, SUPERUSER_ID
from openerp.modules.registry import RegistryManager
from openerp import SUPERUSER_ID as uid

def migrate_purchase_invoice_lines(cr, registry):
    """Purchase Invoices."""
    a_invoice_line_obj = registry['account.invoice.line']

    cr.execute('SELECT order_line_id, invoice_id  FROM purchase_order_line_invoice_rel')

    for line_id, invoice_id in cr.fetchall():
        a_invoice_line_obj.write(cr, uid, [invoice_id], {'purchase_line_id': line_id})
        
@openupgrade.migrate()
def migrate(cr, version):
	registry = RegistryManager.get(cr.dbname)
	migrate_purchase_invoice_lines(cr, registry)
	
	cr.execute("UPDATE wkf_instance SET state='active' where state='deactive'")