from odoo import models, api, fields
from odoo.exceptions import ValidationError

class PurchaseOrderLine(models.Model):
   _inherit = 'purchase.order.line'

   @api.onchange('price_unit', 'product_id')
   def _onchange_check_purchase_price(self):
    if self.product_id and self.price_unit:
        if self.product_id.lst_price > 0 and self.price_unit >= self.product_id.lst_price:
            return {
                'warning': {
                    'title': 'Attention : Prix d\'achat supérieur au prix de vente',
                    'message': (
                        f"Le prix d'achat du produit ({self.product_id.display_name}) est supérieur ou égal"
                        f"à son prix de vente."
                        f"Cela peut affecter votre marge bénéficiaire."
                    )
                }
            }
   @api.constrains('price_unit', 'product_id')
   def _check_purchase_vs_sale_price(self):
        for line in self:
            if not line.product_id or not line.price_unit:
                continue

            if line.product_id.lst_price > 0 and line.price_unit >= line.product_id.lst_price:
                raise ValidationError(
                    f"Impossible de valider le bon de commande :\n\n"
                    f"Produit : {line.product_id.display_name}\n"
                    f"Prix d'achat : {line.price_unit:.2f}\n"
                    f"Prix de vente : {line.product_id.lst_price:.2f}\n\n"
                    f"Le prix d'achat doit être inférieur au prix de vente."
                )
