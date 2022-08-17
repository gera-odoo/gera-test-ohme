# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import Warning
import pulp
from pulp import *


class NutrInfo(models.Model):
    _name = 'nutrimental.info'
    _description = 'Nutrimental Info'
    _rec_name = 'nutriment_id'
    _sql_constraints = [
        ('code', 'unique(code)',
         "There is already a code used for a nutriment. Please select a new one")
    ]

    nutriment_id = fields.Many2one('nutrimental.value', string="Nutriment", index=True)
    value = fields.Float(string="Value", digits=(12, 4))
    uom_id = fields.Many2one('uom.uom', string="Unit of measure", compute="", inverse="_pass", store=True)
    code = fields.Char(string="Code", help="Short name used to identify the nutrimental value",
                       related="nutriment_id.code")
    product_id = fields.Many2one('product.product', string="Product")
    group_id = fields.Many2one('nutrimental.group', related="nutriment_id.group_id", store=True,
                               string="Classification")

    def _pass(self):
        pass

    @api.depends('nutriment_reference_id')
    def get_default_uom(self):
        for record in self:
            if record.nutriment_reference_id.uom_id:
                record.uom_id = record.nutrimet_reference_id.uom_id.id
            else:
                record.uom_id = False


class NutrimentalPairs(models.Model):
    _name = 'nutrimental.pairs'
    _description = 'Nutrimental pairs'
    _rec_name = "display_name"

    display_name = fields.Char(string="Display name", compute="get_name", store=True)
    pair_lines = fields.One2many('nutrimental.pairs.line', 'pair_id', string="Lines")

    @api.depends('pair_lines.display_name', 'pair_lines', 'pair_lines.unit_type')
    def get_name(self):
        for record in self:
            if 0 > len(record.pair_lines) > len(record.pair_lines.filtered(lambda c: c.unit_type == 'single')):
                raise Warning('It is not possible to use a single unit type with multiple lines')
            elif len(record.pair_lines.filtered(lambda c: c.unit_type == 'divider')) >= 1 and not len(
                    record.pair_lines.filtered(lambda c: c.unit_type == 'dividend')):
                raise Warning('Please select a dividend for this record')
            text = ''
            text2 = ''
            if len(record.pair_lines.filtered(lambda c: c.unit_type == 'dividend')):
                text = ' '
                for line in record.pair_lines.filtered(lambda c: c.unit_type == 'dividend'):
                    text += '(' + line.display_name + ') '
            if len(record.pair_lines.filtered(lambda c: c.unit_type == 'divider')):
                text2 = '/'
                for line in record.pair_lines.filtered(lambda c: c.unit_type == 'divider'):
                    text2 += '(' + line.display_name + ') '
            record.display_name = text + text2


class NutrimentalPairsLines(models.Model):
    _name = 'nutrimental.pairs.line'
    _description = 'Nutrimental pairs'
    _rec_name = 'display_name'

    display_name = fields.Char(string="Display name", compute="_compute_complete_name", store=True)
    pair_id = fields.Many2one('nutrimental.pairs', string="Pair")
    uom_id = fields.Many2one('uom.uom', string="Unit of measure")
    nutriment_id = fields.Many2one('nutrimental.value', string="Nutrimental value")
    type = fields.Selection([('nutriment', 'Nutriment'), ('group', 'Group')])
    group_id = fields.Many2one('nutrimental.group', string="Nutrimental group")
    unit_type = fields.Selection([('single', 'Single'), ('dividend', 'Dividend'), ('divider', 'Divider')],
                                 string="Type")

    @api.depends('uom_id', 'nutriment_id', 'group_id')
    def _compute_complete_name(self):
        for record in self:
            if record.uom_id.name and record.nutriment_id.name:
                record.display_name = '%s  %s' % (record.uom_id.name, record.nutriment_id.name)
            elif record.uom_id.name and record.group_id.name:
                record.display_name = '%s  %s' % (record.uom_id.name, record.group_id.name)
            else:
                record.display_name = False


