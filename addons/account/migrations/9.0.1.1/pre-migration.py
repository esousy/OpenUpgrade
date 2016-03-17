from openupgradelib import openupgrade

	
@openupgrade.migrate()
def migrate(cr, version):
    cr.execute("UPDATE wkf_instance SET state='deactive' where state='active'")
    #'partner.view.button.journal_item_count'
    
    # delete a view from obsolete module partner_view_button_journal_item_count that causes
    # migration of the account module not to happen cleanly
    cr.execute(
        "delete from ir_ui_view v "
        "using ir_model_data d where "
        "v.id=d.res_id and d.model='ir.ui.view' and "
        "d.name='partner_view_button_journal_item_count'")
