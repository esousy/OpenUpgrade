from openupgradelib import openupgrade

@openupgrade.migrate()
def migrate(cr, version):
    # sales_team.view_sale_config_settings, crm.view_partners_form_crm_calls
    cr.execute(
        "delete from ir_ui_view v "
        "using ir_model_data d where "
        "v.id=d.res_id and d.model='ir.ui.view' and "
        "d.name='view_partners_form_crm_calls'")
    cr.execute(
        "delete from ir_ui_view v "
        "where v.name='crm settings'")
    
    openupgrade.rename_models(
        cr, [
            ('crm.case.stage', 'crm.stage'),
            ])
    #openupgrade.rename_columns(
    #    cr, column_renames)
    openupgrade.rename_tables(
        cr, [('crm_case_stage', 'crm_stage'),])
    #for constraint in [
    #        'crm_lead_stage_id_fkey', 'crm_lead_team_id_fkey']:
    #    cr.execute(
    #        "ALTER TABLE crm_lead DROP CONSTRAINT IF EXISTS {}".format(
    #            constraint))