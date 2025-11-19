from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    section_id = fields.Many2one(
        'product.section',
        string='Rayon'
    )

    def _get_next_sequence(self, prefix):
        """
        Trouve la séquence la plus élevée dans les DERNIERS 4 CHIFFRES
        des codes produits qui commencent par le prefix.
        """
        existing_product = self.search([('default_code', 'like', prefix + '%')])
        max_seq = 0
        for prod in existing_product:
            code = prod.default_code or ''
            if not code.startswith(prefix):
                continue
            suffix = code[-4:]
            if suffix.isdigit():
                num = int(suffix)
                max_seq = max(max_seq, num)
        return str(max_seq + 1).zfill(4)

    @api.onchange('section_id')
    def _onchange_section_id(self):
        """Génère automatiquement le code produit quand on choisit le rayon."""
        if not self.section_id:
            return

        # Retirer le tiret du code du rayon
        rayon_code_clean = (self.section_id.code or '').replace('-', '')

        # Calcul de la séquence
        next_seq = self._get_next_sequence(rayon_code_clean)
        self.default_code = rayon_code_clean + next_seq
    @api.model
    def create(self, vals):
        """Sécurisation au cas où le code n'est pas défini en création."""
        product = super().create(vals)

        if not product.default_code and product.section_id:
            rayon_code_clean = (product.section_id.code or '').replace('-', '')
            next_seq = product._get_next_sequence(rayon_code_clean)
            product.write({'default_code': rayon_code_clean + next_seq})

        return product
