from openupgradelib import openupgrade

column_renames = {
    'account_account': [
        ('active', None),
        ('currency_mode', None),
        ('parent_id', None),
        ('parent_left', None),
        ('parent_right', None),
        ('shortcut', None),
        ('type', None)
    ],
    'account_account_template': [
        ('parent_id', None),
        ('shortcut', None),
        ('type', None),
    ],
    'account_account_type': [
        ('close_method', None),
        ('code', None),
    ],
    'account_analytic_line': [
        ('journal_id', None),
    ],
    'account_bank_statement': [
        ('closing_date', None),
        ('period_id', None),
    ],
    'account_bank_statement_line': [
        ('journal_entry_id', None),
    ],
    'account_cashbox_line': [
        ('bank_statement_id', None),
        ('number_closing', None),
        ('number_opening', None),
        ('pieces', None),
    ],
    'account_chart_template': [
        ('account_root_id', None),
        ('bank_account_view_id', None),
        ('property_account_expense_opening', None),
        ('property_account_income_opening', None),
        ('tax_code_root_id', None),
    ],
    'account_invoice': [
        ('check_total', None),
        ('internal_number', None),
        ('period_id', None),
        ('supplier_invoice_number', None),
    ],
    'account_invoice_tax': [
        ('base', None),
        ('base_amount', None),
        ('base_code_id', None),
        ('tax_amount', None),
        ('tax_code_id', None),
    ],
    'account_journal': [
        ('allow_date', None),
        ('analytic_journal_id', None),
        ('cash_control', None),
        ('centralisation', None),
        ('entry_posted', None),
        ('internal_account_id', None),
        ('user_id', None),
        ('with_last_closing_balance', None),
    ],
    'account_move': [
        ('balance', None),
        ('line_id', None),
        ('period_id', None),
        ('to_check', None),
    ],
    'account_move_line': [
        ('account_tax_id', None),
        ('centralisation', None),
        ('date_created', None),
        ('reconcile_id', None),
        ('reconcile_partial_id', None),
        ('state', None),
        ('tax_amount', None),
        ('tax_code_id', None),
    ],
    'account_tax': [
        ('account_analytic_collected_id', None),
        ('account_analytic_paid_id', None),
        ('applicable_type', None),
        ('base_code_id', None),
        ('base_sign', None),
        ('child_depend', None),
        ('domain', None),
        ('parent_id', None),
        ('python_compute_inv', None),
        ('ref_base_code_id', None),
        ('ref_base_sign', None),
        ('ref_tax_code_id', None),
        ('ref_tax_sign', None),
        ('tax_code_id', None),
        ('tax_sign', None),
    ],
    'account_tax_template': [
        ('applicable_type', None),
        ('base_code_id', None),
        ('base_sign', None),
        ('child_depend', None),
        ('domain', None),
        ('parent_id', None),
        ('python_compute_inv', None),
        ('ref_base_code_id', None),
        ('ref_base_sign', None),
        ('ref_tax_code_id', None),
        ('ref_tax_sign', None),
        ('tax_code_id', None),
        ('tax_sign', None),
        ('type', None),
    ],
    'res_partner': [
        ('vat_subjected', None),
    ],
}

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