class Product(models.Model):
    _inherit = 'product.product'

    nutrimental_ids = fields.One2many('nutrimental.info', 'product_id', string="Nutrimental info")
    display_nutrimental_info = fields.Boolean(related="categ_id.display_nutrimental_info",
                                              string="Display nutrimental info?")


class ProductCateg(models.Model):
    _inherit = 'product.category'

    display_nutrimental_info = fields.Boolean(string="Display nutrimental info?")


class Nutriment(models.Model):
    _name = 'nutrimental.value'
    _description = 'Nutriment'
    _rec_order = 'sequence'
    _rec_name = 'display_name'

    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(string="Active", store=True, default=True)
    display_name = fields.Char(string="Display Name", compute="_compute_complete_name", store=True, index=True)
    code = fields.Char(string="Code", help="Short name used to identify the nutrimental value", required=True)
    sequence = fields.Integer(string="Sequence", help="Sequence to choose the order of the nutriments")
    group_id = fields.Many2one('nutrimental.group', string="Classification")
    uom_id = fields.Many2one('uom.uom', string="Default unit of measure")

    @api.depends('name', 'code')
    def _compute_complete_name(self):
        for record in self:
            if record.name and record.code:
                record.display_name = '%s / %s' % (record.code, record.name)
            else:
                record.display_name = False


class NutrimentGroup(models.Model):
    _name = 'nutrimental.group'
    _description = 'Nutrimental group'

    name = fields.Char(string="Name")
    value_ids = fields.One2many('nutrimental.value', 'group_id', string="Nutriments")


class Needs(models.Model):
    _name = 'nutrimental.needs'
    _description = 'Needs group'

    need_line_ids = fields.One2many(comodel_name='nutrimental.needs.line', inverse_name='need_id',
                                    string="Specific needs", required=True)
    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(string="Active", default=True)
    based_on = fields.Text(string="Based On",
                           help="Used to display the computations the needs are based on, for the computation of every value use X")
    nutriment_reference_id = fields.Many2one('nutrimental.pairs', string="Nutriment base")
    reference_code = fields.Char(string="Code")
    action_id = fields.Many2one('ir.actions.server', string="Action needed")

    # def _pass(self):
    #     pass
    #
    # @api.depends('nutriment_reference_id')
    # def get_default_uom(self):
    #     for record in self:
    #         if record.nutriment_reference_id.uom_id:
    #             record.uom_id = record.nutrimet_reference_id.uom_id.id
    #         else:
    #             record.uom_id = False


class NeedsLine(models.Model):
    _name = 'nutrimental.needs.line'
    _description = 'Nutrimental needs specifications'
    _rec_name = 'code'

    nutriment_ids = fields.Many2many('nutrimental.value', string="Nutriment", index=True)
    code = fields.Char(string="Code", help="Write the code or operations the calculation must take into account",
                       compute="get_code", inverse="_pass", store=True)
    need_id = fields.Many2one('nutrimental.needs', string="Nutrimental need",
                              help="Used to specify the need that is needed to cover")
    reference_value = fields.Float(string="Reference value")
    objective_function = fields.Boolean(string="Builts OF",
                                        help="If it is true, it will be considered for the calculation of the objective function")
    uom_id = fields.Many2one('uom.uom', string="Unit of measure", compute="get_default_uom", inverse="_pass",
                             store=True)
    type = fields.Selection([('=', '='), ('>', '>'), ('<', '<'), ('≠', '≠'), ('≥', '≥'), ('≤', '≤')], default='=',
                            string="Restriction")
    is_div = fields.Boolean(string="Is divider", compute="get_div", store=True)

    @api.depends('need_id', 'need_id.nutriment_reference_id', 'need_id.nutriment_reference_id.pair_lines.unit_type')
    def get_div(self):
        for record in self:
            if record.need_id and len(record.need_id.nutriment_reference_id.pair_lines.filtered(
                    lambda c: c.unit_type == 'divider' and c.nutriment_id == record.nutriment_ids)):
                record.is_div = True
            elif record.need_id and len(record.need_id.nutriment_reference_id.pair_lines.filtered(
                    lambda c: c.unit_type == 'divider' and c.group_id in record.nutriment_ids.mapped('group_id'))):
                record.is_div = True
            else:
                record.is_div = False

    @api.depends('nutriment_ids')
    def get_default_uom(self):
        for record in self:
            if len(record.nutriment_ids.mapped('uom_id')) == 1:
                record.uom_id = record.nutriment_ids[0].uom_id.id
            else:
                record.uom_id = False

    def _pass(self):
        pass

    @api.constrains('code')
    def valid_code(self):
        for record in self:
            for code in record.nutriment_ids:
                if code.code not in record.code and code.active and record.need_id.active:
                    raise Warning(
                        'Please use the code of the nutriment %s' % code.name + ": %s " % code.code + ' in this text')

    @api.depends('nutriment_ids', 'nutriment_ids.code')
    def get_code(self):
        for record in self:
            if len(record.nutriment_ids) == 1 and len(record.nutriment_ids.code) == 1:
                record.code = record.nutriment_ids[0].code
            else:
                record.code = False


