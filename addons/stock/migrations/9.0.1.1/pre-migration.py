from openupgradelib import openupgrade
	
@openupgrade.migrate()
def migrate(cr, version):

    cr.execute(
        "delete from ir_ui_view  where "
        "inherit_id in (select v.id from ir_ui_view v , ir_model_data d "
        "where v.id=d.res_id and d.model='ir.ui.view' and "
		"d.name='view_partner_property_form' and d.module='stock')")

    cr.execute(
        "delete from ir_ui_view v "
        "using ir_model_data d where "
        "v.id=d.res_id and d.model='ir.ui.view' and "
        "d.name='view_partner_property_form' and d.module='stock'")
