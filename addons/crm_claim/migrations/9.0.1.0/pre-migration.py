from openupgradelib import openupgrade

@openupgrade.migrate()
def migrate(cr, version):
    openupgrade.rename_models(
        cr, [
            ('crm.case.categ', 'crm.claim.category'),
            ])
    #openupgrade.rename_columns(
    #    cr, column_renames)
    openupgrade.rename_tables(
        cr, [('crm_case_categ', 'crm_claim_category'),])
    for constraint in [
            'crm_claim_categ_id_fkey']:
        cr.execute(
            "ALTER TABLE crm_lead DROP CONSTRAINT IF EXISTS {}".format(
                constraint))