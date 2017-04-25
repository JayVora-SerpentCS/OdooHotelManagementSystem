odoo.define("pos_options_bar.pos_options_bar",function (require) {
"use strict";

    var core = require('web.core');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');

    var QWeb = core.qweb;
    var _t = core._t;

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this,arguments);
            this.price_list_container_minimize_maximize = _t("minimize");
        },
    });

    screens.ProductScreenWidget.include({
        start: function(){
            var self = this;
            this._super();
            self.$("div.options_list_container_min_max").on('click',function(){
                if(self.pos.get('selectedOrder').price_list_container_minimize_maximize == _t('minimize')){
                    self.$(".set_min_max_button").removeClass("fa-plus-square");
                    self.$(".set_min_max_button").addClass("fa-minus-square");
                    self.$(".option_list_box").removeClass('oe_hidden');
                    self.pos.get('selectedOrder').price_list_container_minimize_maximize = _t("maximize");
                }else{
                    self.$(".set_min_max_button").removeClass("fa-minus-square");
                    self.$(".set_min_max_button").addClass("fa-plus-square");
                    self.$(".option_list_box").addClass('oe_hidden');
                    self.pos.get('selectedOrder').price_list_container_minimize_maximize = _t("minimize");
                }
            });
        },
        show: function(){
            this._super();
            var self =this;
            if(self.pos.get('selectedOrder').price_list_container_minimize_maximize == _t('minimize')){
                self.$(".set_min_max_button").removeClass("fa-minus-square");
                self.$(".set_min_max_button").addClass("fa-plus-square");
                $(".option_list_box").addClass('oe_hidden');
            }else{
                self.$(".set_min_max_button").removeClass("fa-plus-square");
                self.$(".set_min_max_button").addClass("fa-minus-square");
                $(".option_list_box").removeClass('oe_hidden');
            }
        },
    });

});
