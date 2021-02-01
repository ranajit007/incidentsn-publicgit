sap.ui.define([
	"./BaseController",
	"sap/ui/model/json/JSONModel",
	"sap/ui/core/routing/History",
	"sap/ui/core/Fragment"
], function(BaseController, JSONModel, History,Fragment) {
	"use strict";

	return BaseController.extend("ui.kolki.controller.Home", {
		onInit: function () {
			this._getHeaderData();
			this._getTableData();			
		},
		//NAVIGATES TO NEXT PAGE
		onPressTable: function(oEvent){
			var incident = oEvent.getParameter("row").getBindingContext().getProperty("number");
			var oRouter = this.getRouter();
			oRouter.navTo("incident", {number: incident});
		},
		//Updates the MONGODB from service.
		onUpdate: function(oEvent){
			var that = this;
			if (!this._oBusyDialog) {
				Fragment.load({
					name: "ui.kolki.view.Loading",
					controller: this
				}).then(function (oFragment) {
					this._oBusyDialog = oFragment;
					this.getView().addDependent(this._oBusyDialog);
					this._oBusyDialog.open();
					this._getUpdated(that);
				}.bind(this));
			} else {
				this._oBusyDialog.open();
				this._getUpdated(that);
			}
		},		
		//SENDS CORRESPONDING PETITION.
		onSelectionChangeMCBSelection: function(oEvent){
			var that = this;
			//Get key for table
			var sKey = this.byId("IconTabBarPending").getSelectedKey()
			//Get keys
			var aKeys = this.byId("oMCBSelection").getSelectedKeys()
			if(aKeys.length === 0){
				that.getPopup("no_assignment_groups")
				return;
			}
			that._getTableData(sKey);
			that._getTableCountWraper();
		},
		//GETS TABLE DEPENDING ON KEY
		onFilterSelect: function(oEvent){
			var sKey = oEvent.getParameter("key");
			this._getTableData(sKey);
		},
		//OPEN MAINTENANCE VIEW
		onProposedProcedure: function(oEvent){
			var oRouter = this.getRouter();
			oRouter.navTo("ProposedProcedure", {});		
		},			
		//SELECTS ALL GROUP ASSIGNMENTS:
		_selectAll: function(){
			//Get all possible keys:		
			var aKeys = this.getModel().getProperty("/Groups");
			var sKeys = [];
			aKeys.forEach(oKeys => {
				sKeys.push(oKeys["key"]);
			});
			var oMCBSelection = this.byId("oMCBSelection");
			oMCBSelection.addSelectedKeys(sKeys);
		},
		//Gets updated information from SN
		_getUpdated:  function(that){
			that.getData("api/incidents/update").done(function(result) {
				that.getPopup("incident_done");
				that._getHeaderData();
				that._getTableData();
				that._oBusyDialog.close();
			}).fail(function(result) {
				that.getPopup("error_update",result);
				that._oBusyDialog.close();
			});
		},
		//Gets the header data, last update, username, etc
		_getHeaderData: function(){
			var that = this;
			that.setBusy(that.getView(),true);
			that.getData("api/HeaderData").done(function(result) {
				that.byId("ConfigUpdate").setText(result.last_update);
				that.byId("ConfigUser").setText(result.user_id);
				that.setBusy(that.getView(),false);
				that._selectAll();
			}).fail(function(result) {
				that.getPopup("error_get",result);
				that.setBusy(that.getView(),false);
			});
			that._getTableCountWraper();
		},
		//GET COUNTERS WRAPPER
		_getTableCountWraper: function(){
			var that = this;
			that._getTableCount("pending").done(function(result) {
				that.getModel().setProperty("/PendingCount",result.incidents);
			}).fail(function(result) {
				that.getModel().setProperty("/PendingCount",0);
			});
			that._getTableCount("closed").done(function(result) {
				that.getModel().setProperty("/ClosedCount",result.incidents);
			}).fail(function(result) {
				that.getModel().setProperty("/ClosedCount",0);
			});
		},
		//GET TABLE COUNT
		_getTableCount: function(type="pending"){
			var that = this;
			var sURL = "api/incidents_" + type + "_count";
			//IF FILTER EXISTS, IMPLEMENT
			var oMCBSelection = this.byId("oMCBSelection");
			var aKeys = oMCBSelection.getSelectedKeys();
			if(aKeys.length != 0){
				sURL = sURL + "?groups=" + encodeURI(aKeys.join(","));
			}
			return that.getData(sURL)
		},
		//GET TABLE DATA FROM SERVICE AND UPDATES /Incidents PROPERTY FROM MODEL Incidents
		_getTableData: function(type="pending"){
			var that = this;
			var oTable = that.getView().byId("IncidentsTable");
			that.setBusy(oTable,true);
			var sURL = "api/incidents_" + type;
			//IF FILTER EXISTS, IMPLEMENT
			var oMCBSelection = this.byId("oMCBSelection");
			var aKeys = oMCBSelection.getSelectedKeys();
			if(aKeys.length != 0){
				sURL = sURL + "?groups=" + encodeURI(aKeys.join(","));

			}
			that.getData(sURL).done(function(result) {
				that.getModel().setProperty("/Incidents",result.Incidents);
				that.setBusy(oTable,false);
			}).fail(function(result) {
				that.getPopup("error_get",result);
				that.getModel().setProperty("/Incidents",[]);
				that.setBusy(oTable,false);
			});
		}
	});
});      