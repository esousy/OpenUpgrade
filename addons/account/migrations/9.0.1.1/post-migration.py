from openupgradelib import openupgrade
import logging
import json
from openerp import api, models, SUPERUSER_ID
from openerp.modules.registry import RegistryManager
from openerp import SUPERUSER_ID as uid

logger = logging.getLogger('OpenUpgrade.account')

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}

def migrate_account_type(cr, registry):
    logger.info('Starting migrate_account_type .....')
    """."""
    a_account_obj = registry['account.account']
    # account_ids = a_account_obj.search(cr, uid, [('user_type_id', '=', 2), ])
    # a_account_obj.write(cr, uid, account_ids, {'internal_type': 'receivable', 'reconcile': True})
    # account_ids = a_account_obj.search(cr, uid, [('user_type_id', '=', 3)])
    # a_account_obj.write(cr, uid, account_ids, {'internal_type': 'payable', 'reconcile': True})

    cr.execute(""" update account_account set internal_type='receivable', reconcile=True where user_type_id=2 """)
    cr.execute(""" update account_account set internal_type='payable', reconcile=True where user_type_id=3 """)

          
def migrate_payment_method(cr, registry):
    """."""
    logger.info('Starting migrate_payment_method .....')
    a_journal_obj = registry['account.journal']
    a_pay_meth_obj = registry['account.payment.method']
    inbound_payment_method_ids = a_pay_meth_obj.search(cr, uid, [('payment_type', '=', 'inbound')])
    outbound_payment_method_ids = a_pay_meth_obj.search(cr, uid, [('payment_type', '=', 'outbound')])
    journal_ids = a_journal_obj.search(cr, uid, [('type', 'in', ('bank','cash'))])
    a_journal_obj.write(cr, uid, journal_ids, 
                                   {    'inbound_payment_method_ids': [(6, 0, inbound_payment_method_ids)],
                                        'outbound_payment_method_ids': [(6, 0, outbound_payment_method_ids)]
                                        })
        
def migrate_move_invoice(cr, registry):
    """."""
    logger.info('Starting migrate_move_invoice .....')
    a_move_line_obj = registry['account.move.line']

    cr.execute('SELECT l.id, i.id ' \
                        'FROM account_move_line l, account_invoice i ' \
                        'WHERE l.move_id = i.move_id ')

    for line_id, invoice_id in cr.fetchall():
        a_move_line_obj.write(cr, uid, [line_id], {'invoice_id': invoice_id})

