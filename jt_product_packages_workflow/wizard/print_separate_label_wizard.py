# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64


class PrintSeparateLabelWizard(models.TransientModel):

    _name = "print.separate.label.wizard"
    _description = "Model to generate selected label from multiple labels"

    def _check_domain(self):
        ctx = self._context
        domain = []
        if ctx and ctx.get('active_id'):
            active_id = ctx.get('active_id')
            MO = self.env['mrp.production'].browse(active_id)
            if MO:
                domain = [('manufacturing_order_id', '=', MO.id)]
            if self and self.manufacturing_order_id:
                domain = [('manufacturing_order_id', '=', self.manufacturing_order_id.id)]
        return domain

    labels = fields.Many2many('package.sequence', string="Select Labels", domain=_check_domain)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    report = fields.Binary('Prepared file', readonly=True)
    report1 = fields.Binary('Prepared file', readonly=True)
    name = fields.Char('File Name')
    manufacturing_order_id = fields.Many2one(
        'mrp.production', string="Manufacturing Order")
    start_range = fields.Char(string="Start Range")
    end_range = fields.Char(string="End Range")

    @api.model
    def default_get(self, fields):
        result = super(PrintSeparateLabelWizard, self).default_get(fields)
        ctx = self._context
        active_id = ctx.get('active_id')
        MO = self.env['mrp.production'].browse(active_id)
        if MO:
            sequences = MO.get_sequences()
            if sequences:
                result['start_range'] = sequences[0]
                result['end_range'] = sequences[-1]
            result.update({
                'manufacturing_order_id': MO.id,
            })
        return result

    def add_labels_to_list(self):
        self.ensure_one()
        if not self.start_range or not self.end_range:
            raise ValidationError("Please enter label range to add into label list")
        labels = []
        for sequence in range(int(self.start_range), int(self.end_range) + 1):
            seq = str(sequence).zfill(4)
            mo_sequence = self.env['package.sequence'].search([('sequence', '=', seq), ('manufacturing_order_id', '=', self.manufacturing_order_id.id)], limit=1)
            if mo_sequence:
                labels.append(mo_sequence.id)
        self.write({'labels': [(6, 0, labels)]})

        # Return to wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'print.separate.label.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def clear_list(self):
        self.labels = False
        # Return to wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'print.separate.label.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def get_report(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx['from_preview'] = True
        return self.with_context(ctx).print_report()

    def print_report(self):
        self.ensure_one()

        if self.manufacturing_order_id:

            # Get report
            report = self.env.ref(
                'jt_product_packages_workflow.package_label_report')

            # Set Context
            ctx = self.env.context.copy()

            labels = []
            for label in self.labels:
                labels.append(label.sequence)
            ctx['labels'] = labels

            # Call report with context
            pdf = report.with_context(ctx).render_qweb_pdf(self.manufacturing_order_id.id)

            # Store report as PDF so user can download
            context = {}
            out = base64.b64encode(pdf[0])
            context['name'] = 'Separate_labels.pdf'

            context['file'] = out
            self.write({'report': out, 'name': context['name']})
            if not ctx.get('from_preview'):
                self.write({'state': 'get'})
            if ctx.get('from_preview'):
                self.write({'report1': out})

        # Return to wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'print.separate.label.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
