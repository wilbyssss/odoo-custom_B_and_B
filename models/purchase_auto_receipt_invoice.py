from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    allow_auto_validation_purchase_order = fields.Boolean(
        string="Confirmation automatique des réceptions",
        help="Si activé, les réceptions seront automatiquement confirmées "
             "lors de la validation du bon de commande",
        config_parameter='purchase.allow_auto_validation_purchase_order'
    )
    
    allow_auto_invoice = fields.Boolean(
        string="Création et confirmation automatique des factures",
        help="Si activé, les factures seront créées et validées automatiquement après la réception du bon de commande.",
        config_parameter='account.move.allow_auto_invoice'
    )


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        
        auto_validate = self.env['ir.config_parameter'].sudo().get_param(
            'purchase.allow_auto_validation_purchase_order'
        )
        auto_create_invoice = self.env['ir.config_parameter'].sudo().get_param(
            'account.move.allow_auto_invoice'
        )
        
        if auto_validate:
            for picking in self.picking_ids.filtered(lambda p: p.state == 'assigned'):
                # Remplir automatiquement les quantités faites
                for move in picking.move_ids_without_package:
                    move.quantity_done = move.product_uom_qty
                
                # Valider la réception
                try:
                    picking.button_validate()
                except Exception as e:
                    self.env['ir.logging'].sudo().create({
                        'name': 'Auto-validation réception',
                        'type': 'server',
                        'level': 'warning',
                        'message': f"Erreur lors de la validation automatique: {str(e)}",
                        'path': 'purchase.order',
                        'func': 'button_confirm',
                    })
        
        # Création et validation automatique des factures
        if auto_create_invoice:
            try:
                # Créer la facture
                invoice = self.action_create_invoice()
                
                # Si action_create_invoice retourne une action, récupérer la facture créée
                if isinstance(invoice, dict) and 'res_id' in invoice:
                    invoice_id = self.env['account.move'].browse(invoice['res_id'])
                else:
                    # Sinon chercher la dernière facture créée pour ce bon de commande
                    invoice_id = self.invoice_ids.filtered(lambda inv: inv.state == 'draft')
                
                # Valider la facture
                if invoice_id:
                    for inv in invoice_id:
                        if not inv.invoice_date:
                            inv.invoice_date = fields.Date.today()
                        inv.action_post()
                        
            except Exception as e:
                self.env['ir.logging'].sudo().create({
                    'name': 'Auto-création/validation facture',
                    'type': 'server',
                    'level': 'warning',
                    'message': f"Erreur lors de la création/validation automatique de la facture: {str(e)}",
                    'path': 'purchase.order',
                    'func': 'button_confirm',
                })
        
        return res