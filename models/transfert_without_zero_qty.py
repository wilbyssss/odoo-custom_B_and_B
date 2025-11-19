from odoo import fields, models, api
from odoo.exceptions import ValidationError

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    @api.onchange('location_id', 'product_uom_qty', 'product_id')
    def _onchange_check_stock_in_location(self):
        # Vérifier d'abord la quantité = 0
        if self.product_uom_qty == 0 and self.product_id:
            return {
                'warning': {
                    'title': 'Attention : Quantité nulle',
                    'message': 'Vous devez spécifier une quantité à transférer.'
                }
            }
        
        # Vérifier le stock uniquement pour les emplacements internes
        if (self.location_id and self.product_id and self.product_uom_qty > 0 
            and self.location_id.usage == 'internal'):
            
            # Réccup&ration du stock disponible
            available_qty = self.env['stock.quant']._get_available_quantity(
                self.product_id, 
                self.location_id
            )
            
            if available_qty <= 0:
                return {
                    'warning': {
                        'title': 'Attention : Stock insuffisant',
                        'message': (
                            f"Le produit '{self.product_id.display_name}' a un stock de {available_qty} "
                            f"dans l'emplacement '{self.location_id.complete_name}'.\n\n"
                            f"Quantité demandée : {self.product_uom_qty}\n"
                            f"Veuillez vérifier le stock disponible."
                        )
                    }
                }
            elif self.product_uom_qty > available_qty:
                return {
                    'warning': {
                        'title': 'Attention : Quantité supérieure au stock',
                        'message': (
                            f"Produit : {self.product_id.display_name}\n"
                            f"Stock disponible : {available_qty}\n"
                            f"Quantité demandée : {self.product_uom_qty}\n\n"
                            f"Il manque {self.product_uom_qty - available_qty} unités."
                        )
                    }
                }
    
    @api.constrains('location_id', 'product_id', 'product_uom_qty', 'state')
    def _check_stock_availability(self):
        for move in self:
            # Vérifier uniquement les mouvements sortants d'emplacements internes
            if (move.state in ['assigned', 'confirmed'] 
                and move.location_id.usage == 'internal' 
                and move.product_id 
                and move.product_uom_qty > 0):
                available_qty = self.env['stock.quant']._get_available_quantity(
                    move.product_id, 
                    move.location_id
                )
                
                if available_qty < move.product_uom_qty:
                    raise ValidationError(
                        f"Stock insuffisant pour le transfert :\n\n"
                        f"Produit : {move.product_id.display_name}\n"
                        f"Emplacement : {move.location_id.complete_name}\n"
                        f"Stock disponible : {available_qty}\n"
                        f"Quantité demandée : {move.product_uom_qty}\n\n"
                        f"Il manque {move.product_uom_qty - available_qty} unités."
                    )