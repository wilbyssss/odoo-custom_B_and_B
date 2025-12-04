odoo.define('custom_B_and_B.PosSaleLink', function (require) {
    'use strict';

    const models = require('point_of_sale.models');
    const OrderSuper = models.Order.prototype;

    models.Order = models.Order.extend({

        initialize: function (attributes, options) {
            OrderSuper.initialize.call(this, attributes, options);
            this.sale_order_id = this.sale_order_id || false;
        },

        export_as_JSON: function () {
            const json = OrderSuper.export_as_JSON.call(this);
            json.sale_order_id = this.sale_order_id || false;
            return json;
        },

        set_sale_order: function(sale_order_id) {
            this.sale_order_id = sale_order_id;
        },
    });
});
