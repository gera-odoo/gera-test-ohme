# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    installer_parent_id = fields.Many2one('helpdesk.ticket', 'Parent Ticket')
    installer_ticket_ids = fields.One2many('helpdesk.ticket', 'installer_parent_id', string='Installer Ticket(s)')
    installer_ticket_count = fields.Integer('Installer Ticket Count',
                                            compute='compute_installer_ticket_count',
                                            help='Number of Installer Tickets linked to this ticket')
    related_active_ticket_count = fields.Integer(string='Active Tickets Count',
                                          compute='compute_related_ticket_count',
                                          help='Number of Open tickets from same customer')
    related_closed_ticket_count = fields.Integer(string='Closed Tickets Count',
                                          compute='compute_related_ticket_count',
                                          help='Number of Open tickets from same customer')

    @api.depends('installer_parent_id')
    def compute_installer_ticket_count(self):
        for ticket in self:
            installer_ticket_count = self.env['helpdesk.ticket'].search_count([('installer_parent_id', '=', ticket.id)])
            ticket.installer_ticket_count = installer_ticket_count

    @api.depends('partner_id', 'stage_id')
    def compute_related_ticket_count(self):
        for ticket in self:
            domain = [('partner_email', 'ilike', ticket.partner_email),
                      ('id', '!=', self._origin.id)]
            active_ticket_count = self.env['helpdesk.ticket'].search_count(
                domain + [('stage_id.is_close', '=', False)])
            closed_ticket_count = self.env['helpdesk.ticket'].search_count(
                domain + [('stage_id.is_close', '=', True)])

            ticket.related_active_ticket_count = active_ticket_count
            ticket.related_closed_ticket_count = closed_ticket_count

    def action_view_related_tickets(self):
        action = self.env["ir.actions.actions"]._for_xml_id("helpdesk.helpdesk_ticket_action_main_tree")

        if self.env.context.get('show_installer_tickets', False):
            action['context'] = {'default_installer_parent_id': self.id}
            action['domain'] = [('installer_parent_id', '=', self.id)]
            return action
        else:
            action['context'] = {'create': 0}
            domain = [('id', '!=', self.id),
                      ('partner_email', 'ilike', self.partner_email)]

        if self.env.context.get('show_active_tickets', False):
            domain += [('stage_id.is_close', '=', False)]
        else:
            domain += [ ('stage_id.is_close', '=', True)]
        action['domain'] = domain

        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: