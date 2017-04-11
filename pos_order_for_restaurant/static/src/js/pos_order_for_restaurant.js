odoo.define("pos_order_for_restaurant.pos_order_for_restaurant",function (require) {

    var core = require('web.core');
    var data = require('web.data');
    var chrome = require('point_of_sale.chrome');
    var keyboard = require('point_of_sale.keyboard');
    var gui = require('point_of_sale.gui');
    var Model = require('web.DataModel');
    var models = require('point_of_sale.models');
    var pop_up = require('point_of_sale.popups');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var screens = require('point_of_sale.screens');
    var resturant = require('pos_restaurant.floors');

    var QWeb = core.qweb;
    var _t = core._t;

    var pos_order_model = new Model('pos.order');
    var restaurant_table_dataset = new data.DataSetSearch(self, 'restaurant.table', {}, []);
    var restaurant_table_model =  new Model('restaurant.table');

    var FloorScreenWidget;
    _.each(gui.Gui.prototype.screen_classes,function(screen_class){
        if(screen_class.name == "floors"){
            FloorScreenWidget = screen_class;
        }
    });

    var NumberPopupWidget;
    _.each(gui.Gui.prototype.popup_classes,function(popup_class){
        if(popup_class.name == "number"){
            NumberPopupWidget = popup_class;
        }
    });

    for (var i = 0; i < models.PosModel.prototype.models.length; i++) {
        if(models.PosModel.prototype.models[i].model == 'restaurant.table'){
            models.PosModel.prototype.models.splice(i, 1);
        }
    }

    models.PosModel.prototype.models.push({
        model: 'restaurant.floor',
        fields: ['name','background_color','table_ids','sequence'],
        domain: null,
        loaded: function(self,floors){
            self.floors = floors;
            self.floors_by_id = {};
            for (var i = 0; i < floors.length; i++) {
                floors[i].tables = [];
                self.floors_by_id[floors[i].id] = floors[i];
            }
            // Make sure they display in the correct order
            self.floors = self.floors.sort(function(a,b){ return a.sequence - b.sequence; });
            // Ignore floorplan features if no floor specified.
            self.config.iface_floorplan = !!self.floors.length;
        },
    },{
        model: 'restaurant.table',
        fields: ['name','users_ids', 'capacities','state', 'available_capacities','floor_id','width','height','position_h','position_v','shape','floor_id','color','seats'],
        loaded: function(self, tables_data){
            var tables = [];
            self.table_details = []
            self.tables_by_id = {};
            for (var i = 0; i < tables_data.length; i++) {
                self.tables_by_id[tables_data[i].id] = tables[i];
                var floor = self.floors_by_id[tables_data[i].floor_id[0]];
                if (floor) {
                    floor.tables.push(tables_data[i]);
                    tables_data[i].floor = floor;
                }
            }
            _.each(tables_data, function(item) {
                for(us in item.users_ids){
                    if(item.users_ids[us] == self.session.uid){
                        tables.push([item.id, item.name, item.capacities, item.capacities, item.available_capacities]);
                    }
                }
            });
            self.table_list = tables;
            self.temp_table_list = tables;
            self.all_table = tables_data;
        },
    },{
        model:  'res.partner',
        fields: ['name','street','city','state_id','country_id','vat','phone','zip','mobile','email','barcode','write_date','property_account_position_id'],
        domain: [['customer','=',true]], 
        loaded: function(self,partners){
            self.partners = partners;
            self.partner_list = [];
            _.each(self.partners, function(value) {
                self.partner_list.push(value);
            });
        },
    },{
        model:  'res.users',
        fields: ['name','ean13','company_id'],
        domain:  null,
        loaded: function(self, user_list){
            self.delivery_boy = [];
            _.each(user_list,function(user){
                pos_order_model.call("check_group_pos_delivery_boy",[user.id]).then(function(callback){
                    if(callback){
                        self.delivery_boy.push(user);
                    }
                });
            });
            self.user_list = user_list;
        },
    });

    models.PosModel.prototype.load_new_partners = function(){
        var self = this;
        var def  = new $.Deferred();
        var fields = _.find(this.models,function(model){ return model.model === 'res.partner'; }).fields;
        new Model('res.partner')
            .query(fields)
            .filter([['customer','=',true],['write_date','>',this.db.get_partner_write_date()]])
            .all({'timeout':3000, 'shadow': true})
            .then(function(partners){
                if (self.db.add_partners(partners)) {   // check if the partners we got were real updates
                    _.each(partners,function(partner){
                        self.partner_list.push(partner);
                    });
                    def.resolve();
                } else {
                    def.reject();
                }
            }, function(err,event){ event.preventDefault(); def.reject(); });
        return def;
    }

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function(session, attributes) {
            this.session = session;
            this.pos_session = session;
            return _super_posmodel.initialize.call(this,session,attributes);
        },
        delete_current_order: function(){
            var order = this.get_order();
            if (order) {
                var self = this;
                if(order.attributes.id){
                    pos_order_model.call("close_order", [[order.attributes.id]]).then(function(callback){
                        if(callback){
                            order.destroy({'reason':'abandon'});
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
                    if(table_details != undefined){
                         restaurant_table_model.call("remove_table_order", [table_details]).done(function(callback){
                             order.destroy({'reason':'abandon'});
                         });
                    }else{
                        order.destroy({'reason':'abandon'});
                    }
                }
            }
        },
        set_table: function(table) {
            if (!table) { // no table ? go back to the floor plan, see ScreenSelector
                this.set_order(null);
            } else {
                this.table = table;
                var self = this;
                var orders = this.get_order_list();
                var selection_name= '';
                var reserved_seat = '';
                var selection_id = [];
                var select_tables = [];
                if(table.state == 'reserved'){
                    _.each(orders,function(order){
                        if(order.attributes.table_ids != undefined && order.attributes.table_ids[0] == table.id){
                            self.set({ 'selectedOrder': order });
                        }
                    })
                }
                if(table.state == 'available'){
                    var table_id = parseInt(table.id);
                    selection_id.push(table_id);
                    selection_name += ' ' + table.name +"/" + $("#"+table.id+'_sit_reserv').val();
                    reserved_seat += table.id+ "/" +$("#"+table.id+'_sit_reserv').val()+'_';
                    actual_reserved_seat = parseInt($("#"+table.id+'_sit_reserv').val());
                    select_tables.push({reserver_seat: $("#"+table.id+'_sit_reserv').val(), table_id: table_id});
                    available_seat = table.seating_capacities;
                    var table_vals = {'available_capacities': actual_reserved_seat +  table.available_capacities};
                    if((actual_reserved_seat >  available_seat) || (available_seat == 0) ){
                        self.gui.show_popup('alert',{
                            title:_t('Warning !'),
                            warning_icon : true,
                            body: _t("Table capacity is ") + available_seat + _t(" person you cannot enter more then ") + available_seat + _t(" or less than 1. "),
                        });
                        return false;
                    }
                    if (actual_reserved_seat <= 0 || isNaN(actual_reserved_seat)) {
                        self.gui.show_popup('alert',{
                            title:_t('Warning !'),
                            warning_icon : true,
                            body: _t("You must be add some person in this table"),
                        });
                        return false;
                    }
                    var order = new models.Order({},{pos:this});
                    if (actual_reserved_seat == available_seat) {
                        table_vals['state'] = 'reserved';
                        order.set('creationDate',selection_name);
                        order.set('table',table);
                        order.set('creationDateId', selection_id);
                        order.set('table_ids', selection_id);
                        order.set('table_data', select_tables);
                        order.set('reserved_seat', reserved_seat);
                        if(table.client_detalis != null){
                            order.set_client(self.db.get_partner_by_id(table.client_detalis.id));
                        }
                        self.get('orders').add(order);
                        self.set_order(order );
                        restaurant_table_model.call("write",[[table_id],table_vals]);
                    }else if (actual_reserved_seat != available_seat){
                        order.set('creationDate',selection_name);
                        order.set('table',table);
                        order.set('creationDateId', selection_id);
                        order.set('table_ids', selection_id);
                        order.set('table_data', select_tables);
                        order.set('reserved_seat', reserved_seat);
                        if(table.client_detalis != null){
                            order.set_client(self.db.get_partner_by_id(table.client_detalis.id));
                        }
                        self.get('orders').add(order);
                        self.set_order(order );
                        restaurant_table_model.call("write",[[table_id],table_vals]);
                    }
                }
            }
        },
        //creates a new empty order and sets it as the current order
        add_new_order: function(){
            var order = new models.Order({},{pos:this});
            this.get('orders').add(order);
            this.set('selectedOrder', order);
            return order;
        },
        initialize_table_details : function(floor,re_assign){
            var self = this;
            self.booked_table = [];
            self.empty_table = [];
            return restaurant_table_dataset.read_slice(['name','code','state','users_ids', 'capacities', 'available_capacities','floor_id','width','height','position_h','position_v','shape','floor_id','color',], {'domain': [['floor_id', '!=', false]]}).then(function(table_records){
                self.table_details = [];
                _.each(table_records, function(value) {
                    for(us in value.users_ids){
                        if(value.users_ids[us] == self.session.uid){
                            self.table_details.push(value)
                            if((value.capacities - value.available_capacities) < value.capacities){
                                self.empty_table.push([value.id, value.name, value.capacities, value.capacities - value.available_capacities, value.available_capacities, true,value.floor_id[0],value.state]);
                            }else{
                                self.empty_table.push([value.id, value.name, value.capacities, value.capacities - value.available_capacities, value.available_capacities, false,value.floor_id[0],value.state]);
                            }
                        }
                    }
                });
                if ($('.orders')) {
                    _.each($('.orders')[0].childNodes, function(value) {
                        if($(value).attr('data')){
                            self.booked_table.push([$(value).attr("name"), 
                                                    $(value).attr("name").trim(), 
                                                    $(value).attr("data"),
                                                    $(value).attr('id'),
                                                    $(value)[0].id]);
                        }
                    });
                }
                if(re_assign && self.empty_table.length == 0 && self.option_value == "re_assign_order"){
                    var warning_icon = true;
                    var message = _t("Table is not empty. Please wait!")
                    self.open_alert_dialog(message,warning_icon);
                }
                if(self.booked_table.length < 0 && self.option_value == "merge_order"){
                    var warning_icon = true;
                    var message = _t("There is no more table to merge!");
                    self.open_alert_dialog(message,warning_icon);
                    return false;
                }
                if(floor){
                    self.gui.screen_instances.floors.renderElement();
                    self.gui.show_screen('floors');
                } else if(re_assign ){
                    self.re_assign = re_assign;
                    self.re_assign_table_content();
                }
            });
        },
        re_assign_table_content : function(){
            var self = this;
            $('.reassign_table_screen_content').html($(QWeb.render('select-table', {'table' : self})));
            $('#table_list .input_seat').on('click',function(index){
                $(this).closest('tr').find("input")[0].checked = !$(this).closest('tr').find("input")[0].checked;
                $(this).closest('tr').removeClass('reassign_order_color');
            });
            $('#table_list .field_boolean').on('click',function(index){
                $(this).closest('tr').find("input")[0].checked = !$(this).closest('tr').find("input")[0].checked;
                $(this).closest('tr').removeClass('reassign_order_color');
            });
            $('#table_list tr').on('click',function(){
                if($(this).find("input")[0].checked){
                    $(this).find("input")[0].checked = false;
                    $(this).removeClass('reassign_order_color');
                }else{
                    $(this).find("input")[0].checked = true;
                    $(this).addClass('reassign_order_color');
                }
            });
            self.set_re_assign_table_screen_property();
        },
        set_re_assign_table_screen_property : function(){
            var self = this;
            $(".marge_table").hide();
            if(self.option_value == "merge_order"){
                $("#booked_table_list").hide();
                $( "#booked_table" ).attr( "multiple","multiple");
                $(".marge_table").attr('checked', true);
                $( "#booked_table" ).css({'margin-bottom':'-12px','height':'55px','background':'white'});
                $( "#table_list" ).css({'margin-top':'19px','display':'block'});
                $( "#table_list tr" ).show();
            }else{
                $("#booked_table_list").hide();
                $( "#table_list tr" ).show();
                $( "#table_list" ).css("display","block");
                $(".marge_table").attr('checked', false);
            }
        },
        get_order_list: function() {
            return this.get('orders').models;
        },
        set_textbox_attributes : function(input_name,type_of_popup){
            this.input_name = input_name;
            var self = this;
            if(type_of_popup == 'delivery_order_popup'){
                $('#'+input_name).change(function(e){
                    $("#person_number_txt").val("");
                    _.each(self.partner_list, function(partner) {
                        if(partner.name.toLowerCase() == $('#'+input_name).val().toLowerCase()){
                            if(!partner.phone){
                                $("#person_number_txt").val("");
                            }else{
                                $("#person_number_txt").val(partner.phone);
                            }
                        }
                    });
                });
            }
        },
        open_alert_dialog : function(message,icon){
            var warning_icon = icon;
            var message = message;
            var title = _t('Warning !');
            this.alert_dialog = $(QWeb.render('AlertDialog', {'widget': self,'message': message,'title':title,'warning_icon':warning_icon})).dialog({
                resizable: false,
                height:"auto",
                width:500,
                position: "center",
                modal : 'true',
                open : function(){
                    $(".ui-dialog-titlebar").hide();
                    $(".ui-dialog").css('overflow','hidden');
                    $("body").addClass('hide_over_flow');
                    $(".ui-widget-overlay").height($(document).height()+ 15);
                    set_ui_widget_overlay()
                    $(".ui-dialog").addClass('alert_dialog_warning');
                    $('.ui-dialog-buttonpane').find('button:contains("Ok")').addClass('alert_dialog_button');
                    $(".pincode_dialog_warning").hide();
                    $(".add_customer_dialog_warning").hide();
                },
                close: function( event, ui ) {
                    $( this ).remove();
                    $(".pincode_dialog_warning").show();
                    $(".add_customer_dialog_warning").show();
                    $("body").removeClass('hide_over_flow');
                },
                buttons: {
                    "Ok": function() {
                        $(".ui-dialog-titlebar").show();
                        $(".ui-dialog").removeClass('alert_dialog_warning');
                        $( this ).remove();
                        $("body").removeClass('hide_over_flow');
                        $(".pincode_dialog_warning").show();
                        $(".add_customer_dialog_warning").show();
                    },
                },
            });
        },
      // this is called when an order is removed from the order collection. It ensures that there is always an existing
      // order and a valid selected order
        on_removed_order: function(removed_order,index,reason){
            var order_list = this.get_order_list();
            var self = this;
            if (this.config.iface_floorplan) {
                if( (reason === 'abandon' || removed_order.temporary || this.get('orders').last()) && order_list.length > 0){
                    self.set_order(order_list[index] || order_list[order_list.length -1]);
                }else{
                    // back to the floor plan
                    this.table = null;
                    this.gui.show_screen('floors');
                    this.gui.screen_instances.floors.renderElement();
                }
            } else {
                self.add_new_order();
            }
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function() {
            this.set({
                'parcel': false,
                'driver_name' :false,
                'partner_id' : false,
                'phone' : false,
                'pflag': false,
                'creationDate' : false,
                'table_data':[],
                'reserved_seat':[],
                'table_ids':[],
                'split_order':null,
            })
            _super_order.initialize.apply(this,arguments);
        },
        getDriver: function() {
            if(this.get('driver_name')){
                return this.get('driver_name');
            }else{
                return false;
            }
        },
        getphone: function() {
            if(this.get('phone')){
                return this.get('phone');
            }else{
                return false;
            }
        },
        getFlag: function() {
            if(this.get('pflag')){
                return this.get('pflag');
            }else{
                return false;
            }
        },
        getParcel: function() {
            if(this.get('parcel')){
                return this.get('parcel');
            }else{
                return false;
            }
        },
        get_table_name : function(){
            if(this.get('creationDate')){
                return this.get('creationDate');
            }else{
                return false
            }
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this,arguments);
            var self = this;
            self.attributes.parcel = json.parcel;
            self.attributes.pflag = json.pflag;
            self.attributes.creationDate = json.creationDate;
            self.attributes.reserved_seat = json.reserved_seat;
            self.attributes.table_ids = json.table_ids;
            self.attributes.table_data = json.table_data;
            self.attributes.driver_name = json.driver_name;
            self.attributes.split_order = json.split_order
            if(json.partner_id ){
                _.each(this.pos.partners, function(partner) {
                    if(partner.id == json.partner_id){
                        self.partner_id = partner.name;
                    }
                });
            }
        },
        export_as_JSON : function(json) {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            var self =this;
            json.pflag = this.getFlag();
            json.parcel = this.getParcel();
            json.phone = this.getphone();
            json.driver_name = this.getDriver();
            json.table_id  =(this.attributes.table && !this.attributes.parcel && ! this.getDriver() ) ? this.attributes.table.id : false;
            json.floor     =  (this.attributes.table && !this.attributes.parcel && ! this.getDriver()) ? this.attributes.table.floor.name : false; 
            json.floor_id  =  (this.attributes.table && !this.attributes.parcel && ! this.getDriver()) ? this.attributes.table.floor.id : false;
            json.customer_count = (!this.attributes.parcel && ! this.getDriver()) ? this.customer_count : false;
            json.table_data = (this.attributes.table_data && !this.attributes.parcel && ! this.getDriver() ) ? this.attributes.table_data : [];
            json.creation_date =  self.validation_date || self.creation_date;
            json.creationDate = (this.attributes.creationDate  && !this.attributes.parcel && ! this.getDriver()) ?  this.attributes.creationDate : false;
            json.table_ids = (this.attributes.table_ids  && !this.attributes.parcel && ! this.getDriver()) ?  this.attributes.table_ids : [];
            json.reserved_seat = (this.attributes.reserved_seat  && !this.attributes.parcel && ! this.getDriver()) ?  this.attributes.reserved_seat : [];
            json.split_order = this.attributes.split_order ? this.attributes.split_order : null;
            return json;
        },
        clean_empty_paymentlines: function() {
            var lines = this.paymentlines.models;
            var empty = [];
            for ( var i = 0; i < lines.length; i++) {
               // if (!lines[i].get_amount()) {
                    empty.push(lines[i]);
                //}
            }
            for ( var i = 0; i < empty.length; i++) {
                this.remove_paymentline(empty[i]);
            }
        },
    });

    var AlertPopupWidget = pop_up.extend({
        template:'AlertPopupWidget',
        show: function(options){
            options = options || {};
            var self = this;
            this._super();
            this.message = options.message;
            this.title = options.title;
            this.warning_icon = options.warning_icon,
            this.renderElement();
            this.$('.footer .button').click(function(){
                self.gui.close_popup();
            });
            self.hotkey_handler = function(event){
                if(event.which === 13 || event.which === 27){
                    self.gui.close_popup();
                }
            };
            $('body').on('keyup',self.hotkey_handler);
        },
        close:function(){
            this._super();
            $('body').off('keyup',this.hotkey_handler);
        },
    });
    gui.define_popup({name:'alert2', widget: AlertPopupWidget});

    var ParcelOrderPopupWidget = pop_up.extend({
        template:'ParcelOrderPopupWidget',
        show: function(options){
            options = options || {};
            var self = this;
            this._super();
            this.title = options.title;
            this.renderElement();
            this.$('.footer .ok').click(function(){
                if($("#take_away_txt").val().length == 0 ){
                    var warning_icon = true;
                    var message = _t("Parcel Order is Empty,Please Enter Parcel Order Name");
                    self.pos.open_alert_dialog(message,warning_icon);
                    return false;
                }else{
                    self.gui.close_popup();
                    self.take_away(self.pos,self.pos.callable);
                }
            });
            if(! self.pos.config.iface_vkeyboard){
                $('#take_away_txt').focus();
            }
            if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
                this.chrome.widget.keyboard.connect($('#take_away_txt'));
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
        take_away : function(pos,callable){
            var self = pos;
            var iptxtval = $("#take_away_txt").val();
            var order = new models.Order({},{ pos: self });
            order.set('pflag',true);
            order.set('parcel',iptxtval);
            order.set('driver_name',false);
            order.set('phone',false);
            self.get('orders').add(order);
            self.set('selectedOrder', order);
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
    gui.define_popup({name:'parcel_order', widget: ParcelOrderPopupWidget});

    var DeliveryOrderPopupWidget = pop_up.extend({
        template:'DeliveryOrderPopupWidget',
        show: function(options){
            options = options || {};
            var self = this;
            this._super();
            this.title = options.title;
            this.delivery = options.delivery;
            this.renderElement();
            self.pos.set_textbox_attributes('partner_selection','delivery_order_popup');
            this.$('.footer .ok').click(function(){
                self.delivery_order(self.pos,self.pos.callable);
            });
            
            this.$(".footer .new_customer").click(function(){
                self.add_customer();
            });
            
            this.$('.footer .close').click(function(){
                self.gui.close_popup();
            });
            
            $('#partner_selection').select2({openOnEnter: false});
            $('#driver_name').select2({openOnEnter: false});
            self.hotkey_handler = function(event){
                if(event.which === 13){
                    self.$('.footer .ok').click();
                }else if(event.which === 27){
                    self.gui.close_popup();
                }
            };
            $('body').on('keyup',self.hotkey_handler);
        },
        delivery_order : function(pos,callable){
            var self = pos;
            var partner_id = null;
            var driver = null;
            if(! $("#partner_selection").val()){
                var warning_icon = true;
                var message = _t("Please Select Customer.");
                self.open_alert_dialog(message,warning_icon);
                return false;
            }else if ($("#partner_selection").val()){
                partner_id = $("#partner_selection").val();
            }
            if(!$("#person_number_txt").val()){
                var warning_icon = true;
                var message = _t("Please Enter Phone Number.");
                self.open_alert_dialog(message,warning_icon);
                return false;
            }
            if(! $('#driver_name').val()){
                var warning_icon = true;
                var message = _t("Please Select Delivery Boy.");
                self.open_alert_dialog(message,warning_icon);
                return false;
            }else{
                var customer_not_exits = true;
                _.each(self.partner_list,function(partner){
                    if($("#partner_selection").val().toLowerCase() == partner.name.toLowerCase()){
                        customer_not_exits = false;
                    }
                });
                if(customer_not_exits){
                    var warning_icon = true;
                    var message = _t("Customer not Exists");
                    self.open_alert_dialog(message,warning_icon);
                    return false;
                }
                var driver_not_exits = true;
                _.each(self.delivery_boy,function(user){
                    if(user.name.toLowerCase() == $('#driver_name').val().toLowerCase()){
                        driver = user.id;
                        driver_not_exits = false;
                    }
                });
                if(driver_not_exits){
                    var warning_icon = true;
                    var message = _t("Invalid Driver");
                    self.open_alert_dialog(message,warning_icon);
                    return false;
                }
                var order = new models.Order({},{ pos: self });
                if(partner_id){
                    _.each(self.partner_list, function(partner) {
                        if(partner.name.toLowerCase() == partner_id.toLowerCase()){
                            order.set_client(partner);
                        }
                    });
                }
                var phone = $("#person_number_txt").val();
                var pflag = false;
                var parcel = false;
                order.partner_id = partner_id;
                order.set('pflag',pflag);
                order.set('parcel',parcel);
                order.set('driver_name',driver);
                order.set('phone',phone);
                order.set('partner_id',partner_id);
                if(partner_id.length == 0 ){
                    var warning_icon = true;
                    var message = _t("Person name is Empty,Please Enter Person Name");
                    self.open_alert_dialog(message,warning_icon);
                    return false;
                }
                self.get('orders').add(order);
                self.set('selectedOrder', order);
                self.gui.close_popup();
            }
        },
        add_customer : function(){
            var self = this;
            self.add_customer_dialog = $(QWeb.render('add-customer', {'widget': self})).dialog({
                resizable: false,
                width:350,
                title: _t("Add Customer"),
                modal : true,
                open : function(){
                    $('body').off('keyup',self.hotkey_handler);
                    $(".ui-dialog").addClass('add_customer_dialog_warning');
                    $(".ui-dialog").css('overflow','hidden')
                    $("body").addClass('hide_over_flow');
                    $(".ui-widget-overlay").height($(document).height()+ 15);
                    set_ui_widget_overlay()
                    $(".ui-dialog-titlebar-close").hide();
                    $('.ui-dialog-buttonpane').find('button:contains("Ok")').addClass('alert_dialog_button');
                    $('.ui-dialog-buttonpane').find('button:contains("Close")').addClass('alert_dialog_button');
                },
                close: function( event, ui ) {
                    $('body').on('keyup',self.hotkey_handler);
                    $( this ).remove();
                    $("body").removeClass('hide_over_flow');
                },
                buttons: {
                    "Ok": function() {
                        var c_name = ($("#customer_name").val()).trim();
                        var c_street = ($("#input_street").val()).trim();
                        var c_street2 = ($("#input_street2").val()).trim();
                        var c_city = ($("#input_city").val()).trim();
                        var c_zip = ($('#input_zip').val()).trim();
                        var c_phone = ($('#input_phone').val()).trim();
                        var nb_error = 0;
                        if (c_name == ''){
                            var warning_icon = true;
                            var message = _t("Please Enter Customer Name.");
                            self.pos.open_alert_dialog(message,warning_icon);
                            nb_error++;
                            return false;
                        }
                        if (c_phone == ''){
                            var warning_icon = true;
                            var message = _t("Please Enter Customer Phone Number.");
                            self.pos.open_alert_dialog(message,warning_icon);
                            nb_error++;
                            return false;
                        }
                        if (nb_error > 0){
                            var warning_icon = true;
                            var message = _t("Please Enter Correct Data");
                            self.pos.open_alert_dialog(message,warning_icon);
                         }else{
                             var Partners = new Model('res.partner');
                             Partners.call('create_customer_from_pos', [c_name, c_street,c_street2,c_city,c_zip, c_phone])
                                 .then(function(clientId){
                                     (new Model('res.partner')).get_func('read')(clientId).then(function(callback){
                                         self.pos.partners.push(callback);
                                         self.pos.partner_list.push(callback);
                                         $("#person_number_txt").val(callback.phone);
                                         self.gui.close_popup();
                                         self.gui.show_popup('delivery_order',{
                                             title:_t('Delivery'),
                                             delivey:true,
                                         });
                                     });
                                 },function(err,event) {
                                     event.preventDefault();
                                     var warning_icon = true;
                                     var message = _t('Error : Can not create customer.');
                                     self.pos.open_alert_dialog(message,warning_icon);
                                });
                                $( this ).remove();
                                self.add_customer_dialog.remove();
                                $("body").removeClass('hide_over_flow');
                        }
                        $('body').on('keyup',self.hotkey_handler);
                    },
                    "Close": function() {
                        $( this ).remove();
                        $("body").removeClass('hide_over_flow');
                        self.add_customer_dialog.remove();
                        $('body').on('keyup',self.hotkey_handler);
                    }
                },
            });
        },
        close:function(){
            this._super();
            $('body').off('keyup',this.hotkey_handler);
        },
    });
    gui.define_popup({name:'delivery_order', widget: DeliveryOrderPopupWidget});

    keyboard.OnscreenKeyboardWidget.include({
      //called after the keyboard is in the DOM, sets up the key bindings.
        start: function(){
            var self = this;
            $('.close_button').unbind('click').bind('click',function(){ 
                //self.deleteAllCharacters();
                self.hide(); 
            });
            // Keyboard key click handling
            $('.keyboard li').click(function(){
                var $this = $(this),
                    character = $this.html(); // If it's a lowercase letter, nothing happens to this variable
                if ($this.hasClass('left-shift') || $this.hasClass('right-shift')) {
                    self.toggleShift();
                    return false;
                }
                if ($this.hasClass('capslock')) {
                    self.toggleCapsLock();
                    return false;
                }
                if ($this.hasClass('delete')) {
                    self.deleteCharacter();
                    return false;
                }
                if ($this.hasClass('numlock')){
                    self.toggleNumLock();
                    return false;
                }
                // Special characters
                if ($this.hasClass('symbol')) character = $('span:visible', $this).html();
                if ($this.hasClass('space')) character = ' ';
                if ($this.hasClass('tab')) character = "\t";
                if ($this.hasClass('return')){
                    character = "\n";
                    self.hide(); 
                }
                // Uppercase letter
                if ($this.hasClass('uppercase')) character = character.toUpperCase();
                // Remove shift once a key is clicked.
                self.removeShift();
                self.writeCharacter(character);
            });
        },
    });

    chrome.OrderSelectorWidget.include({
        neworder_click_handler: function(event, $el) {
            if (this.pos.config.iface_floorplan) {
                 this.gui.show_screen('floors');
                 this.gui.screen_instances.floors.renderElement();
            }else{
                this.pos.add_new_order();
            }
        },
        renderElement: function(){
            var self = this;
            this._super();
            $('#options').click(function(event){
                self.gui.show_screen('reassign_table_screen');
            });
        },
    });

    NumberPopupWidget.widget.include({
        show: function(options){
            options = options || {};
            this._super(options);
            var self = this;
            this.options = options
            this.add_customer = options.add_customer ? options.add_customer : false;
            this.inputbuffer = '' + (options.value   || '');
            this.decimal_separator = _t.database.parameters.decimal_point;
            this.renderElement();
            this.firstinput = true;
            this.add_customer ? $(".pos .popup.popup-number").addClass('popup_height') : $(".pos .popup.popup-number").removeClass('popup_height')
            $("#customer_selection").select2({openOnEnter: false});
            self.numberpopup_event_handler = function(event){
                if(event.which === 13){
                    self.click_confirm();
                }else if(event.which === 27){
                    self.gui.close_popup();
                }
            };
            document.body.addEventListener('keyup',self.numberpopup_event_handler);
        },
        close:function(){
            var self = this;
            this._super();
            document.body.removeEventListener('keyup',self.numberpopup_event_handler);
        },
    });

 // The Table GUI element, should always be a child of the FloorScreenWidget
    var TableWidget = PosBaseWidget.extend({
        template: 'TableWidget',
        init: function(parent, options){
            this._super(parent, options);
            this.table    = options.table;
            this.selected = false;
            this.moved    = false;
            this.dragpos  = {x:0, y:0};
            this.handle_dragging = false;
            this.handle   = null;
        },
        // computes the absolute position of a DOM mouse event, used
        // when resizing tables
        event_position: function(event){
            if(event.touches && event.touches[0]){
                return {x: event.touches[0].screenX, y: event.touches[0].screenY};
            }else{
                return {x: event.screenX, y: event.screenY};
            }
        },
        // when a table is clicked, go to the table's orders
        // but if we're editing, we select/deselect it.
        click_handler: function(){
            var self = this;
            var floorplan = this.getParent();
            if (floorplan.editing) {
                setTimeout(function(){  // in a setTimeout to debounce with drag&drop start
                    if (!self.dragging) {
                        if (self.moved) {
                            self.moved = false;
                        } else if (!self.selected) {
                            self.getParent().select_table(self);
                        } else {
                            self.getParent().deselect_tables();
                        }
                    } 
                },50);
            } else {
                if(self.table.state == "reserved"){
                    //floorplan.pos.set_table(self.table);
                    self.gui.show_popup('alert',{
                        title:_t('Warning !'),
                        warning_icon : true,
                        body: _t('Can not select table. Table is already reserved.'),
                   });
                   return false;
                }else{
                    self.gui.show_popup('number',{
                        'title':_t('Number of Person ?'),
                        'cheap': true,
                        'add_customer':true,
                        'value': self.table.seating_capacities,
                        'confirm': function(value) {
                            self.table.client_detalis = null;
                            if($('#customer_selection').val().length){
                                _.each(self.pos.partners, function(partner) {
                                    if(partner.name.toLowerCase() == $('#customer_selection').val().toLowerCase()){
                                        self.table.client_detalis = partner;
                                        $("#"+self.table.id+'_sit_reserv').val(value)
                                        floorplan.pos.set_table(self.table);
                                    }
                                });
                            }else{
                                $("#"+self.table.id+'_sit_reserv').val(value);
                                floorplan.pos.set_table(self.table);
                            }
                        },
                    });
                }
            }
        },
        // drag and drop for moving the table, at drag start
        dragstart_handler: function(event,$el,drag){
            if (this.selected && !this.handle_dragging) {
                this.dragging = true;
                this.dragpos  = { x: drag.offsetX, y: drag.offsetY };
            }
        },
        // drag and drop for moving the table, at drag end
        dragend_handler:   function(){
            this.dragging = false;
        },
        // drag and drop for moving the table, at every drop movement.
        dragmove_handler: function(event,$el,drag){
            if (this.dragging) {
                var dx   = drag.offsetX - this.dragpos.x;
                var dy   = drag.offsetY - this.dragpos.y;

                this.dragpos = { x: drag.offsetX, y: drag.offsetY };
                this.moved   = true;

                this.table.position_v += dy;
                this.table.position_h += dx;

                $el.css(this.table_style());
            } 
        },
        // drag and dropping the resizing handles
        handle_dragstart_handler: function(event, $el, drag) {
            if (this.selected && !this.dragging) {
                this.handle_dragging = true;
                this.handle_dragpos  = this.event_position(event);
                this.handle          = drag.target;
            } 
        },
        handle_dragend_handler: function() {
            this.handle_dragging = false;
        },
        handle_dragmove_handler: function(event) {
            if (this.handle_dragging) {
                var pos  = this.event_position(event);
                var dx   = pos.x - this.handle_dragpos.x;
                var dy   = pos.y - this.handle_dragpos.y;
                this.handle_dragpos = pos;
                this.moved   = true;
                var cl     = this.handle.classList;
                var MIN_SIZE = 40;  // smaller than this, and it becomes impossible to edit.
                var tw = Math.max(MIN_SIZE, this.table.width);  
                var th = Math.max(MIN_SIZE, this.table.height);
                var tx = this.table.position_h;
                var ty = this.table.position_v;
                if (cl.contains('left') && tw - dx >= MIN_SIZE) {
                    tw -= dx;
                    tx += dx;
                } else if (cl.contains('right') && tw + dx >= MIN_SIZE) {
                    tw += dx;
                }
                if (cl.contains('top') && th - dy >= MIN_SIZE) {
                    th -= dy;
                    ty += dy;
                } else if (cl.contains('bottom') && th + dy >= MIN_SIZE) {
                    th += dy;
                }
                this.table.width  = tw;
                this.table.height = th;
                this.table.position_h = tx;
                this.table.position_v = ty;
                this.$el.css(this.table_style());
            }
        },
        set_table_color: function(color){
            this.table.color = _.escape(color);
            this.$el.css({'background': this.table.color});
        },
        set_table_name: function(name){
            if (name) {
                this.table.name = name;
                this.renderElement();
            }
        },
        set_table_seats: function(seats){
            if (seats) {
                this.table.capacities = Number(seats);
                this.table.seating_capacities = Number(seats);
                this.table.seats = Number(seats);
                this.renderElement();
            }
        },
        // The table's positioning is handled via css absolute positioning,
        // which is handled here.
        table_style: function(){
            var table = this.table;
            function unit(val){ return '' + val + 'px'; }
            var style = {
                'width':        unit(table.width),
                'height':       unit(table.height),
                'line-height':  unit(table.height),
                'margin-left':  unit(-table.width/2),
                'margin-top':   unit(-table.height/2),
                'top':          unit(table.position_v + table.height/2),
                'left':         unit(table.position_h + table.width/2),
                'border-radius': table.shape === 'round' ? 
                        unit(Math.max(table.width,table.height)/2) : '3px',
            };
            if (table.color) {
                style.background = table.color;
            }
            if(table.available_capacities != 0 && table.state == 'available'){
                style.background = 'red';
            }
            if(table.state != 'available'){
                style.background = 'gray';
            }
            if (table.height >= 150 && table.width >= 150) {
                style['font-size'] = '32px';
            } 
            if(table.shape == 'round' && table.width < 85) {
                style.width = '85px';
            }
            return style;
        },
        // convert the style dictionary to a ; separated string for inclusion in templates
        table_style_str: function(){
            var style = this.table_style();
            var str = "";
            var s;
            for (s in style) {
                str += s + ":" + style[s] + "; ";
            }
            return str;
        },
        // select the table (should be called via the floorplan)
        select: function() {
            this.selected = true;
            this.renderElement();
        },
        // deselect the table (should be called via the floorplan)
        deselect: function() {
            this.selected = false;
            this.renderElement();
            this.save_changes();
        },
        // sends the table's modification to the server
        save_changes: function(){
            var self   = this;
            var model  = new Model('restaurant.table');
            var fields = _.find(this.pos.models,function(model){ return model.model === 'restaurant.table'; }).fields;
            // we need a serializable copy of the table, containing only the fields defined on the server
            var serializable_table = {};
            for (var i = 0; i < fields.length; i++) {
                if (typeof this.table[fields[i]] !== 'undefined') {
                    serializable_table[fields[i]] = this.table[fields[i]];
                }
            }
            // and the id ...
            serializable_table.id = this.table.id;
            model.call('create_from_ui',[serializable_table]).then(function(table_id){
                model.query(fields).filter([['id','=',table_id]]).first().then(function(table){
                    for (var field in table) {
                        self.table[field] = table[field];
                    }
                    self.renderElement();
                });
            }, function(err,event) {
                self.gui.show_popup('error',{
                    'title':_t('Changes could not be saved'),
                    'body': _t('You must be connected to the internet to save your changes.'),
                });
                event.stopPropagation();
                event.preventDefault();
            });
        },
        // destroy the table.  We do not really destroy it, we set it 
        // to inactive so that it doesn't show up anymore, but it still
        // available on the database for the orders that depend on it.
        trash: function(){
            var self  = this;
            var model = new Model('restaurant.table');
            return model.call('create_from_ui',[{'active':false,'id':this.table.id}]).then(function(table_id){
                // Removing all references from the table and the table_widget in in the UI ... 
                for (var i = 0; i < self.pos.floors.length; i++) {
                    var floor = self.pos.floors[i];
                    for (var j = 0; j < floor.tables.length; j++) {
                        if (floor.tables[j].id === table_id) {
                            floor.tables.splice(j,1);
                            break;
                        }
                    }
                }
                for(var i=0;i<self.pos.table_details.length;i++){
                    if (self.pos.table_details[i].id === table_id) {
                        self.pos.table_details.splice(i,1);
                        break;
                    }
                }
                var floorplan = self.getParent();
                for (var i = 0; i < floorplan.table_widgets.length; i++) {
                    if (floorplan.table_widgets[i] === self) {
                        floorplan.table_widgets.splice(i,1);
                    }
                }
                if (floorplan.selected_table === self) {
                    floorplan.selected_table = null;
                }
                floorplan.update_toolbar();
                self.destroy();
            }, function(err, event) {
                self.gui.show_popup('error', {
                    'title':_t('Changes could not be saved'),
                    'body': _t('You must be connected to the internet to save your changes.'),
                });
                event.stopPropagation();
                event.preventDefault();
                
            });
        },
        get_notifications: function(){  //FIXME : Make this faster
            var orders = this.pos.get_table_orders(this.table);
            var notifications = {};
            for (var i = 0; i < orders.length; i++) {
                if (orders[i].hasChangesToPrint()) {
                    notifications.printing = true;
                    break;
                } else if (orders[i].hasSkippedChanges()) {
                    notifications.skipped  = true;
                }
            }
            return notifications;
        },
        update_click_handlers: function(editing){
            var self = this;
            this.$el.off('mouseup touchend touchcancel click dragend');
            if (editing) {
                this.$el.on('mouseup touchend touchcancel', function(event){ self.click_handler(event,$(this)); });
            } else {
                this.$el.on('click dragend', function(event){ self.click_handler(event,$(this)); });
            }
        },
        renderElement: function(){
            var self = this;
            this.order_count    = this.pos.get_table_orders(this.table).length;
            this.customer_count = this.pos.get_customer_count(this.table);
            this.fill           = Math.min(1,Math.max(0,this.customer_count / this.table.seats));
            this.notifications  = this.get_notifications();
            this._super();
            this.update_click_handlers();
            this.$el.on('dragstart', function(event,drag){ self.dragstart_handler(event,$(this),drag); });
            this.$el.on('drag',      function(event,drag){ self.dragmove_handler(event,$(this),drag); });
            this.$el.on('dragend',   function(event,drag){ self.dragend_handler(event,$(this),drag); });
            var handles = this.$el.find('.table-handle');
            handles.on('dragstart',  function(event,drag){ self.handle_dragstart_handler(event,$(this),drag); });
            handles.on('drag',       function(event,drag){ self.handle_dragmove_handler(event,$(this),drag); });
            handles.on('dragend',    function(event,drag){ self.handle_dragend_handler(event,$(this),drag); });
        },
    });

    FloorScreenWidget.widget.include({
        init: function(parent, options) {
            this._super(parent, options);
            this.width = (this.pos.config.display_delivery && this.pos.config.display_parcel) ? '49%' : '100%';
        },
        click_back_button :function(event,$el){
            if(this.pos.get('orders').size() > 0){
                this.pos.set({'selectedOrder' : this.pos.get('orders').last()});
                this.gui.show_screen('products')
            }
        },
        renderElement: function(){
            var self = this;
            // cleanup table widgets from previous renders
            for (var i = 0; i < this.table_widgets.length; i++) { 
                this.table_widgets[i].destroy();
            }
            this.table_widgets = [];
            $.when(self.pos.initialize_table_details(false,false)).done(function(){
                screens.ScreenWidget.prototype.renderElement.apply(self,arguments);
                self.chrome.widget.order_selector.hide();
                _.each(self.pos.table_details,function(rec){
                    for (var i = 0; i < self.floor.tables.length; i++) {
                        if(rec.id == self.floor.tables[i].id){
                            self.floor.tables[i].seating_capacities = rec.capacities - rec.available_capacities;
                            self.floor.tables[i].available_capacities = rec.available_capacities;
                            self.floor.tables[i].state = rec.state;
                            var tw = new TableWidget(self,{
                                table: self.floor.tables[i],
                            });
                            tw.appendTo(self.$('.floor-map .tables'));
                            self.table_widgets.push(tw);
                            break;
                        }
                    }
                });
                self.$('.floor-selector .button').click(function(event){
                    self.click_floor_button(event,$(this));
                });
                self.$('.edit-button.shape').click(function(){
                    self.tool_shape_action();
                });
                self.$('.edit-button.color').click(function(){
                    self.tool_colorpicker_open();
                });
                self.$('.edit-button.dup-table').click(function(){
                    self.tool_duplicate_table();
                });
                self.$('.edit-button.new-table').click(function(){
                    self.tool_new_table();
                });
                self.$('.edit-button.rename').click(function(){
                    self.tool_rename_table();
                });
                self.$('.edit-button.seats').click(function(){
                    self.tool_change_seats();
                });
                self.$('.edit-button.trash').click(function(){
                    self.tool_trash_table();
                });
                self.$('.color-picker .close-picker').click(function(event){
                    self.tool_colorpicker_close();
                    event.stopPropagation();
                });
                self.$('.color-picker .color').click(function(event){
                    self.tool_colorpicker_pick(event,$(this));
                    event.stopPropagation();
                });
                self.$('.edit-button.editing').click(function(){
                    self.toggle_editing();
                });
                self.$('.floor-map,.floor-map .tables').click(function(event){
                    if (event.target === self.$('.floor-map')[0] ||
                        event.target === self.$('.floor-map .tables')[0]) {
                        self.deselect_tables();
                    }
                });
                self.$('.color-picker .close-picker').click(function(event){
                    self.tool_colorpicker_close();
                    event.stopPropagation();
                });
                self.$('.back').click(function(event){
                    self.click_back_button(event,$(this));
                });
                self.$('#delivery').bind('click',function(){
                    self.gui.show_popup('delivery_order',{
                        title:_t('Delivery'),
                        delivey:true,
                    });
                });
                self.$('#take_away').bind('click',function(){
                    self.gui.show_popup('parcel_order',{
                        title:_t('Take Away'),
                    });
                });
                self.update_toolbar();
            });
        },
        tool_change_seats: function(){
            var self = this;
            if (this.selected_table) {
                this.gui.show_popup('number',{
                    'title':_t('Number of Seats ?'),
                    'cheap': true,
                    'add_customer':false,
                    'value': self.selected_table.table.seating_capacities,
                    'confirm': function(value) {
                        self.selected_table.set_table_seats(value);
                    },
                });
            }
        },
        tool_duplicate_table: function(){
            if (this.selected_table) {
                var tw = this.create_table(this.selected_table.table);
                tw.table.position_h += 10;
                tw.table.position_v += 10;
                tw.save_changes();
                tw.table.users_ids = [[6, 0, this.selected_table.table.users_ids]];
                this.select_table(tw);
            }
        },
        tool_new_table: function(){
            var tw = this.create_table({
                'position_v': 100,
                'position_h': 100,
                'width': 75,
                'height': 75,
                'shape': 'square',
                'seats': 1,
                'capacities': 1,
                'seating_capacities':1,
                'available_capacities':0,
                'users_ids':[[6, 0, [this.session.uid]]],
            });
            tw.save_changes();
            this.select_table(tw);
            this.check_empty_floor();
        },
        create_table: function(params) {
            var table = {};
            for (var p in params) {
                table[p] = params[p];
            }
            table.name = this.new_table_name(params.name);
            delete table.id; 
            table.floor_id = [this.floor.id,''];
            table.floor = this.floor;
            table.state = 'available'
            this.pos.table_details.push(table)
            this.floor.tables.push(table);
            var tw = new TableWidget(this,{table: table});
                tw.appendTo('.floor-map .tables');
            this.table_widgets.push(tw);
            return tw;
        },
    });

    gui.Gui.include({
        show_saved_screen:  function(order,options) {
            options = options || {};
            this.close_popup();
            if (order) {
                if(order.get_screen_data('screen') != 'floors'){
                    this.show_screen(order.get_screen_data('screen') || 
                            options.default_screen || 
                            this.default_screen,
                            null,'refresh');
                }else{
                    this.show_screen(options.default_screen || this.default_screen,
                            null,'refresh');
                }
            } else {
                this.show_screen(this.startup_screen);
            }
        },
    });

    screens.PaymentScreenWidget.include({
        validate_order: function(force_validation) {
            var self = this;
            var order = this.pos.get_order();
            // FIXME: this check is there because the backend is unable to
            // process empty orders. This is not the right place to fix it.
            if (order.get_orderlines().length === 0) {
                this.gui.show_popup('error',{
                    'title': _t('Empty Order'),
                    'body':  _t('There must be at least one product in your order before it can be validated'),
                });
                return;
            }
            var plines = order.get_paymentlines();
            for (var i = 0; i < plines.length; i++) {
                if (plines[i].get_type() === 'bank' && plines[i].get_amount() < 0) {
                    this.gui.show_popup('error',{
                        'title': _t('Negative Bank Payment'),
                        'body': _t('You cannot have a negative amount in a Bank payment. Use a cash payment method to return money to the customer.'),
                    });
                    return;
                }
            }
            if (!order.is_paid() || this.invoicing) {
                return;
            }
            // The exact amount must be paid if there is no cash payment method defined.
            if (Math.abs(order.get_total_with_tax() - order.get_total_paid()) > 0.00001) {
                var cash = false;
                for (var i = 0; i < this.pos.cashregisters.length; i++) {
                    cash = cash || (this.pos.cashregisters[i].journal.type === 'cash');
                }
                if (!cash) {
                    this.gui.show_popup('error',{
                        title: _t('Cannot return change without a cash payment method'),
                        body:  _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'),
                    });
                    return;
                }
            }

            // if the change is too large, it's probably an input error, make the user confirm.
            if (!force_validation && (order.get_total_with_tax() * 1000 < order.get_total_paid())) {
                this.gui.show_popup('confirm',{
                    title: _t('Please Confirm Large Amount'),
                    body:  _t('Are you sure that the customer wants to  pay') + 
                           ' ' + 
                           this.format_currency(order.get_total_paid()) +
                           ' ' +
                           _t('for an order of') +
                           ' ' +
                           this.format_currency(order.get_total_with_tax()) +
                           ' ' +
                           _t('? Clicking "Confirm" will validate the payment.'),
                    confirm: function() {
                        self.validate_order('confirm');
                    },
                });
                return;
            }
            if (order.is_paid_with_cash() && this.pos.config.iface_cashdrawer) { 
                this.pos.proxy.open_cashbox();
            }
            order.initialize_validation_date();
            if (order.is_to_invoice()) {
                var invoiced = this.pos.push_and_invoice_order(order);
                this.invoicing = true;
                invoiced.fail(function(error){
                    self.invoicing = false;
                    if (error.message === 'Missing Customer') {
                        self.gui.show_popup('confirm',{
                            'title': _t('Please select the Customer'),
                            'body': _t('You need to select the customer before you can invoice an order.'),
                            confirm: function(){
                                self.gui.show_screen('clientlist');
                            },
                        });
                    } else if (error.code < 0) {        // XmlHttpRequest Errors
                        self.gui.show_popup('error',{
                            'title': _t('The order could not be sent'),
                            'body': _t('Check your internet connection and try again.'),
                        });
                    } else if (error.code === 200) {    // Odoo Server Errors
                        self.gui.show_popup('error-traceback',{
                            'title': error.data.message || _t("Server Error"),
                            'body': error.data.debug || _t('The server encountered an error while receiving your order.'),
                        });
                    } else {                            // ???
                        self.gui.show_popup('error',{
                            'title': _t("Unknown Error"),
                            'body':  _t("The order could not be sent to the server due to an unknown error"),
                        });
                    }
                });
                invoiced.done(function(){
                    self.invoicing = false;
                    order.finalize();
                });
            } else {
                $.blockUI();
                var push_order = this.pos.push_order(order);
                push_order.done(function(){
                    $.unblockUI();
                    self.gui.show_screen('receipt');
                });
                push_order.fail(function(error){
                    $.unblockUI();
                });
            }
        },
        show: function(){
            this.chrome.widget.order_selector.hide();
            this._super();
        },
        hide: function(){
            this.chrome.widget.order_selector.show();
            this._super();
        },
    });

    var splitBillScreenWidget;
    _.each(gui.Gui.prototype.screen_classes,function(screen_class){
        if(screen_class.name == "splitbill"){
            splitBillScreenWidget = screen_class;
        }
    });
    splitBillScreenWidget.widget.include({
        show: function(){
            var self = this;
            screens.ScreenWidget.prototype.show.call(this);
            this.renderElement();
            var order = this.pos.get_order();
            var neworder = new models.Order({
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

    var ReassignTableScreenWidget = screens.ScreenWidget.extend({
        template: 'ReassignTableScreenWidget',
        hide: function(){
            this._super();
            $(".pos-leftpane").show();
            $(".rightpane").removeClass("full_screen");
        },
        show: function(){
            var self = this;
            this._super();
            this.renderElement();
            $(".pos-leftpane").hide();
            $(".rightpane").addClass("full_screen");
        },
        renderElement: function(){
            this._super();
            var self = this;
            this.$el.find("#back_screen").bind("click",function() {
                self.gui.show_screen('products');
            });
            this.$el.find( ".oe_sidebar_print" ).bind("click",function() {
                self.pos.option_value = '';
                self.pos.option_text = $(this).text();
                self.pos.option_value = $(this).attr("id");
                self.$el.find( ".oe_sidebar_print" ).removeClass('highlight')
                $(this).addClass('highlight')
                $(".reassign_table_screen_content").html("")
                flag = 0;
                _.each(self.pos.attributes.orders.models, function(order){
                    if(order.attributes.reserved_seat)
                        flag ++;
                });
                if(flag){
                    self.pos.initialize_table_details(false,true);
                }
            });
            this.$el.find('.re_assign_order_button').click(function(e){
                self.order_re_assign(self.pos);
            });
            $("#re_assign_order").click();
//            document.body.removeEventListener('keyup',this.pos.re_assign_event_handler);
        },
        order_re_assign : function(pos){
            var self = pos;
            var tabel_screen = this;
            var selection_name = '';
            var reserved_seat = '';
            var selection_id = [];
            var select_tables = [];
            var flag = true;
            self.is_any_checked_table = false;
            $('#table_list tr input[type="checkbox"]:checked').each(function(index){
                self.is_any_checked_table = true;
                selection_name += ' ' + this.value +"/" + $("#"+$(this).attr('id')+'_reserv_sit').val();  //selected_row[1]
                table_id = parseInt($(this).attr('id'));
                selection_id.push(table_id); //selected_row[0]
                reserved_seat += $(this).attr('id')+ "/" +$("#"+$(this).attr('id')+'_reserv_sit').val()+'_';
                actual_reserved_seat = parseInt($("#"+$(this).attr('id')+'_reserv_sit').val());
                already_booked_seat = parseInt($("#"+$(this).attr('id')+'_reserv_sit').attr('booked'));
                available_seat = parseInt($("#"+$(this).attr('id')+'_leaft_seat')[0].innerHTML);
                select_tables.push({reserver_seat: $("#"+$(this).attr('id')+'_reserv_sit').val(), table_id: table_id});
                var table_vals = {'available_capacities': actual_reserved_seat + already_booked_seat};
                    
                if (actual_reserved_seat == available_seat) {
                    table_vals['state'] = 'reserved';
                }
                if((actual_reserved_seat >  available_seat) || (available_seat == 0) ){
                    self.gui.show_popup('alert',{
                        title:_t('Warning !'),
                        body: _t("Table capacity is ") + $("#"+$(this).attr('id')+'_leaft_seat')[0].innerHTML + _t(" person you cannot enter more then ") + $("#"+$(this).attr('id')+'_leaft_seat')[0].innerHTML + _t(" or less than 1. "),
                    });
                    flag = false;
                    return false;
                }
                if(self.re_assign){
                    if($("#booked_table option").filter(':selected').val()){
                        restaurant_table_model.call("write",[[table_id],table_vals]).then(function(callback){},function(err,event) {event.preventDefault();});
                    }
                    else{
                        return false;
                    }
                }else{
                    restaurant_table_model.call("write",[[table_id],table_vals]).then(function(callback){},function(err,event) {event.preventDefault();});
                }
                if (actual_reserved_seat <= 0) {
                    self.gui.show_popup('alert',{
                        title:_t('Warning !'),
                        body: _t("You must be add some person in this table"),
                    });
                    flag = false;
                    return false;
                }
                this.checked = false;
            });
            if(self.re_assign && ! self.delivery && flag){//flag not 
               this.re_assign(self,selection_name,selection_id,reserved_seat,select_tables);
            }
        },
        re_assign : function(pos,selection_name,selection_id,reserved_seat,select_tables){
            var self = pos;
            var tabel_screen = this;
            var booked_selected_table = $("#booked_table option").filter(':selected').val();
            booked_selected_table = booked_selected_table.toString().replace('_,','_');
            if(booked_selected_table){
                if(self.option_value == "re_assign_order" && ! self.is_any_checked_table){
                    self.gui.show_popup('alert',{
                        title:_t('Warning !'),
                        body: _t('Please select table , without table user can not make order.'),
                    });
                    return false;
                }
                var items = $("#booked_table option:selected").map(function() {
                    return $(this).attr('item');
                }).get();
                items.join();
                var items_id = $("#booked_table option:selected").map(function() {
                    return $(this).attr('id');
                }).get();
                items_id.join();
                var re_assign_orders = false;
                var merge_orders = false
                for(var i=0;i < self.attributes.orders.models.length;i++){
                    order =  _.clone(self.attributes.orders.models[i]);
                    var template = '<span class="order-sequence">' + order.sequence_number + '</span>'
                    /*Reassign Order code */
                    if(order && $("#booked_table option").filter(':selected').val() == order.attributes.reserved_seat 
                        &&  items_id.indexOf(order.name.toString().replace(' ','_')) != -1 
                        && ! order.attributes.pflag && ! $(".marge_table").is(":checked")){
                        pos_order_model.call('reassign_table', [booked_selected_table]);
                        _.each(order.attributes.table_ids, function(id){
                            restaurant_table_model.call("write",[[id],{"state":"available"}]);
                        });
                        $("#"+order.name.replace(' ', '_')).attr("name", selection_name);
                        $("#"+order.name.replace(' ', '_')).attr("item", selection_name);
                        $("#"+order.name.replace(' ', '_')).attr("data", reserved_seat);
                        $("#"+order.name.replace(' ', '_')).html(template + selection_name);
                        order.set('reserved_seat',reserved_seat);
                        order.set('creationDate',selection_name);
                        order.set('table_ids',selection_id);
                        order.set('table_data',select_tables);
                        re_assign_orders = order;
                        var send_order_to_kitchen = {'data': re_assign_orders.export_as_JSON()};
                        pos_order_model.call("create_from_ui", [[send_order_to_kitchen], true]).done(function(order_id){
                            re_assign_orders.set('id',order_id[0]);
                            for( idx in re_assign_orders.orderlines.models){
                                re_assign_orders.orderlines.models[idx].ol_flag = false;
                                re_assign_orders.orderlines.models[idx].flag = false;
                                re_assign_orders.orderlines.models[idx].line_id = order_id[1][idx];
                            }
                        });
                        self.gui.show_screen('products');
                    }else if(self.option_value == "merge_order"){/*Merge Order code */
                        var table_name = (items.toString().replace(',',' ') +selection_name).trim();
                        table_name += ' ';
                        if(order && booked_selected_table == order.attributes.reserved_seat  
                            && items_id.indexOf(order.name.toString().replace(' ','_')) != -1){
                            if(selection_name){
                                $("#"+order.name.replace(' ', '_')).attr("data", order.attributes.reserved_seat +reserved_seat);
                                $("#"+order.name.replace(' ', '_')).attr("name",  table_name);
                                $("#"+order.name.replace(' ', '_')).attr("item", table_name);
                                $("#"+order.name.replace(' ', '_')).html(template + table_name);
                                order.set('creationDate',table_name);
                                order.set('reserved_seat',order.attributes.reserved_seat + reserved_seat);
                                _.each(selection_id, function(id){
                                    order.attributes.table_ids.push(id);
                                });
                                _.each(select_tables, function(data){
                                    order.attributes.table_data.push(data);
                                });
                                self.set('selectedOrder', self.attributes.orders.models[i]);
                                merge_orders = order;
                                var send_order_to_kitchen = {'data': order.export_as_JSON()};
                                pos_order_model.call("create_from_ui", [[send_order_to_kitchen], true]).done(function(order_id){
                                    merge_orders.set('id',order_id[0]);
                                    for( idx in merge_orders.orderlines.models){
                                        merge_orders.orderlines.models[idx].ol_flag = false;
                                        merge_orders.orderlines.models[idx].flag = false;
                                        merge_orders.orderlines.models[idx].line_id = order_id[1][idx];
                                    }
                                    tabel_screen.merge_order(self,merge_orders,table_name,items_id);
                                });
                            }else{
                                tabel_screen.merge_order(self,order,table_name,items_id)
                            }
                        }
                    }
                    self.gui.show_screen('products');
                }
            }else{
                self.gui.show_popup('alert',{
                    title:_t('Warning !'),
                    body: _t('Please select table , without table user can not make order.'),
                });
                return false;
            }
        },
        merge_order : function(pos,order,table_name,items_id){
            var self = pos;
            for(var j=0;j < self.get('orders').models.length;j++){
                second_order =  _.clone( self.get('orders').models[j]);
                second_order.attributes.state = 'draft';
               // if(order.attributes.user_id == second_order.attributes.user_id){
                    if(second_order && second_order.attributes.creationDate && table_name.search(second_order.attributes.creationDate.trim(' ')) != -1 
                        && items_id.indexOf(order.name.toString().replace(' ','_')) != -1){
                        if(second_order.partner_id && order.partner_id 
                            && (order.partner_id != second_order.partner_id)){
                            self.gui.show_popup('alert',{
                                title:_t('Warning !'),
                                body: _t('Partner are not same! So can not Merge table!'),
                            });
                            return false;
                        }else if(second_order.user_id && order.user_id 
                            && (second_order.user_id != order.user_id)){
                            self.gui.show_popup('alert',{
                                title:_t('Warning !'),
                                body: _t('Salesman are not same! So can not Merge table!'),
                            });
                            return false;
                        }else{
                            if(second_order.name != order.name){
                                if(second_order.attributes.id && order.attributes.id){
                                    pos_order_model.call("remove_order", [[order.attributes.id], second_order.attributes.id]).then(function(callback){
                                        if(callback){
                                            order.orderlines.add(second_order.orderlines.models);
                                            var template = '<span class="order-sequence">' + order.sequence_number + '</span>'
                                            $("#"+order.name.replace(' ', '_')).attr("data", order.attributes.reserved_seat +second_order.attributes.reserved_seat);
                                            $("#"+order.name.replace(' ', '_')).html(template + table_name);
                                            $("#"+order.name.replace(' ', '_')).attr("name", table_name);
                                            $("#"+order.name.replace(' ', '_')).attr("item", table_name);
                                            _.each(second_order.attributes.table_ids, function(id){
                                                order.attributes.table_ids.push(id);
                                            });
                                            order.set('reserved_seat',order.attributes.reserved_seat + second_order.attributes.reserved_seat);
                                            order.set('creationDate',table_name);
                                            _.each(second_order.attributes.table_data, function(data){
                                                order.attributes.table_data.push(data);
                                            });
                                            self.set('selectedOrder',  self.attributes.orders.models[i]);
                                            var send_order_to_kitchen = {'data': order.export_as_JSON()};
                                            pos_order_model.call("create_from_ui", [[send_order_to_kitchen], true]).done(function(order_id){
                                                order.set('id',order_id[0]);
                                                for( idx in order.orderlines.models){
                                                    order.orderlines.models[idx].ol_flag = false;
                                                    order.orderlines.models[idx].flag = false;
                                                    order.orderlines.models[idx].line_id = order_id[1][idx];
                                                }
                                            });
                                            second_order.destroy();
                                            //new instance.web.DataSet(this, 'pos.order').unlink([second_order.attributes.id]);
                                        }
                                    });
                                }else if(second_order.attributes.id && ! order.attributes.id){
                                    second_order.orderlines.add(order.orderlines.models);
                                    var template = '<span class="order-sequence">' + second_order.sequence_number + '</span>'
                                    $("#"+second_order.name.replace(' ', '_')).attr("data", second_order.attributes.reserved_seat + order.attributes.reserved_seat);
                                    $("#"+second_order.name.replace(' ', '_')).html(template + table_name);
                                    $("#"+second_order.name.replace(' ', '_')).attr("name", table_name);
                                    $("#"+second_order.name.replace(' ', '_')).attr("item", table_name);
                                    _.each(order.attributes.table_ids, function(id){
                                        second_order.attributes.table_ids.push(id);
                                    });
                                    second_order.set('creationDate',table_name); 
                                    second_order.set('reserved_seat',second_order.attributes.reserved_seat + order.attributes.reserved_seat);
                                    _.each(order.attributes.table_data, function(data){
                                        second_order.attributes.table_data.push(data);
                                    });
                                    self.set('selectedOrder', second_order);
                                    var send_order_to_kitchen = {'data': second_order.export_as_JSON()};
                                    pos_order_model.call("create_from_ui", [[send_order_to_kitchen], true]).done(function(order_id){
                                        second_order.set('id',order_id[0]);
                                        for( idx in second_order.orderlines.models){
                                            second_order.orderlines.models[idx].ol_flag = false;
                                            second_order.orderlines.models[idx].flag = false;
                                            second_order.orderlines.models[idx].line_id = order_id[1][idx];
                                            second_order.orderlines.models[idx].read_only = true
                                        }
                                    });
                                    order.destroy();
                                }else {
                                    order.orderlines.add(second_order.orderlines.models);
                                    var template = '<span class="order-sequence">' + order.sequence_number + '</span>'
                                    $("#"+order.name.replace(' ', '_')).attr("data", order.attributes.reserved_seat +second_order.attributes.reserved_seat);
                                    $("#"+order.name.replace(' ', '_')).html(template + table_name);
                                    $("#"+order.name.replace(' ', '_')).attr("name", table_name);
                                    $("#"+order.name.replace(' ', '_')).attr("item", table_name);
                                    _.each(second_order.attributes.table_ids, function(id){
                                        order.attributes.table_ids.push(id);
                                    });
                                    order.set('creationDate',table_name);
                                    order.set('reserved_seat',order.attributes.reserved_seat + second_order.attributes.reserved_seat);
                                    $("#"+order.name.replace(' ', '_')).attr("name", table_name);
                                    _.each(second_order.attributes.table_data, function(data){
                                        order.attributes.table_data.push(data);
                                    });
                                    self.set('selectedOrder', order);
                                    var send_order_to_kitchen = {'data': order.export_as_JSON()};
                                    pos_order_model.call("create_from_ui", [[send_order_to_kitchen], true]).done(function(order_id){
                                        order.set('id',order_id[0]);
                                        for( idx in order.orderlines.models){
                                            order.orderlines.models[idx].ol_flag = false;
                                            order.orderlines.models[idx].flag = false;
                                            order.orderlines.models[idx].line_id = order_id[1][idx];
                                        }
                                    });
                                    second_order.destroy();
                                }
                            }
                        }
                    }
              //  }
            }
        },
    });
    gui.define_screen({'name': 'reassign_table_screen','widget': ReassignTableScreenWidget});

    screens.ReceiptScreenWidget.include({
        show: function(){
            this._super();
            this.chrome.widget.order_selector.hide();
        },
        hide: function(){
            this.chrome.widget.order_selector.show();
            this._super();
        },
    });

    function set_ui_widget_overlay(){
        $(window).unbind('resize').bind('resize',function () {
            $(".ui-widget-overlay").height($(document).height()+ 15);
        });
    }

});
