from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_manual_session_date = fields.Boolean(
        string="Autoriser la modification de la date de la session",
        related='pos_config_id.allow_manual_session_date',
        readonly=False
    )
class PosConfig(models.Model):
    _inherit = 'pos.config'

    allow_manual_session_date = fields.Boolean(
        string="Autoriser la modification de la date de la session",
        help="Permet de modifier la date des ventes lors de la saisie différée."
    )
class PosSession(models.Model):
    _inherit = 'pos.session'

    manual_date = fields.Datetime(
        string="Date réelle de l'opération",
        help="Permet de définir la date réelle de la vente lorsque la saisie est faite ultérieurement."
    )

    allow_manual_session_date = fields.Boolean(
        related='config_id.allow_manual_session_date',
        string="Autoriser la modification de la date",
        store=False
    )

    def action_open_backdate_wizard(self):
        """Ouvre le wizard de modification de date si autorisé"""
        self.ensure_one()
        if not self.allow_manual_session_date:
            raise fields.UserError("La modification de la date n’est pas autorisée pour ce point de vente.")
        return {
            'name': "Modifier la date de session",
            'type': 'ir.actions.act_window',
            'res_model': 'pos.session.backdate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_session_id': self.id},
        }