class Blend(models.Model):
    _name = 'blend.optimization'
    _description = 'Blend optimization'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", required=True)
    need_id = fields.Many2one('nutrimental.needs', string="Nutrimental need", index=True, required=True)
    needs_ids = fields.One2many(related='need_id.need_line_ids', string="Reference values")
    solution = fields.Char(string="Solution status")
    product_ids = fields.Many2many('product.product', string="Products",
                                   domain="[('display_nutrimental_info','=',True)]", required=True)
    result_ids = fields.One2many('blend.optimization.line', 'blend_id', string="Results")
    process_ids = fields.One2many('blend.optimization.process', 'blend_id', string="Process")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string="State", default='draft')
    global_restrictions = fields.Float(string="Global restrictions", compute="get_global_restr", store=True)
    objective_value = fields.Float(string="Objective Value")
    total_mix = fields.Float(string="Sum of values", compute="get_sum_mix", store=True)

    @api.depends('result_ids', 'result_ids.value')
    def get_sum_mix(self):
        for record in self:
            if len(record.result_ids) > 0:
                record.total_mix = sum(record.result_ids.mapped('value'))
            else:
                record.total_mix = False

    @api.depends('need_id', 'need_id.need_line_ids', 'need_id.need_line_ids.objective_function')
    def get_global_restr(self):
        for record in self:
            if len(record.need_id.need_line_ids.filtered(lambda c: c.objective_function)):
                record.global_restrictions = sum(
                    record.need_id.need_line_ids.filtered(lambda c: c.objective_function).mapped('reference_value'))
            else:
                record.global_restrictions = False

    def get_process_line(self):
        for record in self:
            if len(record.product_ids) > 0 and len(record.needs_ids) > 0:
                for line in record.product_ids:
                    for item in record.needs_ids:
                        self.env['blend.optimization.process'].create(
                            {'reference_value': item.reference_value, 'blend_id': record.id, 'need_line_id': item.id,
                             'product_id': line.id, 'reference_unit': item.uom_id.id,
                             'uom_id': line.nutrimental_ids.filtered(
                                 lambda c: c.nutriment_id == item.nutriment_ids).mapped('uom_id')[0].id,
                             'nutriment_ids': line.nutrimental_ids.filtered(
                                 lambda c: c.nutriment_id == item.nutriment_ids).ids,
                             'actual_value':
                                 line.nutrimental_ids.filtered(lambda c: c.nutriment_id == item.nutriment_ids).mapped(
                                     'uom_id')[0]._compute_quantity(qty=sum(line.nutrimental_ids.filtered(
                                     lambda c: c.nutriment_id == item.nutriment_ids).mapped('value')) / 100,
                                                                    to_unit=item.uom_id,
                                                                    round=True, rounding_method='UP',
                                                                    raise_if_failure=True)})
                prob = LpProblem(record.name, LpMinimize)
                food_items = record.product_ids.mapped('name')
                food_vars = LpVariable.dicts("Food", record.product_ids.mapped('name'), lowBound=0, cat='Continuous')
                a = []
                for product in record.product_ids:
                    self.env['blend.optimization.line'].create(
                        {'product_id': product.id, 'blend_id': record.id, 'global_nutrs': sum(
                            record.process_ids.filtered(
                                lambda c: c.product_id.id == product.id and c.need_line_id.objective_function).mapped(
                                'actual_value')), 'reference_lp': food_vars[product.name]})
                    if len(record.needs_ids.filtered(lambda c: c.is_div)) == 0:
                        a.append(sum(record.result_ids.filtered(lambda c: c.product_id.id == product.id).mapped(
                            'global_nutrs')) * food_vars[product.name] - record.global_restrictions)
                    else:
                        a.append(sum(record.result_ids.filtered(lambda c: c.product_id.id == product.id).mapped(
                            'global_nutrs')) * food_vars[product.name] - (record.global_restrictions * sum(
                            record.process_ids.filtered(
                                lambda c: c.product_id.id == product.id and c.need_line_id.is_div is True).mapped(
                                'actual_value')) * food_vars[product.name]))
                prob += lpSum(a)
                for nutr in record.needs_ids.filtered(lambda c: c.is_div is False):
                    b = []
                    for product in record.product_ids:
                        if len(record.needs_ids.filtered(lambda c: c.is_div)) == 0:
                            b.append(sum(record.process_ids.filtered(
                                lambda c: c.product_id.id == product.id and c.need_line_id.id == nutr.id).mapped(
                                'actual_value')) * food_vars[product.name] - record.global_restrictions)
                        else:
                            b.append(sum(record.process_ids.filtered(
                                lambda c: c.product_id.id == product.id and c.need_line_id.id == nutr.id).mapped(
                                'actual_value')) * food_vars[product.name] - (nutr.reference_value * sum(
                                record.process_ids.filtered(
                                    lambda c: c.product_id.id == product.id and c.need_line_id.is_div is True).mapped(
                                    'actual_value')) * food_vars[product.name]))
                    prob += lpSum(b) >= 0.001, nutr.code
                record.message_post(body=prob)
                prob.solve()
                record.state = 'done'
                record.solution = LpStatus[prob.status]
                for v in prob.variables():
                    if v.varValue > 0:
                        record.result_ids.filtered(lambda c: c.reference_lp == v.name)[0].value = v.varValue
                record.objective_value = round(value(prob.objective), 4)


