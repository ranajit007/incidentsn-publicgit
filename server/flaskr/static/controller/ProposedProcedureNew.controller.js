sap.ui.define([
	"./BaseController",
	"sap/ui/model/json/JSONModel",
	"sap/ui/core/routing/History",
	"sap/m/MessageBox"
], function(BaseController, JSONModel, History, MessageBox) {
	"use strict";

	return BaseController.extend("ui.kolki.controller.ProposedProcedureNew", {

		//Initialize page
		onInit: function () {
			var oRouter = this.getRouter();
			oRouter.getRoute("ProposedProcedureNew").attachPatternMatched(this._onObjectMatched, this);
		},
		//Back button
		onNavBack: function() {
			var sPreviousHash = History.getInstance().getPreviousHash();
			var oRouter = this.getRouter();
			if (sPreviousHash !== undefined) {
				history.go(-1);
			} else {
				oRouter.navTo("ProposedProcedure", {}, true);
			}
		},		
		//Matched URL
		_onObjectMatched: function(oEvent){
			var that = this;
			that._getProposedProcedureData();
		},
		//Reset data
		_getProposedProcedureData: function(){
			var	that = this,
			oModel = that.getModel(),
			oNew = {
				"l3": "",
				"solution": "",
				"active": true
			};
			oModel.setProperty("/ProposedProcedureNew",oNew);
		},
		//Save changes
		onSave: function(oEvent){
			var that = this,
				oModel = this.getModel(),
				oNew = oModel.getProperty("/ProposedProcedureNew");
			if(!oNew.l3 ||
				!oNew.solution){
				that.getPopup("check_required");
				return;
			}
			var aCreate = [oNew];
			MessageBox.confirm(that.getText("confirm_save"),{
				onClose: function(oAction){
					if(oAction === "OK"){
						that._saveChanges_wrapper([],[],aCreate);
					}
				}
			});			
		},
		//Discard changes
		onDiscard: function(oEvent){
			var that = this;
			var oRouter = that.getRouter();
			MessageBox.confirm(that.getText("confirm_cancel"),{
				onClose: function(oAction){
					if(oAction === "OK"){
						oRouter.navTo("ProposedProcedure", {}, true);
					}
				}
			});
		},
		//Send the information to server, process response.
		_saveChanges_wrapper: function(aUpdate,aDelete,aCreate){
			var that = this;
			var oRouter = that.getRouter();
			that.setBusy(that.getView(),true);				
			that.sendCRUD_ProposedProcedure(aUpdate,aDelete,aCreate).done(function(result) {
				oRouter.navTo("ProposedProcedure", {}, true);
				that.setBusy(that.getView(),false);				
				that.getPopup("changes_saved");
			}).fail(function(result) {
				that.getPopup("changes_error",result);
				that.setBusy(that.getView(),false);				
			});
		},		
	});
});      