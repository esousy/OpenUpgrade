from openupgradelib import openupgrade

column_renames = {
    'crm_case_section': [
        ('parent_id', None),
        ],
    }
	
@openupgrade.migrate()
def migrate(cr, version):
    openupgrade.rename_models(
        cr, [
			('crm.case.section', 'crm.team')
            ])
    openupgrade.rename_columns(
        cr, column_renames)
    openupgrade.rename_tables(
        cr, [('crm_case_section', 'crm_team'),])