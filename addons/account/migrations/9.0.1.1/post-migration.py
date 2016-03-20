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

    cr.execute(""" update account_account set type='receivable' where user_type_id=2 """)
    cr.execute(""" update account_account set type='payable' where user_type_id=3 """)

          
def migrate_payment_method(cr, registry):
    """."""
    logger.info('Starting migrate_payment_method .....')
    a_journal_obj = registry['account.journal']
    #a_pay_meth_obj = registry['account.payment.method']
    #inbound_payment_method_ids = a_pay_meth_obj.search(cr, uid, [('payment_type', '=', 'inbound')])
    #outbound_payment_method_ids = a_pay_meth_obj.search(cr, uid, [('payment_type', '=', 'outbound')])
    journal_ids = a_journal_obj.search(cr, uid, [('type', 'in', ('bank','cash'))])
    #journals = a_journal_obj.browse(cr, uid, journal_ids)
    for journal_id in journal_ids:
        #ins = list(set(inbound_payment_method_ids) - set(journal_id.inbound_payment_method_ids.mapped('id')))
        #outs = list(set(outbound_payment_method_ids) - set(journal_id.outbound_payment_method_ids.mapped('id')))
        # logger.info('Journal: %s', journal_id)
        a_journal_obj.write(cr, uid, [journal_id], {'inbound_payment_method_ids': (4, 1, None),
                                                'outbound_payment_method_ids': (4, 2, None)})
        a_journal_obj.write(cr, uid, [journal_id], {'inbound_payment_method_ids': (4, 3, None),
                                                'outbound_payment_method_ids': (4, 4, None)})
        
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
                        v.company_id, v.partner_id, v.move_id from account_voucher v join account_journal j on(v.journal_id=j.id) 
                            where v.type in ('receipt','payment') and j.type in ('bank', 'cash') and v.amount > 0""" )
    voucher_ids = cr.fetchall()
    

    for voucher in voucher_ids:
        logger.info("Treating Voucher: %s ", voucher)
        # if float(voucher[5]) <= 0.0:
        #    continue
        journal = a_journal_obj.browse(cr, uid, voucher[1])
        
        payment_type = voucher[2] == 'receipt' and 'inbound' or 'outbound'
        partner_type = voucher[2] == 'receipt' and 'customer' or 'supplier'
        #journal_payment_methods = payment_type == 'inbound' and journal.inbound_payment_method_ids or journal.outbound_payment_method_ids
        #payment_method_id = journal_payment_methods[0].id
        payment_method_id = payment_type == 'inbound' and 1 or 2
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
        #sequence_id = ir_sequence_obj.browse(cr, uid, seq_id)
        #context['fiscalyear_id'] = period.fiscalyear_id.id
        #journal = self.pool.get('account.journal').browse(cr, uid, journal_id, None)
        #return obj_seq.next_by_id(cr, uid, journal.sequence_id.id, context=context)

        
        # context['ir_sequence_date'] = voucher[3]    
        payment_name = ir_sequence_obj.next_by_id(cr, uid, seq_id, context={'ir_sequence_date':voucher[3]})
        
        cr.execute(""" select id, move_line_id, type  from account_voucher_line where voucher_id = %s """ % voucher[0])
        voucher_line_ids = cr.fetchall()
        
        cr.execute(""" SELECT i.id FROM account_invoice i join account_move_line ml on (i.move_id = ml.move_id) 
                            WHERE ml.id in %s""", (tuple(x[1] for x in voucher_line_ids), ))
        
        invoice_ids = [x[0] for x in cr.fetchall()]
        
        vals = {
            'name': payment_name,
            'journal_id': journal.id,
            'payment_method_id': payment_method_id,
            'payment_date': voucher[3],
            'communication': voucher[4],
            'invoice_ids': (6, None, invoice_ids),  # [(4, invoice_id, None)],
            'payment_type': payment_type,
            'amount': voucher[5],
            'currency_id': voucher[6],
            'partner_id': voucher[8],
            'partner_type': partner_type,
            'company_id': voucher[7],
        }
        logger.info("Creating a payment: %s ", vals)
        a_payment_id = a_payment_obj.create(cr, uid, vals)
        
        if voucher[2] == 'receipt': 
            cr.execute(""" (select id from account_move_line 
                            where  move_id=%s and reconcile_ref is not null) 
                            union 
                            (select id from account_move_line 
                            where  move_id=%s and debit > 0  and reconcile_ref is null) """,
                                (voucher[9], voucher[9], ))
        else:
            cr.execute(""" (select id from account_move_line 
                            where  move_id=%s and reconcile_ref is not null) 
                            union 
                            (select id from account_move_line 
                            where  move_id=%s and credit > 0  and reconcile_ref is null) """,
                                (voucher[9], voucher[9], ))
                        
        payment_move_lines = [x[0] for x in cr.fetchall()]
        logger.info("Payment Journal Items %s: %s ", a_payment_id, payment_move_lines)
        a_move_line_obj.write(cr, uid, payment_move_lines, {'payment_id': a_payment_id})
        
        cr.execute(""" select distinct reconcile_ref from account_move_line
                                            where move_id = %s and reconcile_ref is not null""", 
                                            (voucher[9], ))
        reconcile_refs = [x[0] for x in cr.fetchall()]
        
        for reconcile_ref in reconcile_refs:
            cr.execute(""" select id from account_move_line 
                            where  reconcile_ref = %s """, (reconcile_ref, ))
            reconcile_move_ids = [x[0] for x in cr.fetchall()]
            a_reconcile_lines = a_move_line_obj.browse(cr, uid, reconcile_move_ids)
            result_reconcile_lines = a_reconcile_lines.auto_reconcile_lines()
            logger.info("result_reconcile_lines %s: %s ", reconcile_ref, result_reconcile_lines.mapped('id'))
        
        

def migrate_payment_invoice(cr, registry):
    """Create a Push rule for each pair of locations linked. Will break if
    there are multiple warehouses for the same company."""
    a_move_obj = registry['account.move']
    a_move_line_obj = registry['account.move.line']
    a_payment_obj = registry['account.payment']
    a_invoice_obj = registry['account.invoice']
    a_journal_obj = registry['account.journal']
    a_pay_meth_obj = registry['account.payment.method']

    cr.execute('SELECT i.id, i.move_id FROM account_invoice i')
    a_lines = cr.fetchall()
    

    for invoice_id, move_id in a_lines:
        invoice = a_invoice_obj.browse(cr, uid, invoice_id)
        move = a_move_obj.browse(cr, uid, move_id)
        partial_lines = lines = []
        
        for line in move.line_ids:
            if line.account_id != invoice.account_id:
                continue
            #move_line = a_move_line_obj.browse(cr, uid, line)
            cr.execute(""" select l.id, journal_id, j.type, reconcile_id from account_move_line l, 
                            account_journal j  where l.journal_id=j.id and  l.reconcile_id in (select reconcile_id 
                        FROM account_move_line al, account_invoice i  
                        WHERE al.move_id = i.move_id and al.id=%s)  and j.type in ('bank', 'cash')""" % line.id)
            lines = lines + cr.fetchall()
            cr.execute(""" select l.id, journal_id, j.type, reconcile_partial_id from account_move_line l, 
                            account_journal j  where l.journal_id=j.id and  l.reconcile_partial_id in (select reconcile_id 
                        FROM account_move_line al, account_invoice i  
                        WHERE al.move_id = i.move_id and al.id=%s)  and j.type in ('bank', 'cash')""" % line.id)
            lines = lines + cr.fetchall()
        logger.info("lines reconciled %s: %s ", line, lines)
        if not lines:
        	continue

        journal = a_journal_obj.browse(cr, uid, lines[0][1])
        
        payment_type = invoice.type in ('out_invoice', 'in_refund') and 'inbound' or 'outbound'
        payment_method_id = PAYMENT_METHODS[lines[0][2]][payment_type]
        journal_payment_methods = payment_type == 'inbound' and journal.inbound_payment_method_ids or journal.outbound_payment_method_ids
        payment_method_id = journal_payment_methods[0].id
        vals = {
			'name': 'Draft Payment', # TODO: name by sequence
            'journal_id': journal.id,
            'payment_method_id': payment_method_id,
            'payment_date': move.date,
            'communication': invoice.reference,
            'invoice_ids': [(4, invoice_id, None)],
            'payment_type': payment_type,
            'amount': move.amount,
            'currency_id': invoice.currency_id.id,
            'partner_id': invoice.partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoice.type],
            'company_id':move.company_id.id,
        }
        logger.info("Creating a payment: %s ", vals)
        a_payment_id = a_payment_obj.create(cr, uid, vals)
        for line in lines:
            a_move_line_obj.write(cr, uid, [line[0]], {'payment_id': a_payment_id})
            cr.execute("""INSERT INTO account_invoice_account_move_line_rel (%s, %s) """ % (invoice.id, line[0])) 
        
@openupgrade.migrate()
def migrate(cr, version):
    registry = RegistryManager.get(cr.dbname)
    migrate_account_type(cr, registry)
    migrate_move_invoice(cr, registry)
    migrate_payment_method(cr, registry)
    migrate_payment(cr, registry)
	
    cr.execute("UPDATE wkf_instance SET state='active' where state='deactive'")
    