from openupgradelib import openupgrade
import logging

logger = logging.getLogger('OpenUpgrade.account')

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

def convert_field(cr, model, field, target_model, target_field):
	logger.info("convert_field: %s-%s to  %s-%s", model, field, target_model, target_field)
	cr.execute("UPDATE ir_model_fields set name=%s, model=%s WHERE model=%s AND name=%s", (target_field, target_model, model, field))

@openupgrade.migrate()
def migrate(cr, version):
    openupgrade.rename_columns(cr, column_renames)
    #openupgrade.rename_xmlids(cr, xmlid_renames)
    
    convert_field(cr, 'res.partner', 'property_account_payable', 'res.partner', 'property_account_payable_id')
    convert_field(cr, 'res.partner', 'property_account_receivable', 'res.partner', 'property_account_receivable_id')
    convert_field(cr, 'res.partner', 'property_account_position', 'res.partner', 'property_account_position_id')
    convert_field(cr, 'res.partner', 'property_payment_term', 'res.partner', 'property_payment_term_id')
    convert_field(cr, 'res.partner', 'property_supplier_payment_term', 'res.partner', 'property_supplier_payment_term_id')
    convert_field(cr, 'account.chart.template', 'property_account_expense', 'account.chart.template', 'property_account_expense_id')
    convert_field(cr, 'account.chart.template', 'property_account_expense_categ', 'account.chart.template', 'property_account_expense_categ_id')
    convert_field(cr, 'account.chart.template', 'property_account_income', 'account.chart.template', 'property_account_income_id')
    convert_field(cr, 'account.chart.template', 'property_account_income_categ', 'account.chart.template', 'property_account_income_categ_id')
    convert_field(cr, 'account.chart.template', 'property_account_payable', 'account.chart.template', 'property_account_payable_id')
    convert_field(cr, 'account.chart.template', 'property_account_receivable', 'account.chart.template', 'property_account_receivable_id')
    convert_field(cr, 'product.category', 'property_account_expense_categ', 'product.category', 'property_account_expense_categ_id')
    convert_field(cr, 'product.category', 'property_account_income_categ', 'product.category', 'property_account_income_categ_id')
    convert_field(cr, 'product.category', 'property_account_expense', 'product.category', 'property_account_expense_id')
    convert_field(cr, 'product.category', 'property_account_income', 'product.category', 'property_account_income_id')
    
    cr.execute("UPDATE wkf_instance SET state='deactive' where state='active'")
    #'partner.view.button.journal_item_count'
    
    # delete a view from obsolete module partner_view_button_journal_item_count that causes
    # migration of the account module not to happen cleanly
    cr.execute(
        "delete from ir_ui_view v "
        "using ir_model_data d where "
        "v.id=d.res_id and d.model='ir.ui.view' and "
        "d.name='partner_view_button_journal_item_count'")
