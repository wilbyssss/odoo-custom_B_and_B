from odoo import models, fields, api

class ReportPosOrder(models.Model):
    _inherit = 'report.pos.order'
    
    team_id = fields.Many2one(
        'crm.team',
        string='Équipe Commerciale',
        readonly=True
    )
    
    def _select(self):
        # Récupérer l'équipe commerciale de l'utilisateur
        return super(ReportPosOrder, self)._select() + ", us.sale_team_id as team_id"
    
    def _from(self):
        # Ajouter la jointure avec res_users
        return super(ReportPosOrder, self)._from() + " LEFT JOIN res_users us ON (s.user_id = us.id)"
    
    def _group_by(self):
        return super(ReportPosOrder, self)._group_by() + ", us.sale_team_id"