def migrate_payment(cr, registry):
    """Create a Push rule for each pair of locations linked. Will break if
    there are multiple warehouses for the same company."""
    logger.info('Starting migrate_payment .....')
    a_move_line_obj = registry['account.move.line']
    a_payment_obj = registry['account.payment']
    a_journal_obj = registry['account.journal']
    ir_sequence_obj = registry['ir.sequence']
        

    cr.execute(""" select v.id, v.journal_id, v.type, v.date, v.reference, v.amount, v.payment_rate_currency_id,
                        v.company_id, v.partner_id, v.move_id, v.is_multi_currency, v.state, v.number
                    from account_voucher v join account_journal j on(v.journal_id=j.id) 
                            where v.type in ('receipt','payment') and j.type in ('bank', 'cash') and v.amount != 0""" )
    voucher_ids = cr.fetchall()
    

    for voucher in voucher_ids:
        logger.info("Treating Voucher: %s ", voucher)
        # if float(voucher[5]) <= 0.0:
        #    continue
        journal = a_journal_obj.browse(cr, uid, voucher[1])
        
        payment_type = voucher[2] == 'receipt' and 'inbound' or 'outbound'
        partner_type = voucher[2] == 'receipt' and 'customer' or 'supplier'
        journal_payment_methods = payment_type == 'inbound' and journal.inbound_payment_method_ids or journal.outbound_payment_method_ids
        payment_method_id = journal_payment_methods[0].id
        # payment_method_id = payment_type == 'inbound' and 1 or 2
        if partner_type == 'customer':
            if payment_type == 'inbound':
                sequence = 'account.sequence_payment_customer_invoice'
            if payment_type == 'outbound':
                sequence = 'account.sequence_payment_customer_refund'
        if partner_type == 'supplier':
            if payment_type == 'inbound':
                sequence = 'account.sequence_payment_supplier_refund'
            if payment_type == 'outbound':
                sequence = 'account.sequence_payment_supplier_invoice'
                
        seq_id = registry['ir.model.data'].xmlid_to_res_id(cr, uid, sequence)
        payment_name = ir_sequence_obj.next_by_id(cr, uid, seq_id, context={'ir_sequence_date':voucher[3]})
        
        cr.execute(""" select id, move_line_id, type  from account_voucher_line 
                            where amount != 0 and voucher_id = %s """ % voucher[0])
        voucher_line_ids = cr.fetchall()
        
        cr.execute(""" SELECT distinct i.id FROM account_invoice i join account_move_line ml on (i.move_id = ml.move_id) 
                            WHERE ml.id in %s""", (tuple(x[1] for x in voucher_line_ids), ))
        
        invoice_ids = [x[0] for x in cr.fetchall()]
        
        vals = {
            'name': payment_name,
            'journal_id': journal.id,
            'payment_method_id': payment_method_id,
            'payment_date': voucher[3],
            'communication': 'Migration of payment N:  %s %s ' % (voucher[12], voucher[4]),
            'invoice_ids': [(6, 0, invoice_ids)],  # [(4, invoice_id, None)],
            'payment_type': payment_type,
            'amount': abs(voucher[5]),
            'currency_id': voucher[6],
            'partner_id': voucher[8],
            'partner_type': partner_type,
            'company_id': voucher[7],
            'state': voucher[11],
        }
        logger.info("Creating a payment: %s ", vals)
        a_payment_id = a_payment_obj.create(cr, uid, vals)
        
        if voucher[2] == 'receipt': 
            cr.execute(""" (select id, amount_currency from account_move_line 
                            where  move_id=%s and reconcile_ref is not null) 
                            union 
                            (select id, amount_currency from account_move_line 
                            where  move_id=%s and debit > 0  and reconcile_ref is null) """,
                                (voucher[9], voucher[9], ))
        else:
            cr.execute(""" (select id, amount_currency from account_move_line 
                            where  move_id=%s and reconcile_ref is not null) 
                            union 
                            (select id, amount_currency from account_move_line 
                            where  move_id=%s and credit > 0  and reconcile_ref is null) """,
                                (voucher[9], voucher[9], ))
                        
        if bool(voucher[10]):
            logger.info("Payment is_multi_currency true %s: %s ", a_payment_id, voucher[10])
            payment_move_lines = [x[0] for x in cr.fetchall() if (float(x[1]) != 0.0)]
        else:
            logger.info("Payment is_multi_currency false %s: %s ", a_payment_id, voucher[10])
            payment_move_lines = [x[0] for x in cr.fetchall()]
        logger.info("Payment Journal Items %s: %s ", a_payment_id, payment_move_lines)
        a_move_line_obj.write(cr, uid, payment_move_lines, {'payment_id': a_payment_id})
        
        

def migrate_reconciliation(cr, registry):
    """Create a Push rule for each pair of locations linked. Will break if
    there are multiple warehouses for the same company."""
    a_move_obj = registry['account.move']
    a_move_line_obj = registry['account.move.line']

    cr.execute(""" select id from account_move_reconcile """)
    
    reconcile_ids = [x[0] for x in cr.fetchall()]
    
    for reconcile_id in reconcile_ids:
        
        cr.execute(""" select id from account_move_line
                            where openupgrade_legacy_9_0_reconcile_id = %s or openupgrade_legacy_9_0_reconcile_partial_id = %s""", 
                            (reconcile_id, reconcile_id, ))
    
        
        
        reconcile_move_ids = [x[0] for x in cr.fetchall()]
        a_reconcile_lines = a_move_line_obj.browse(cr, uid, reconcile_move_ids)
        logger.info("a_reconcile_lines %s: %s ", reconcile_id, a_reconcile_lines.mapped('id'))
        result_reconcile_lines = a_reconcile_lines.auto_reconcile_lines()
        logger.info("result_reconcile_lines %s: %s ", reconcile_id, result_reconcile_lines.mapped('id'))
    
@openupgrade.migrate()
def migrate(cr, version):
    registry = RegistryManager.get(cr.dbname)
    migrate_account_type(cr, registry)
    migrate_move_invoice(cr, registry)
    migrate_payment_method(cr, registry)
    migrate_payment(cr, registry)
    migrate_reconciliation(cr, registry)
	
    cr.execute("UPDATE wkf_instance SET state='active' where state='deactive'")
    