class BlendLines(models.Model):
    _name = 'blend.optimization.line'
    _description = 'Blend lines'

    blend_id = fields.Many2one('blend.optimization', string="Blend name")
    product_id = fields.Many2one('product.product', string="Product")
    value = fields.Float(string="Value", digits=(12, 6))
    percentage = fields.Float(string="Value (%)", compute="get_percentage", store=True)
    global_nutrs = fields.Float(string="Global weight", help="Global weight for the equation of the product")
    uom_id = fields.Many2one('uom.uom', related="product_id.uom_id")
    reference_uom_id = fields.Many2one('uom.uom', string="UoM Ref")
    reference_lp = fields.Char(string="Reference from LP")

    @api.depends('value', 'blend_id.total_mix')
    def get_percentage(self):
        for record in self:
            if record.value and record.blend_id.total_mix:
                record.percentage = record.value / record.blend_id.total_mix


class BlendProcess(models.Model):
    _name = 'blend.optimization.process'
    description = 'Blend processing'

    blend_id = fields.Many2one('blend.optimization', string="Blend name")
    product_id = fields.Many2one('product.product', string="Product")
    nutriment_ids = fields.Many2many('nutrimental.info', string="Nutrimental info")
    reference_value = fields.Float(string="Reference value")
    reference_unit = fields.Many2one('uom.uom', string="Reference Unit")
    uom_id = fields.Many2one('uom.uom', string="Unit of measure")
    actual_value = fields.Float(string="Value", store=True)
    need_line_id = fields.Many2one('nutrimental.needs.line', string="Need Line")
