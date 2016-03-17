from openupgradelib import openupgrade

	
@openupgrade.migrate()
def migrate(cr, version):
    cr.execute("UPDATE wkf_instance SET state='active' where state='deactive'")