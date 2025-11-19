from odoo import models, fields, api
from datetime import date

class TurnOverWizard(models.TransientModel):
    _name = 'turn.over.wizard'
    _description = "Assistant du Chiffre d'Affaires Global"

    sale_src = fields.Selection([
        ('all', 'Global'),
        ('pos', 'Point de vente'),
        ('sale', 'Vente'),
    ], string='Source', compute='_compute_sale_src', store=True, readonly=False)
    start_date = fields.Date(string="Date de début", default=lambda self: date.today().replace(day=1))
    end_date = fields.Date(string="Date de fin", default=lambda self: date.today())
    rayon_id = fields.Many2one('product.section', string="Rayon")
    company_id = fields.Many2one('res.company', string="Société", default=lambda self: self.env.company)
    pos_order_id = fields.Many2one('pos.order', string="Commande POS")
    sale_order_id = fields.Many2one('sale.order', string="Commande Vente")

    @api.depends('pos_order_id', 'sale_order_id')
    def _compute_sale_src(self):
        for record in self:
            if record.pos_order_id:
                record.sale_src = 'pos'
            elif record.pos_sale_order_id:
                record.sale_src = 'sale'
            else:
                record.sale_src = 'all'


    def _get_turn_over_data(self):
        report_data = {}
        total_vente = 0.0
        total_pos = 0.0

        def add_line(line, qty, price_unit, source):
            nonlocal total_vente, total_pos

            rayon = line.product_id.section_id
            parent = rayon.parent_id or rayon  # Si pas de parent, rayon lui-même
            parent_name = parent.name or "Sans catégorie"
            rayon_name = rayon.name or "Sans rayon"

            #Si le parent n'existe pas encore
            if parent_name not in report_data:
                report_data[parent_name] = {
                    'total_achat': 0.0,
                    'total_vente': 0.0,
                    'rayons': {}
                }

            #Si le sous-rayon n'existe pas encore
            if rayon_name not in report_data[parent_name]['rayons']:
                report_data[parent_name]['rayons'][rayon_name] = {
                    'total_achat': 0.0,
                    'total_vente': 0.0
                }
            total_achat_line = line.product_id.standard_price * qty
            total_vente_line = price_unit * qty
            
            report_data[parent_name]['total_achat'] += total_achat_line
            report_data[parent_name]['total_vente'] += total_vente_line
            report_data[parent_name]['rayons'][rayon_name]['total_achat'] += total_achat_line
            report_data[parent_name]['rayons'][rayon_name]['total_vente'] += total_vente_line

            if source == 'sale':
                total_vente += total_vente_line
            elif source == 'pos':
                total_pos += total_vente_line

        #VENTES
        sale_domain = [
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date)
        ]
        if self.rayon_id:
            sale_domain.append(('product_id.section_id', '=', self.rayon_id.id))

        sale_lines = self.env['sale.order.line'].search(sale_domain)
        for line in sale_lines:
            add_line(line, line.product_uom_qty, line.price_unit, 'sale')

        #POINT DE VENTE
        pos_domain = [
            ('order_id.state', 'in', ['paid', 'done', 'invoiced']),
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date)
        ]
        if self.rayon_id:
            pos_domain.append(('product_id.section_id', '=', self.rayon_id.id))

        pos_lines = self.env['pos.order.line'].search(pos_domain)
        for line in pos_lines:
            add_line(line, line.qty, line.price_unit, 'pos')

        #otaux globaux
        total_general_achat = sum(v['total_achat'] for v in report_data.values())
        total_general_vente = sum(v['total_vente'] for v in report_data.values())
        total_general_marge = total_general_vente - total_general_achat

        return {
            'report_data': report_data,
            'vente': total_vente,
            'pos': total_pos,
            'total_general_achat': total_general_achat,
            'total_general_vente': total_general_vente,
            'total_general_marge': total_general_marge,
        }

    def _get_turn_over_pos_data(self):
        report_data = {}
        total_pos = 0.0

        def add_line(line, qty, price_unit, source):
            nonlocal total_pos

            rayon = line.product_id.section_id
            parent = rayon.parent_id or rayon  
            parent_name = parent.name or "Sans catégorie"
            rayon_name = rayon.name or "Sans rayon"

            #Si le parent n'existe pas encore
            if parent_name not in report_data:
                report_data[parent_name] = {
                    'total_achat': 0.0,
                    'total_vente': 0.0,
                    'rayons': {}
                }

            #Si le sous-rayon n'existe pas encore
            if rayon_name not in report_data[parent_name]['rayons']:
                report_data[parent_name]['rayons'][rayon_name] = {
                    'total_achat': 0.0,
                    'total_vente': 0.0
                }
            total_achat_line = line.product_id.standard_price * qty
            total_vente_line = price_unit * qty
            
            report_data[parent_name]['total_achat'] += total_achat_line
            report_data[parent_name]['total_vente'] += total_vente_line
            report_data[parent_name]['rayons'][rayon_name]['total_achat'] += total_achat_line
            report_data[parent_name]['rayons'][rayon_name]['total_vente'] += total_vente_line

            if source == 'pos':
                total_pos += total_vente_line

             #POINT DE VENTE
        pos_domain = [
            ('order_id.state', 'in', ['paid', 'done', 'invoiced']),
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date)
        ]
        if self.rayon_id:
            pos_domain.append(('product_id.section_id', '=', self.rayon_id.id))

        pos_lines = self.env['pos.order.line'].search(pos_domain)
        for line in pos_lines:
            add_line(line, line.qty, line.price_unit, 'pos')

        #otaux globaux
        total_general_achat = sum(v['total_achat'] for v in report_data.values())
        total_general_vente = sum(v['total_vente'] for v in report_data.values())
        total_general_marge = total_general_vente - total_general_achat

        return {
            'report_data': report_data,
            'pos': total_pos,
            'total_general_achat': total_general_achat,
            'total_general_vente': total_general_vente,
            'total_general_marge': total_general_marge,
        }
    
    def _get_turn_over_sale_data(self):
        report_data = {}
        total_vente = 0.0

        def add_line(line, qty, price_unit):
            nonlocal total_vente

            payment_term = line.order_id.payment_term_id.name or "Sans condition de paiement"
            rayon = line.product_id.section_id
            parent = rayon.parent_id or rayon
            parent_name = parent.name or "Sans catégorie"
            rayon_name = rayon.name or "Sans rayon"

            # Si la condition de paiement n'existe pas encore
            if payment_term not in report_data:
                report_data[payment_term] = {
                    'total_achat': 0.0,
                    'total_vente': 0.0,
                    'categories': {}
                }

            condition_data = report_data[payment_term]

            # Si la catégorie n'existe pas encore sous cette condition
            if parent_name not in condition_data['categories']:
                condition_data['categories'][parent_name] = {
                    'total_achat': 0.0,
                    'total_vente': 0.0,
                    'rayons': {}
                }

            category_data = condition_data['categories'][parent_name]

            # Si le rayon n'existe pas encore
            if rayon_name not in category_data['rayons']:
                category_data['rayons'][rayon_name] = {
                    'total_achat': 0.0,
                    'total_vente': 0.0
                }

            rayon_data = category_data['rayons'][rayon_name]

            total_achat_line = line.product_id.standard_price * qty
            total_vente_line = price_unit * qty

            rayon_data['total_achat'] += total_achat_line
            rayon_data['total_vente'] += total_vente_line

            category_data['total_achat'] += total_achat_line
            category_data['total_vente'] += total_vente_line

            condition_data['total_achat'] += total_achat_line
            condition_data['total_vente'] += total_vente_line

            total_vente += total_vente_line

        
        # VENTES 
        sale_domain = [
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date),
        ]
        if self.rayon_id:
            sale_domain.append(('product_id.section_id', '=', self.rayon_id.id))

        sale_lines = self.env['sale.order.line'].search(sale_domain)
        for line in sale_lines:
            add_line(line, line.product_uom_qty, line.price_unit)

        # Totaux généraux
        total_general_achat = sum(
            condition['total_achat'] for condition in report_data.values()
        )
        total_general_vente = sum(
            condition['total_vente'] for condition in report_data.values()
        )
        total_general_marge = total_general_vente - total_general_achat

        return {
            'report_data': report_data,
            'total_general_achat': total_general_achat,
            'total_general_vente': total_general_vente,
            'total_general_marge': total_general_marge,
            'total_vente': total_vente,
        }



 
 
    def generate_report(self):
        """Génère le rapport selon la source sélectionnée (sale_src)."""
        self.ensure_one()
        print(">>> Génération rapport pour :", self.sale_src)

        if self.sale_src == 'pos':
            report_action = self.env.ref('preva_custom_report.action_report_turn_over_pos')
        elif self.sale_src == 'sale':
            report_action = self.env.ref('preva_custom_report.action_report_turn_over_sale')
        else:
            report_action = self.env.ref('preva_custom_report.action_report_turn_over')

        return report_action.report_action(self)

