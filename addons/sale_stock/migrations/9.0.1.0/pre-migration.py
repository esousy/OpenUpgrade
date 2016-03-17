from openupgradelib import openupgrade
	
@openupgrade.migrate()
def migrate(cr, version):
    cr.execute(
        "delete from ir_ui_view  where "
        "inherit_id in (select v.id from ir_ui_view v , ir_model_data d "
        "where v.id=d.res_id and d.model='ir.ui.view' and "
		"d.name='view_order_form_inherit' and d.module='sale_stock')")

    cr.execute(
        "delete from ir_ui_view v "
        "using ir_model_data d where "
        "v.id=d.res_id and d.model='ir.ui.view' and "
        "d.name in ('view_sales_config_sale_stock', 'view_order_form_inherit') "
        "and d.module='sale_stock'")
    