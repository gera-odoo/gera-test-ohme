# -*- coding: utf-8 -*-
from odoo import models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _compute_sale_data(self):
        res = super(CrmLead, self)._compute_sale_data()
        set_won = False

        for lead in self:
            if lead.order_ids and all([x.state == 'sale' for x in lead.order_ids]):
                set_won = True
        if set_won:
            self.action_set_won()

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: