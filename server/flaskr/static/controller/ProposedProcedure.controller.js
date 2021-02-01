sap.ui.define([
	"./BaseController",
	"sap/ui/model/json/JSONModel",
	"sap/ui/core/routing/History",
	"sap/m/MessageBox"
], function(BaseController, JSONModel, History, MessageBox) {
	"use strict";

	return BaseController.extend("ui.kolki.controller.ProposedProcedure", {

		//Initialize page
		onInit: function () {
			var oRouter = this.getRouter();
			oRouter.getRoute("ProposedProcedure").attachPatternMatched(this._onObjectMatched, this);
		},
		//Back button
		onNavBack: function() {
			var sPreviousHash = History.getInstance().getPreviousHash();
			var oRouter = this.getRouter();
			if (sPreviousHash !== undefined) {
				history.go(-1);
			} else {
				oRouter.navTo("home", {}, true);
			}
		},		
		//Mark update
		onChangeText: function(oEvent){
			this._sendUpdate(oEvent);
		},
		//Mark update
		onSelect: function(oEvent){
			this._sendUpdate(oEvent);
		},
		//Delete record
		onDelRecord: function(oEvent){
			var aKeys = this.byId("ProposedProcedureTable").getSelectedIndices();
			if(aKeys.length=== 0){
				this.getPopup("no_delete_selected");
				return;
			}
			this._sendDelete(aKeys);
		},
		//New record
		onNewRecord: function(oEvent){
			var	that = this,
				oModel = that.getModel(),
				oRouter = that.getRouter(),
				oNew = {
					"l3": "",
					"solution": "",
					"active": true
				};
			oModel.setProperty("/ProposedProcedureNew",oNew);
			oRouter.navTo("ProposedProcedureNew", {}, true);
		},
		//Save changes
		onSave: function(oEvent){
			var	that = this,
				oModel = this.getModel(),
				aUpdate = oModel.getProperty("/ProposedProcedureUpdate"),
				aDelete = oModel.getProperty("/ProposedProcedureDelete");
			if(aUpdate.length === 0
				&& aDelete.length === 0){
				that.getPopup("no_changes");
				return;
			}
			MessageBox.confirm(that.getText("confirm_save"),{
				onClose: function(oAction){
					if(oAction === "OK"){
						that._saveChanges_wrapper(aUpdate,aDelete,[]);
					}
				}
			});			
		},
		//Discard changes
		onDiscard: function(oEvent){
			var	that = this,
				oRouter = that.getRouter();
			MessageBox.confirm(that.getText("confirm_cancel"),{
				onClose: function(oAction){
					if(oAction === "OK"){
						oRouter.navTo("home", {}, true);
					}
				}
			});
		},
		//Matched URL
		_onObjectMatched: function(oEvent){
			var that = this;
			that._getProposedProcedureData();
		},
		//Get data from service
		_getProposedProcedureData: function(){
			var that = this,
				oModel = that.getModel();
			that.setBusy(that.byId("ProposedProcedureTable"),true);
			that.getData("api/ProposedProcedure").done(function(result) {
				oModel.setProperty("/ProposedProcedure",result);
				oModel.setProperty("/ProposedProcedureDelete",[]);
				oModel.setProperty("/ProposedProcedureUpdate",[]);			
				that.setBusy(that.byId("ProposedProcedureTable"),false);				
			}).fail(function(result) {
				that.getPopup("error_retrieval",result);
				that.setBusy(that.byId("ProposedProcedureTable"),false);
			});
		},
		//Send the information to server, process response.
		_saveChanges_wrapper: function(aUpdate,aDelete,aCreate){
			var that = this;
			that.setBusy(that.getView(),true);				
			that.sendCRUD_ProposedProcedure(aUpdate,aDelete,aCreate).done(function(result) {
				that._getProposedProcedureData();
				that.setBusy(that.getView(),false);				
				that.getPopup("changes_saved");
			}).fail(function(result) {
				that.getPopup("changes_error",result);
				that.setBusy(that.getView(),false);				
			});
		},
		//Send to delete:
		_sendDelete: function(aKeys){
			var	oModel = this.getModel(),
				aDelete = oModel.getProperty("/ProposedProcedureDelete"),
				aUpdate = oModel.getProperty("/ProposedProcedureUpdate"),
				aProposed= oModel.getProperty("/ProposedProcedure");
				aProposed = [...aProposed]
			for (var iKey of aKeys) {
				var _id = this.byId("ProposedProcedureTable").getContextByIndex(iKey).getProperty("_id");
				//Remove from update array:
				aUpdate = this._removeFromUpdate(_id,aUpdate);
				//Remove from ProposedProcedure array:
				aProposed = this._removeFromUpdate(_id,aProposed);
				//Add to remove array
				aDelete.push( {
					"_id": _id
				});				
			}			
			oModel.setProperty("/ProposedProcedureDelete",aDelete);
			oModel.setProperty("/ProposedProcedureUpdate",aUpdate);
			oModel.setProperty("/ProposedProcedure",aProposed);
			oModel.refresh("");
			this.byId("ProposedProcedureTable").clearSelection();
		},
		//Send to update:
		_sendUpdate: function(oEvent){
			var oValue = oEvent.getSource().getBindingContext().getProperty(),
				oModel = this.getModel(),
				oUpdate = {
					"_id": oValue._id,
					"solution": oValue.solution,
					"active": oValue.active };
			var aUpdate = oModel.getProperty("/ProposedProcedureUpdate");
			aUpdate = this._removeFromUpdate(oUpdate._id,aUpdate);
			aUpdate.push(oUpdate);
			oModel.setProperty("/ProposedProcedureUpdate",aUpdate);
		},
		//Removes item from update proeprty
		_removeFromUpdate: function(_id,aArray){
			return aArray.filter(x=> x._id !== _id);
		},		
	});
});      