# -*- coding: utf-8 -*-
from odoo import models, fields
from dateutil.relativedelta import relativedelta


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def _calculate_date_deadline(self, activity_type):
        res = super(MailActivity, self)._calculate_date_deadline(activity_type=activity_type)
        if self.res_model == 'helpdesk.ticket':
            days = 2 if res.weekday() == 5 else 1 if res.weekday() == 6 else 0
            return res + relativedelta(days=days)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: