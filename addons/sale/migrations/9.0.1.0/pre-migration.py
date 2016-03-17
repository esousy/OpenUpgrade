from openupgradelib import openupgrade

column_renames = {
    'sale_order_line_invoice_rel': [
        ('invoice_id', 'invoice_line_id'),
        ],
    }
	
@openupgrade.migrate()
def migrate(cr, version):
    cr.execute("UPDATE wkf_instance SET state='deactive' where state='active'")

    cr.execute(
        "delete from ir_ui_view v "
        "using ir_model_data d where "
        "v.id=d.res_id and d.model='ir.ui.view' and "
        "d.name='res_partner_address_type' and d.module='sale'")

    openupgrade.rename_columns(
        cr, column_renames)
    