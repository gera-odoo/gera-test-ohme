from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ohm_url = fields.Char('Fleet API', config_parameter='ohme.url')
    ohm_token = fields.Char('Token', config_parameter='ohme.token')
