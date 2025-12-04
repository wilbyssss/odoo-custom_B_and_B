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
            elif record.sale_order_id:
                record.sale_src = 'sale'
            else:
                record.sale_src = 'all'

    # -------------------------------------------------------
    #   Méthode générale : POS + Vente (sans double comptage)
    # -------------------------------------------------------
    def _get_turn_over_data(self):
        report_data = {}
        total_vente = 0.0
        total_pos = 0.0

        def add_line(line, qty, price_unit, source):
            nonlocal total_vente, total_pos

            rayon = line.product_id.section_id
            parent = rayon.parent_id or rayon
            parent_name = parent.name or "Sans catégorie"
            rayon_name = rayon.name or "Sans rayon"

            if parent_name not in report_data:
                report_data[parent_name] = {
                    'total_achat': 0.0,
                    'total_vente': 0.0,
                    'rayons': {}
                }

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

        # ==================================================
        #   VENTES : exclure celles qui ont été facturées via POS
        # ==================================================
        sale_domain = [
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date),
            #si la vente a été facturée via POS, on l'exclut complètement
            ('order_id.pos_order_line_ids', '=', False),  # Pas de lignes POS liées
        ]

        if self.rayon_id:
            sale_domain.append(('product_id.section_id', '=', self.rayon_id.id))

        sale_lines = self.env['sale.order.line'].search(sale_domain)

        for line in sale_lines:
            # Vérification supplémentaire : la vente ne doit pas avoir de facture POS
            if not line.order_id.invoice_ids.filtered(lambda inv: inv.pos_order_id):
                add_line(line, line.product_uom_qty, line.price_unit, 'sale')

        # ==================================================
        #   POS : inclure TOUT, y compris les ventes facturées via POS
        # ==================================================
        pos_line_domain = [
            ('order_id.state', 'in', ['paid', 'done', 'invoiced']),
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date),
        ]

        if self.rayon_id:
            pos_line_domain.append(('product_id.section_id', '=', self.rayon_id.id))

        pos_lines = self.env['pos.order.line'].search(pos_line_domain)

        for line in pos_lines:
            add_line(line, line.qty, line.price_unit, 'pos')

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

    # -------------------------------------------------------
    #   POS seulement (inchangé)
    # -------------------------------------------------------
    def _get_turn_over_pos_data(self):
        report_data = {}
        total_pos = 0.0

        def add_line(line, qty, price_unit):
            nonlocal total_pos
            rayon = line.product_id.section_id
            parent = rayon.parent_id or rayon
            parent_name = parent.name or "Sans catégorie"
            rayon_name = rayon.name or "Sans rayon"

            if parent_name not in report_data:
                report_data[parent_name] = {'total_achat': 0.0, 'total_vente': 0.0, 'rayons': {}}

            if rayon_name not in report_data[parent_name]['rayons']:
                report_data[parent_name]['rayons'][rayon_name] = {'total_achat': 0.0, 'total_vente': 0.0}

            total_achat = line.product_id.standard_price * qty
            total_vente = price_unit * qty

            report_data[parent_name]['total_achat'] += total_achat
            report_data[parent_name]['total_vente'] += total_vente
            report_data[parent_name]['rayons'][rayon_name]['total_achat'] += total_achat
            report_data[parent_name]['rayons'][rayon_name]['total_vente'] += total_vente

            total_pos += total_vente

        pos_domain = [
            ('order_id.state', 'in', ['paid', 'done', 'invoiced']),
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date),
        ]

        if self.rayon_id:
            pos_domain.append(('product_id.section_id', '=', self.rayon_id.id))

        pos_lines = self.env['pos.order.line'].search(pos_domain)
        for line in pos_lines:
            add_line(line, line.qty, line.price_unit)

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

    # -------------------------------------------------------
    #   Vente seulement (EXCLURE celles facturées via POS)
    # -------------------------------------------------------
    def _get_turn_over_sale_data(self):
        report_data = {}
        total_vente = 0.0

        def add_line(line, qty, price_unit):
            nonlocal total_vente

            payment_term = line.order_id.payment_term_id.name or "Sans condition"
            rayon = line.product_id.section_id
            parent = rayon.parent_id or rayon
            parent_name = parent.name or "Sans catégorie"
            rayon_name = rayon.name or "Sans rayon"

            if payment_term not in report_data:
                report_data[payment_term] = {
                    'total_achat': 0.0,
                    'total_vente': 0.0,
                    'categories': {}
                }

            cond = report_data[payment_term]

            if parent_name not in cond['categories']:
                cond['categories'][parent_name] = {
                    'total_achat': 0.0,
                    'total_vente': 0.0,
                    'rayons': {}
                }

            cat = cond['categories'][parent_name]

            if rayon_name not in cat['rayons']:
                cat['rayons'][rayon_name] = {'total_achat': 0.0, 'total_vente': 0.0}

            total_achat = line.product_id.standard_price * qty
            total_vente_line = price_unit * qty

            cat['rayons'][rayon_name]['total_achat'] += total_achat
            cat['rayons'][rayon_name]['total_vente'] += total_vente_line
            cat['total_achat'] += total_achat
            cat['total_vente'] += total_vente_line
            cond['total_achat'] += total_achat
            cond['total_vente'] += total_vente_line

            total_vente += total_vente_line

        sale_domain = [
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date),
            #Exclure les ventes qui ont des lignes POS
            ('order_id.pos_order_line_ids', '=', False),
        ]

        if self.rayon_id:
            sale_domain.append(('product_id.section_id', '=', self.rayon_id.id))

        sale_lines = self.env['sale.order.line'].search(sale_domain)

        # Vérification supplémentaire au cas où
        for line in sale_lines:
            # S'assurer que la vente n'a pas été facturée via POS
            if not line.order_id.invoice_ids.filtered(lambda inv: inv.pos_order_id):
                add_line(line, line.product_uom_qty, line.price_unit)

        total_general_achat = sum(c['total_achat'] for c in report_data.values())
        total_general_vente = sum(c['total_vente'] for c in report_data.values())
        total_general_marge = total_general_vente - total_general_achat

        return {
            'report_data': report_data,
            'total_general_achat': total_general_achat,
            'total_general_vente': total_general_vente,
            'total_general_marge': total_general_marge,
            'total_vente': total_vente,
        }

    # -------------------------------------------------------
    #  Action du wizard (choix du bon rapport)
    # -------------------------------------------------------
    def generate_report(self):
        self.ensure_one()

        if self.sale_src == 'pos':
            report_ref = 'custom_B_and_B.action_report_turn_over_pos'
        elif self.sale_src == 'sale':
            report_ref = 'custom_B_and_B.action_report_turn_over_sale'
        else:
            report_ref = 'custom_B_and_B.action_report_turn_over'

        return self.env.ref(report_ref).report_action(self)