# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 KTec S.r.l.
#    (<http://www.ktec.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models,fields, api, _
from openerp.exceptions import except_orm, Warning

class DeferredInvoice_SaleOrder(models.Model):

    _inherit = 'sale.order'

    def _prepare_invoice(self,cr, uid, order, lines, context):

        res = super(DeferredInvoice_SaleOrder, self)._prepare_invoice(cr, uid, order, lines, context)

        if len(res) == 0:
            return res

        if not res['payment_term']:
            res.update({'date_due':res['date_invoice']})

        return res

    @api.multi
    def action_invoice_create(self, grouped=False, states=None, date_invoice = False,
                              deferred_invoice = None, group_ddt_line = None):

        if not deferred_invoice:
            return super(DeferredInvoice_SaleOrder, self).action_invoice_create(grouped, states, date_invoice)

        if states is None:
            states = ['confirmed', 'done', 'exception']
        res = False
        invoices = {}
        invoice_ids = []
        invoice = self.env['account.invoice']
        obj_sale_order_line = self.env['sale.order.line']
        partner_currency = {}
        # If date was specified, use it as date invoiced, usefull when invoices are generated this month and put the
        # last day of the last month as invoice date
        if date_invoice:
            context = dict(context or {}, date_invoice=date_invoice)
        for o in self:
            currency_id = o.pricelist_id.currency_id.id
            if (o.partner_id.id in partner_currency) and (partner_currency[o.partner_id.id] <> currency_id):
                raise except_orm(
                    _('Error!'),
                    _('You cannot group sales having different currencies for the same partner.'))

            partner_currency[o.partner_id.id] = currency_id

            lines = []
            if group_ddt_line:
                for line in o.order_line:
                    if line.invoiced and group_ddt_line:
                        raise except_orm(
                            _('Error!'),
                            _('You cannot group sales on ddt having invoiced lines.'))
                lines.append(obj_sale_order_line._deferredinvoice_single_invoice_line(o))
            else:
                for line in o.order_line:
                    if line.invoiced:
                        continue
                    elif (line.state in states):
                        lines.append(obj_sale_order_line._deferredinvoice_single_invoice_line(line))
            if lines:
                invoices.setdefault(o.partner_invoice_id.id or o.partner_id.id, []).append((o, lines))

        #ToDo: Controllare questo pezzo
        if not invoices:
            for o in self:
                for i in o.invoice_ids:
                    if i.state == 'draft':
                        return i.id

        for val in invoices.values():
            if grouped:
                res = self._make_invoice(val[0][0], reduce(lambda x, y: x + y, [l for o, l in val], []))
                invoice_ref = ''
                origin_ref = ''
                for o, l in val:
                    invoice_ref += (o.client_order_ref or o.name) + '|'
                    origin_ref += (o.origin or o.name) + '|'
                    o.state = 'progress'
                    self.env.cr.execute('insert into sale_order_invoice_rel (order_id,invoice_id) values (%s,%s)',
                                        (o.id, res))
                    self.env.invalidate_all()
                #remove last '|' in invoice_ref
                if len(invoice_ref) >= 1:
                    invoice_ref = invoice_ref[:-1]
                if len(origin_ref) >= 1:
                    origin_ref = origin_ref[:-1]
                invoice.write(cr, uid, [res], {'origin': origin_ref, 'name': invoice_ref})
            else:
                for order, il in val:
                    res = self._make_invoice(cr, uid, order, il, context=context)
                    invoice_ids.append(res)
                    self.write(cr, uid, [order.id], {'state': 'progress'})
                    cr.execute('insert into sale_order_invoice_rel (order_id,invoice_id) values (%s,%s)', (order.id, res))
                    self.invalidate_cache(cr, uid, ['invoice_ids'], [order.id], context=context)
        return res


class DeferredInvoice_SeleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):

        res = super(DeferredInvoice_SeleOrderLine,self)._prepare_order_line_invoice_line(cr, uid, line,
                                                                                         account_id, context)

        if len(res) == 0:
            return res
        ddt_ref = []
        for pk_id in line.order_id.picking_ids:
            if pk_id.ddt_id and pk_id.ddt_id.state == 'confirmed':
                ddt_ref.append('{0} : {1:%Y-%m-%d}'.format(pk_id.ddt_id.name,
                                                           fields.Datetime.from_string(pk_id.ddt_id.date)))
            elif pk_id.ddt_id and (pk_id.ddt_id.state == 'draft'):
                raise except_orm(_('Error!'),
                                 _('Impossibile creare la fattura con DDT in bozza o cancellati'))

        ddt_str = None
        for ref in set(ddt_ref):
            ddt_str = ref + ' | '
        ddt_str = ddt_str[:-3] if ddt_str else False

        res.update({'ddt_ref': ddt_str})

        return res


class DeferredInvoice_AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    ddt_ref = fields.Char(compute='_ddtref_fromline',
        string='DDT Reference'
    )

    #get ddt ref from lines
    @api.one
    @api.depends('invoice_line')
    def _ddtref_fromline(self):

        ddt_refs = []
        for line in self.invoice_line:
            if line.ddt_ref:
                ddt_refs.append(line.ddt_ref)
        ddt_refs = set(ddt_refs)

        ddt_ref = ''
        for ddt in ddt_refs:
            ddt_ref += ddt+' | '
        self.ddt_ref = ddt_ref[:-3] if ddt_ref else False


class DeferredInvoice_AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    ddt_ref = fields.Char(
        string='DDT Reference'
    )