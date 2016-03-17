from openupgradelib import openupgrade

@openupgrade.migrate()
def migrate(cr, version):
    # purchase.view_product_normal_purchase_buttons_from,
    cr.execute(
        "delete from ir_ui_view v "
        "using ir_model_data d where "
        "v.id=d.res_id and d.model='ir.ui.view' and "
        "d.name='view_product_normal_purchase_buttons_from'")