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

PAYMENT_METHODS = {
					'bank': {'inbound':1, 'outbound':1},
					'cash': {'inbound':1, 'outbound':1},
					'general': {'inbound':1, 'outbound':1},
					'purchase': {'inbound':1, 'outbound':1},
					'sale': {'inbound':1, 'outbound':1},
				}

  
def migrate_move_invoice(cr, registry):
    """."""
    a_move_line_obj = registry['account.move.line']

    cr.execute('SELECT l.id, i.id ' \
                        'FROM account_move_line l, account_invoice i ' \
                        'WHERE l.move_id = i.move_id ')

    for line_id, invoice_id in cr.fetchall():
        a_move_line_obj.write(cr, uid, [line_id], {'invoice_id': invoice_id})
          
def migrate_payment_method(cr, registry):
    """Create a Push rule for each pair of locations linked. Will break if
    there are multiple warehouses for the same company."""
    a_pay_meth_obj = registry['account.payment.method']
    PAYMENT_METHODS['bank']['inbound'] = a_pay_meth_obj.create(cr, uid, {'name':'Bank', 'code':'bank', 'payment_type':'inbound'})
    PAYMENT_METHODS['bank']['outbound'] = a_pay_meth_obj.create(cr, uid, {'name':'Bank', 'code':'bank', 'payment_type':'outbound'})
    PAYMENT_METHODS['cash']['inbound'] = a_pay_meth_obj.create(cr, uid, {'name':'Cash', 'code':'cash', 'payment_type':'inbound'})
    PAYMENT_METHODS['cash']['outbound'] = a_pay_meth_obj.create(cr, uid, {'name':'Cash', 'code':'cash', 'payment_type':'outbound'})
    PAYMENT_METHODS['general']['inbound'] = a_pay_meth_obj.create(cr, uid, {'name':'General', 'code':'general', 'payment_type':'inbound'})
    PAYMENT_METHODS['general']['outbound'] = a_pay_meth_obj.create(cr, uid, {'name':'General', 'code':'general', 'payment_type':'outbound'})
    PAYMENT_METHODS['purchase']['inbound'] = a_pay_meth_obj.create(cr, uid, {'name':'Purchase', 'code':'purchase', 'payment_type':'inbound'})
    PAYMENT_METHODS['purchase']['outbound'] = a_pay_meth_obj.create(cr, uid, {'name':'Purchase', 'code':'purchase', 'payment_type':'outbound'})
    PAYMENT_METHODS['sale']['inbound'] = a_pay_meth_obj.create(cr, uid, {'name':'Sale', 'code':'sale', 'payment_type':'inbound'})
    PAYMENT_METHODS['sale']['outbound'] = a_pay_meth_obj.create(cr, uid, {'name':'Sale', 'code':'sale', 'payment_type':'outbound'})
 

def migrate_payment_info_JSON(cr, registry):
    a_invoice_obj = registry['account.invoice']
    
    cr.execute('SELECT i.id  FROM account_invoice i')

    for invoice_id in cr.fetchall():
        invoice = a_invoice_obj.browse(cr, uid, invoice_id)
        invoice.payments_widget = json.dumps(False)
        if invoice.payment_move_line_ids:
            info = {'title': _('Less Payment'), 'outstanding': False, 'content': []}
            for payment in invoice.payment_move_line_ids:
                #we don't take into account the movement created due to a change difference
                if payment.currency_id and payment.move_id.rate_diff_partial_rec_id:
                    continue
                if invoice.type in ('out_invoice', 'in_refund'):
                    amount = sum([p.amount for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
                    amount_currency = sum([p.amount_currency for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
                elif invoice.type in ('in_invoice', 'out_refund'):
                    amount = sum([p.amount for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
                    amount_currency = sum([p.amount_currency for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
                # get the payment value in invoice currency
                if payment.currency_id and amount_currency != 0:
                    currency_id = payment.currency_id
                    amount_to_show = -amount_currency
                else:
                    currency_id = payment.company_id.currency_id
                    amount_to_show = -amount
                info['content'].append({
                    'name': payment.name,
                    'journal_name': payment.journal_id.name,
                    'amount': amount_to_show,
                    'currency': currency_id.symbol,
                    'digits': [69, currency_id.decimal_places],
                    'position': currency_id.position,
                    'date': payment.date,
                    'payment_id': payment.id,
                    'move_id': payment.move_id.id,
                    'ref': payment.move_id.ref,
                })
        	a_invoice_obj.write(cr, uid, [invoice_id], {'payments_widget': json.dumps(info)})

def migrate_payment(cr, registry):
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

        #journal = a_journal_obj.browse(cr, uid, lines[0][1])
        
        payment_type = invoice.type in ('out_invoice', 'in_refund') and 'inbound' or 'outbound'
        payment_method_id = PAYMENT_METHODS[lines[0][2]][payment_type]
        vals = {
			'name': 'Draft Payment', # TODO: name by sequence
            'journal_id': lines[0][1],
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
        
@openupgrade.migrate()
def migrate(cr, version):
	registry = RegistryManager.get(cr.dbname)
	migrate_move_invoice(cr, registry)
	migrate_payment_method(cr, registry)
	migrate_payment(cr, registry)
	migrate_payment_info_JSON(cr, registry)
	
   	cr.execute("UPDATE wkf_instance SET state='active' where state='deactive'")
    