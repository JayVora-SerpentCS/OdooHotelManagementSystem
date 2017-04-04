odoo.define("pos_receipt.pos_receipt",function (require) {

    var core = require('web.core');
    var Model = require('web.DataModel');
    var screens = require('point_of_sale.screens');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var models = require('point_of_sale.models');
    var data = require('web.data');
    var chrome = require('point_of_sale.chrome');
    var pop_up = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var QWeb = core.qweb;
    var _t = core._t;

    var SendToKitchenButton = PosBaseWidget.extend({
        template: 'SendToKitchenButton',
    });

    var CustomerReceiptButton = PosBaseWidget.extend({
        template: 'CustomerReceiptButton',
    });

    var KitchenReceiptButton = PosBaseWidget.extend({
        template: 'KitchenReceiptButton',
    });

    var AddSequence = PosBaseWidget.extend({
        template: 'AddSequence',
    })

    models.PosModel.prototype.models.push({
        model:  'pos.category',
        fields: ['id','name','parent_id','child_id','image'],
        domain: null,
        loaded: function(self, categories){
            self.categories = categories;
            var pos_category_model = new Model('pos.category');
            pos_category_model.call("get_root_of_category").done(function(root_category_data){
                self.root_category = root_category_data;
            });
        },
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        delete_current_order: function(){
            var order = this.get_order();
            var posOrderModel = new Model('pos.order');
            if (order) {
                var self = this;
                if(order.attributes.id){
                    posOrderModel.call("close_order", [[order.attributes.id]]).then(function(callback){
                        if(callback){
                            order.destroy({'reason':'abandon'});
//                            if(self.get('orders').last()){
//                                self.set({ selectedOrder: self.get('orders').last() });
//                            }
                        }else if(! callback){
                            self.gui.show_popup('alert',{
                                title:_t('Warning !'),
                                warning_icon : true,
                                body: _t('Can not remove order.'),
                            });
                        }
                    },function(err,event) {
                        event.preventDefault();
                        order.destroy({'reason':'abandon'});
                    });
                }else{
                    var self = this;
                    var table_details = order.attributes.table_data;
                    var restaurant_table_model =  new Model('restaurant.table');
                    if(table_details != undefined){
                         restaurant_table_model.call("remove_table_order", [table_details]).done(function(callback){});
                    }
                    order.destroy({'reason':'abandon'});
                }
            }
        },

    });

    chrome.Chrome.include({
        build_widgets: function(){
            this._super();
            this.do_call_recursive();
        },
        do_call_recursive: function(){
            var self = this;
            var order_ids = [];
            var posOrderModel = new Model('pos.order');
            _.each(this.pos.attributes.orders.models, function(order){
                if(order.attributes.id){
                    order_ids.push(order.attributes.id);
                    clearInterval(self[order.uid]);
                    $("span[data-uid="+order.uid+ "]").closest("span").css({"visibility": "visible"});
                }
            });
            if(order_ids != []){
                posOrderModel.call("get_done_orderline", [order_ids]).then(function(callback){
                    _.each(self.pos.attributes.orders.models, function(order){
                        if(callback){
                            _.each(callback, function(ord){
                                if(ord.id == order.attributes.id){
                                    var set = false;
                                    self[order.uid] = setInterval(function() {
                                        $("span[data-uid="+order.uid+ "]").closest("span").css({
                                            "visibility": set ? "hidden" : "visible",
                                        });
                                        set = !set;
                                    }, 800); 
                                }
                            });
                        }
                    });
                },function(err,event) {
                    event.preventDefault();
                });
                setTimeout(function() { self.do_call_recursive() },10000)
            }else{
                setTimeout(function() { self.do_call_recursive() },10000)
            }
        },
    });

    var SquencePopupWidget = pop_up.extend({
        template:'SquencePopupWidget',
        show: function(options){
            options = options || {};
            var self = this;
            this._super();
            this.options = options;
            this.title = options.title;
            this.category_data = options.category_data
            this.send_to_kitchen = options.send_to_kitchen || false;
            this.orderlines = [];
            this.orderlines = self.pos.get('selectedOrder').orderlines.models;
            this.renderElement();
            self.hotkey_handler = function(event){
                if(event.which === 27){
                    self.gui.close_popup();
                }
            };
            $('body').on('keyup',self.hotkey_handler);
        },
        click_confirm: function(){
            this.gui.close_popup();
            if( this.options.confirm ){
                this.options.confirm.call(this);
            }
        },
        close:function(){
            this._super();
            $('body').off('keyup',this.hotkey_handler);
        },
    });
    gui.define_popup({name:'sequence_popup', widget: SquencePopupWidget});

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function() {
            var self =this
            self.set({
                'id': null,
            })
            _super_order.initialize.apply(this,arguments);
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this,arguments);
            var self = this;
            self.attributes.id = json.id;
        },
        add_product: function(product, options){
            this._printed = false;
            _super_order.add_product.apply(this,arguments);
        },
        export_as_JSON : function(json) {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            var self = this;
            json.id =  self.attributes.id;
            json.creation_date =  self.validation_date || self.creation_date;
            return json;
        },
    });

    var _super_order_line = models.Orderline.prototype;
    var temporary_sequence_number = 1;
    models.Orderline = models.Orderline.extend({
        initialize: function() {
            this.temporary_sequence_number = temporary_sequence_number++;
            this.sequence_number = 1;
            _super_order_line.initialize.apply(this,arguments);
        },
        init_from_JSON: function(json) {
            _super_order_line.init_from_JSON.apply(this,arguments);
            var self = this;
            self.line_id = json.line_id;
            self.order_line_state_id = json.order_line_state_id
        },
        set_line_id : function(line_id){
            this.line_id = line_id;
            this.trigger('change',this);
        },
        export_as_JSON : function(json) {
            var json = _super_order_line.export_as_JSON.apply(this,arguments);
            var self = this;
            json.line_id =  self.line_id;
            json.order_line_state_id = 1
            return json;
        },
    });

    var ActionpadWidget = PosBaseWidget.extend({
        template: 'ActionpadWidget',
        init: function(parent, options) {
            var self = this;
            this._super(parent, options);
            this.pos.bind('change:selectedClient', function() {
                self.renderElement();
            });
        },
        renderElement: function() {
            var self = this;
            $('.pay').unbind('click').bind('click',function(){
                var currentOrder = self.pos.get('selectedOrder');
                currentOrder.kitchen_receipt = false;
                currentOrder.customer_receipt = false;
                self.gui.show_screen('payment');
            });
            this._super();
        }
    });

    screens.ProductScreenWidget.include({
        start: function(){
            var self = this;
            this._super();
            this.actionpad = new ActionpadWidget(this,{});
            this.actionpad.replace(this.$('.placeholder-ActionpadWidget'));
            
            this.SendToKitchenButton = new SendToKitchenButton(this,{});
            this.SendToKitchenButton.appendTo(this.$('.placeholder-OptionsListWidget .option_list_box_container'));
            
            this.CustomerReceiptButton = new CustomerReceiptButton(this,{});
            this.CustomerReceiptButton.appendTo(this.$('.placeholder-OptionsListWidget .option_list_box_container'));
            
            this.KitchenReceiptButton = new KitchenReceiptButton(this,{});
            this.KitchenReceiptButton.appendTo(this.$('.placeholder-OptionsListWidget .option_list_box_container'));
            
            this.AddSequence = new AddSequence(this,{});
            this.AddSequence.appendTo(this.$('.placeholder-OptionsListWidget .option_list_box_container'));

            this.$(".send_to_kitchen_button").on('click',function(){
                self.send_to_kitchen();
            });
            
            this.$(".customer_receipt_button").on('click',function(){
                self.customer_receipt();
            });
            
            this.$(".kitchen_receipt_button").on('click',function(){
                self.kitchen_receipt();
            });
            
            this.$(".add_sequence").on('click',function(){
                self.add_sequence();
            });
        },
        send_to_kitchen : function(){
            var self = this;
            if(self.pos.attributes.selectedOrder.orderlines.models == ''){
                self.gui.show_popup('alert',{
                     title:_t('Warning !'),
                     body: _t('Can not create order which have no order line.'),
                });
                return false;
            }else{
                var order = [];
                var current_order = this.pos.get_order();
                var posOrderModel = new Model('pos.order');
                order.push({'data':current_order.export_as_JSON()})
                posOrderModel.call('create_from_ui',[order, true]).then(function(callback){
                   current_order.attributes.id = callback[0];
                   for( idx in current_order.orderlines.models){
                       current_order.orderlines.models[idx].line_id = callback[1][idx];
                       current_order.orderlines.models[idx].set_line_id(callback[1][idx]);
                   }
                },function(err,event) {
                    event.preventDefault();
                });
                setTimeout(function(){
                    self.gui.show_popup('alert',{
                        title:_t('Successful'),
                        warning_icon : false,
                        body: _t('Order send to the kitchen successfully!'),
                   });
                },300);
            }
        },
        kitchen_receipt : function(){
            var self = this;
            var currentOrder = self.pos.get('selectedOrder');
            if(self.pos.attributes.selectedOrder.orderlines.models == ''){
                self.gui.show_popup('alert',{
                    title:_t('Warning !'),
                    body: _t('Can not Print order which have no order line.'),
               });
               return false;
            }else{
                var currentOrder = self.pos.get('selectedOrder');
               // self.create_from_ui(currentOrder.export_as_JSON(),true,false);
                currentOrder.kitchen_receipt = true;
                currentOrder.customer_receipt = false;
                _.each(currentOrder.orderlines.models, function(order_line){
                    order_line.categ_name = "All";
                    order_line.product_name = order_line.product.display_name;
                    order_line.print_qty = order_line.quantity;
                    order_line.print = true;
                    order_line.ol_flag = false;
                });
                if(self.pos.config.iface_print_via_proxy){
                    var receipt = currentOrder.export_for_printing();
                    self.pos.proxy.print_receipt(QWeb.render('kitchen_receipt',{
                        receipt: receipt,
                        widget: self,
                        order:currentOrder,
                        orderlines: currentOrder.orderlines.models,
                    }));
                }else{
                    self.gui.show_screen('receipt');
                }
            }
        },
        customer_receipt : function(){
            var self = this;
            if(self.pos.attributes.selectedOrder.orderlines.models == ''){
                self.gui.show_popup('alert',{
                    title:_t('Warning !'),
                    warning_icon : true,
                    body: _t('Can not Print order which have no order line.'),
                });
                return false;
            }else{
                
                var currentOrder = self.pos.get('selectedOrder');
                currentOrder.kitchen_receipt = false;
                currentOrder.customer_receipt = true;
                if(self.pos.config.iface_print_via_proxy){
                    var receipt = currentOrder.export_for_printing();
                    self.pos.proxy.print_receipt(QWeb.render('XmlReceipt',{
                        widget: self,
                        pos:self.pos,
                        receipt: receipt,
                        order:currentOrder,
                        orderlines: currentOrder.orderlines.models,
                        paymentlines: currentOrder.get_paymentlines(),
                    }));
                }else{
                   self.gui.show_screen('receipt');
                }
            }
        },
        category_data : function(){
            var self = this;
            var currentOrder = self.pos.get('selectedOrder');
            var duplicate_root_category_id = [];
            var res = [];
            _.each(self.pos.get('selectedOrder').orderlines.models,function(line){
                var root_category_id;
                var root_category_name;
                if(self.pos.root_category[line.product.pos_categ_id[0]] == undefined){
                    root_category_id = 'Undefined';
                    root_category_name = 'Undefined'
                }else if( ! self.pos.root_category[line.product.pos_categ_id[0]].root_category_name){
                    root_category_id = self.pos.root_category[line.product.pos_categ_id[0]].categ_id;
                    root_category_name = self.pos.root_category[line.product.pos_categ_id[0]].categ_name;
                }else{
                    root_category_id = self.pos.root_category[line.product.pos_categ_id[0]].root_category_id;
                    root_category_name = self.pos.root_category[line.product.pos_categ_id[0]].root_category_name;
                }
                if(duplicate_root_category_id.indexOf(root_category_id) == -1){
                    duplicate_root_category_id.push(root_category_id);
                    res.push({'id':root_category_id,'name':root_category_name,'data':[{'product':line.product,'qty':line.quantity,'sequence_number':line.sequence_number,'temporary_sequence_number':line.temporary_sequence_number}]})
                }else{
                    _.each(res,function(record){
                        if(record['id'] == root_category_id){
                            product_categ_data = [];
                            product_categ_data = record['data'];
                            product_categ_data.push({'product':line.product,'qty':line.quantity,'sequence_number':line.sequence_number,'temporary_sequence_number':line.temporary_sequence_number});
                            record['data'] = product_categ_data;
                        }
                    });
                }
            });
            return res;
        },
        add_sequence : function(){
            var self = this;
            if(self.pos.attributes.selectedOrder.orderlines.models == ''){
                self.gui.show_popup('alert',{
                    title:_t('Warning !'),
                    warning_icon : true,
                    body: _t('Can not create order which have no order line.'),
                });
                return false;
            }else{
                self.gui.show_popup('sequence_popup',{
                    title:_t('Orderline Sequence'),
                    send_to_kitchen :true,
                    category_data:self.category_data(),
                    'confirm': function(value) {
                        var dict = {}
                        $('#sequence_data tr input').each(function(index){
                             var temporary_sequence_number_value = $(this).attr('temporary_sequence_number');
                             dict[temporary_sequence_number_value] = $("#sequence_data tr input[temporary_sequence_number="+ temporary_sequence_number_value +"]").val()
                        })
                        _.each(self.pos.get('selectedOrder').orderlines.models,function(line){
                            line.sequence_number = parseInt(dict[line.temporary_sequence_number])
                        });
                        self.pos.get('selectedOrder').orderlines.models.sort(function(a, b){
                            return a['sequence_number'] - b['sequence_number'];
                        });
                    },
                });
            }
        },
    });

    screens.NumpadWidget.include({
        clickDeleteLastChar: function() {
            var self = this;
            var order = this.pos.get('selectedOrder');
            if(order.selected_orderline != undefined){
                if(order.selected_orderline.line_id && this.state.get('mode') != 'price' && this.state.get('mode') != 'discount'){
                     (new Model('pos.order.line')).get_func('orderline_state_id')(order.selected_orderline.line_id,order.attributes.id).then(function(state_id){
                         if(state_id == 1){
                             self.pos_orderline_dataset = new data.DataSetSearch(self, 'pos.order.line', {}, []);
                             self.pos_orderline_dataset.unlink([order.selected_orderline.line_id]);
                             return self.state.deleteLastChar();
                         }else if(state_id == 'cancel'){
                             return self.state.deleteLastChar();
                         }else if(state_id != 1){
                             self.gui.show_popup('alert',{
                                 title:_t('Warning'),
                                 warning_icon : true,
                                 body: _t('Current orderline is not remove'),
                             });
                             return false;
                         }
                     });
                 }else{
                     return self.state.deleteLastChar();
                 }
             }else{
                 return self.state.deleteLastChar();
             }
        },
    });

    screens.ReceiptScreenWidget.include({
        click_back: function() {
            this.gui.show_screen('products');
        },
        show: function(){
            this._super();
            var self = this;
            var order = this.pos.get_order()
            var is_kitchen = order.kitchen_receipt;
            if(!is_kitchen){
                if(! order.customer_receipt){
                    this.$('.next').show();
                    this.$('.back').hide();
                    this.$('.change-value').parent().show();
                }else{
                    this.$('.next').hide();
                    this.$('.change-value').parent().hide();
                    this.$('.back').show();
                }
            }else{
                this.$('.next').hide();
                this.$('.change-value').parent().hide();
            }
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.$('.back').click(function(){
                self.click_back();
            });
        },
    });

    var splitBillScreenWidget;
    var pos_config_dataset = new data.DataSet(this,'pos.config',{},[]);
    pos_config_dataset.call('check_is_pos_restaurant').done(function(result){
        if(result){
            if(result){
                _.each(gui.Gui.prototype.screen_classes,function(screen_class){
                    if(screen_class.name == "splitbill"){
                        splitBillScreenWidget = screen_class;
                    }
                });
                splitBillScreenWidget.widget.include({
                    renderElement: function(){
                        var order = this.pos.get_order();
                        if(!order){
                            return;
                        }
                        order.kitchen_receipt = false;
                        order.customer_receipt = false;
                        this._super();
                    },
                    pay: function(order,neworder,splitlines){
                        var orderlines = order.get_orderlines();
                        var empty = true;
                        var full  = true;
                        for(var i = 0; i < orderlines.length; i++){
                            var id = orderlines[i].id;
                            var split = splitlines[id];
                            if(!split){
                                full = false;
                            }else{
                                if(split.quantity){
                                    empty = false;
                                    if(split.quantity !== orderlines[i].get_quantity()){
                                        full = false;
                                    }
                                }
                            }
                        }
                        if(empty){
                            return;
                        }
                        if(full){
                            neworder.destroy({'reason':'abandon'});
                            this.gui.show_screen('payment');
                        }else{
                            for(var id in splitlines){
                                var split = splitlines[id];
                                var line  = order.get_orderline(parseInt(id));
                                line.set_quantity(line.get_quantity() - split.quantity);
                                if(Math.abs(line.get_quantity()) < 0.00001){
                                    order.remove_orderline(line);
                                }
                                if(line.line_id != undefined){
                                    self.pos_line = new data.DataSetSearch(self, 'pos.order.line');
                                    self.pos_line.unlink(line.line_id)
                                }
                                delete splitlines[id];
                            }
                            neworder.set_screen_data('screen','payment');
                            // for the kitchen printer we assume that everything
                            // has already been sent to the kitchen before splitting 
                            // the bill. So we save all changes both for the old 
                            // order and for the new one. This is not entirely correct 
                            // but avoids flooding the kitchen with unnecessary orders. 
                            // Not sure what to do in this case.
                            if ( neworder.saveChanges ) { 
                                order.saveChanges();
                                neworder.saveChanges();
                            }
                            neworder.set_customer_count(1);
                            order.set_customer_count(order.get_customer_count() - 1);
                          
                            this.pos.get('orders').add(neworder);
                            this.pos.set('selectedOrder',neworder);
                            this.gui.show_screen('payment');
                        }
                    },
                    show : function(){
                        var self = this;
                        screens.ScreenWidget.prototype.show.call(this)
                        this.renderElement();
                        var order = this.pos.get_order();
                        var neworder = new models.Order({},{
                            pos: this.pos,
                            temporary: true,
                        });
                        neworder.set('client',order.get('client'));
                        neworder.set('pflag',order.get('pflag'));
                        neworder.set('parcel',order.get('parcel'));
                        neworder.set('pricelist_id',order.get('pricelist_id'));
                        neworder.set('phone',order.get('phone'));
                        neworder.set('partner_id',order.get('partner_id'));
                        neworder.set('driver_name',order.get('driver_name'));
                        neworder.set('creationDate',order.get('creationDate'));
                        neworder.set('table_data',order.get('table_data'));
                        neworder.set('table',order.get('table'));
                        neworder.set('table_ids',order.get('table_ids'));
                        neworder.set('split_order',true);
                        
                        var splitlines = {};
                        this.$('.orderlines').on('click','.orderline',function(){
                            var id = parseInt($(this).data('id'));
                            var $el = $(this);
                            self.lineselect($el,order,neworder,splitlines,id);
                        });
                        this.$('.paymentmethods .button').click(function(){
                            self.pay(order,neworder,splitlines);
                        });
                        this.$('.back').unbind('click').bind('click',function(){
                            neworder.destroy({'reason':'abandon'});
                            self.gui.show_screen(self.previous_screen);
                        });
                    },
                });
            }
        }
    });

});
