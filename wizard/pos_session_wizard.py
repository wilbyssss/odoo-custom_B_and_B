from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError

class PosSessionBackDateWizard(models.TransientModel):
    _name = 'pos.session.backdate.wizard'
    _description = "Assistant de modification de la date de session"

    session_id = fields.Many2one('pos.session', string="Session", required=True)
    manual_date = fields.Datetime(string="Nouvelle date", required=True, default=fields.Datetime.now)

    def apply_manual_date(self):
        """Applique la nouvelle date aux commandes et à la session"""
        self.ensure_one()
        session = self.session_id

        if not session.allow_manual_session_date:
            raise UserError("La modification de la date n’est pas autorisée pour ce point de vente.")

        start_date = self.manual_date
        end_date = start_date + timedelta(minutes=30)

        # Mise à jour des dates de la session
        session.write({
            'manual_date': start_date,
            'start_at': start_date,
            'stop_at': end_date,
        })

        # Mise à jour de la date de commande
        orders = self.env['pos.order'].search([('session_id', '=', session.id)])
        orders.write({'date_order': start_date})

        return {'type': 'ir.actions.act_window_close'}

