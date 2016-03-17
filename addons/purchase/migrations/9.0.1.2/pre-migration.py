from openupgradelib import openupgrade

@openupgrade.migrate()
def migrate(cr, version):
    cr.execute("UPDATE wkf_instance SET state='deactive' where state='active'")
    #cr.execute("delete from ir_ui_view where id in (713)")
    