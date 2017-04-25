odoo.define("pos_folio.pos_folio",function (require) {
    
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var Popup = require('point_of_sale.popups');
    var chrome = require('point_of_sale.chrome');
    var keyboard = require('point_of_sale.keyboard');
    var gui = require('point_of_sale.gui');
    var Model = require('web.DataModel');
    
    var QWeb = core.qweb;
    var _t   = core._t;

    
    var FolioButtonWidget = screens.ActionButtonWidget.extend({
        template: 'FolioButton',
        button_click: function(){
            var self = this;
            if(self.pos.get_order().orderlines.models == ''){
                self.gui.show_popup('alert',{
                     title:_t('Warning !'),
                     body: _t('Can not create order which have no order line.'),
                });
                return false;
            }else{
                self.gui.show_popup('folio_popup',{
                    title:_t('Folio'),
                });
            }
        },
    });
    
    screens.define_action_button({
        'name': 'folio_button',
        'widget': FolioButtonWidget,
    });
    
    
    var FolioPopupWidget = Popup.extend({
        template:'FolioPopupWidget',
        show: function(options){
            options = options || {};
            var self = this;
            this._super();
            this.title = options.title;
            this.renderElement();
            this.$('.footer .ok').click(function(){
                if($("#folio_number_txt").val().length == 0 ){
                    var warning_icon = true;
                    var message = _t("Folio Number is Empty,Please Enter Folio Number");
                    self.pos.open_alert_dialog(message,warning_icon);
                    return false;
                }else{
                    self.gui.close_popup();
                    self.take_folio(self.pos,self.pos.callable);
                }
            });
            if(! self.pos.config.iface_vkeyboard){
                $('#folio_number_txt').focus();
            }
            if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
                this.chrome.widget.keyboard.connect($('#folio_number_txt'));
            }
            this.$('.footer .close').click(function(){
                self.gui.close_popup();
            });
            self.hotkey_handler = function(event){
                if(event.which === 13){
                    self.$('.footer .ok').click();
                }else if(event.which === 27){
                    self.gui.close_popup();
                }
            };
            $('body').on('keyup',self.hotkey_handler);
        },
        take_folio : function(pos,callable){
            var self = this;
            var input_value = $("#folio_number_txt").val();
            //var order = new models.Order({},{ pos: self });
            new Model("hotel.folio").get_func("search_read")
                ([['name', '=', input_value]], 
                        ['id', 'name', 'partner_id']).pipe(
                                function(result) {name
                                    if (result && result.length == 1) {
                                        var order = []
                                        var current_order = self.pos.get_order();
                                        var posOrderModel = new Model('pos.order');
                                        current_order.set_folio_number(result[0].name);
                                        current_order.set_folio_number_id(result[0].id);
                                        current_order.set_client(self.pos.db.get_partner_by_id(result[0].partner_id[0]));
                                        order.push({'data':current_order.export_as_JSON()});
                                        posOrderModel.call('create_from_ui',[order, true]).then(function(callback){
                                           current_order.attributes.id = callback[0];
                                           for( idx in current_order.orderlines.models){
                                               current_order.orderlines.models[idx].line_id = callback[1][idx];
                                               current_order.orderlines.models[idx].set_line_id(callback[1][idx]);
                                           }
                                           current_order.kitchen_receipt = false;
                                           current_order.customer_receipt = true;
                                           if(self.pos.config.iface_print_via_proxy){
                                               var receipt = current_order.export_for_printing();
                                               self.pos.proxy.print_receipt(QWeb.render('XmlReceipt',{
                                                   widget: self,
                                                   pos:self.pos,
                                                   receipt: receipt,
                                                   order:currentOrder,
                                                   orderlines: current_order.orderlines.models,
                                                   paymentlines: current_order.get_paymentlines(),
                                               }));
                                           }else{
                                              self.gui.show_screen('receipt');
                                           }
                                           
                                        },function(err,event) {
                                            event.preventDefault();
                                        });
                                    }
                                    else{
                                        alert('Folio Number Not Found!!!');
                                    }
                                });
        },
        close:function(){
            this._super();
            $('body').off('keyup',this.hotkey_handler);
            if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
                this.chrome.widget.keyboard.hide();
                this.chrome.widget.keyboard.connect($('.searchbox input'));
            }
        },
    });
    gui.define_popup({name:'folio_popup', widget: FolioPopupWidget});
    
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function() {
            this.set({
                'folio_number' : false,
                'folio_number_id' : false,
            })
            _super_order.initialize.apply(this,arguments);
        },
        get_folio_number : function(){
            return this.get('folio_number');
        },
        set_folio_number : function(folio_number){
           this.set('folio_number',folio_number);
        },
        get_folio_number_id : function(){
            return this.get('folio_number_id');
        },
        set_folio_number_id : function(folio_number_id){
           this.set('folio_number_id',folio_number_id);
        },
        export_as_JSON : function(json) {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            var self =this;
            json.folio_id = this.get_folio_number_id();
            return json;
        },
    });
    
    screens.ReceiptScreenWidget.include({
        click_done: function() {
            this.pos.get_order().destroy();
        },
        show: function(){
            this._super();
            var self = this;
            var order = this.pos.get_order()
            var is_kitchen = order.kitchen_receipt;
            var is_folio = order.get_folio_number();
            if(!is_kitchen){
                if(! order.customer_receipt){
                    this.$('.next').show();
                    this.$('.back').hide();
                    this.$('.change-value').parent().show();
                    this.$('.done').hide();
                }else{
                    this.$('.next').hide();
                    this.$('.change-value').parent().hide();
                    this.$('.done').hide();
                    this.$('.back').show();
                    if(is_folio){
                        this.$('.back').hide();
                        this.$('.done').show();
                        self.pos.db.remove_unpaid_order(order);
                    }
                }
            }else{
                this.$('.next').hide();
                this.$('.done').hide();
                this.$('.change-value').parent().hide();
            }
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.$('.done').click(function(){
                self.click_done();
            });
        },
    });
});
