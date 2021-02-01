sap.ui.define([
	"./BaseController",
	"sap/ui/model/json/JSONModel",
	"sap/ui/core/routing/History",
	"sap/m/MessageBox"
], function(BaseController, JSONModel, History, MessageBox) {
	"use strict";

	return BaseController.extend("ui.kolki.controller.Incident", {

		//Initialize page
		onInit: function () {
			var oRouter = this.getRouter();
			oRouter.getRoute("incident").attachPatternMatched(this._onObjectMatched, this);
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
		//Matched URL
		_onObjectMatched: function(oEvent){
			var that = this;
			var sNumber = oEvent.getParameter("arguments").number;;
			that._getNumberData(sNumber);
		},
		//Get data from service
		_getNumberData: function(sNumber){
			var that = this,
				oView = that.getView(),
				oModel = that.getModel();
			that.setBusy(oView,true);
			that.getData("api/incidents/" + sNumber).done(function(result) {
				oModel.setProperty("/Incident",result);
				oModel.setProperty("/Predictions",result.predictions);
				that.setBusy(oView,false);
			}).fail(function(result) {
				that.getPopup("feedback_error",result);
				that.setBusy(oView,false);
			});
			that.getData("api/predictions_conf").done(function(result){
				oModel.setProperty("/PredictionsConfig",result);
			});
		},
		//Update with positive review
		onActionFeedback: function(oEvent) {
			var that = this,
				oModel = that.getModel(),
				sNumber = oModel.getProperty("/Incident/number"),
				sUUID = oEvent.getParameter("row").getBindingContext().getProperty("uuid"),
				sFeedback = oEvent.getSource().data().feedback;
			that.getReviewHandler(sNumber,sFeedback,sUUID);
		},
		//Updates feedback with positive or negative connotation
		getReviewHandler(sNumber,sFeedback,sUUID){
			var that = this,
				oTable = that.byId("PredictionList");
			that.setBusy(oTable,true);
			that.sendReview(sNumber,sFeedback,sUUID).done(function(result) {
				that._getNumberData(sNumber);
				that.getPopup("feedback_sent");
				that.setBusy(oTable,false);
			}).fail(function(result) {
				that.getPopup("feedback_error",result);
				that.setBusy(oTable,false);
			});
		},
		//Send review to service
		sendReview: function(sNumber,sFeedback,sUUID){
			return jQuery.ajax({
				url: "api/review/"+ sNumber,
				type: "POST",
				data: {
					feedback: sFeedback,
					uuid: sUUID
				}
			});
		},
		//Calculates predictions
		onCalculatePrediction: function(oEvent){
			var that = this,
			oModel = that.getModel(),
			sNumber = oModel.getProperty("/Incident/number");
			var that = this,
				oTable = that.byId("PredictionList");
			that.setBusy(oTable,true);			
			that.getData("api/get_predictions/" + sNumber).done(function(result) {
				that._getNumberData(sNumber);
				that.setBusy(oTable,false);
			}).fail(function(result) {
				that.getPopup("prediction_error",result);
				that.setBusy(oTable,false);
			});
		},
		//Delete all predictions
		onDeletePrediction: function(oEvent){
			var that = this;
			MessageBox.confirm(that.getText("confirm_delete"),{
				onClose: function(oAction){
					if(oAction === "OK"){
						that._onDeleteAll(that);
					}
				}
			});
		},
		//Actually deletes the predictions
		_onDeleteAll(that){
			var oModel = that.getModel(),
				sNumber = oModel.getProperty("/Incident/number"),
				oTable = that.byId("PredictionList");
			that.getData("api/delete_predictions/" + sNumber).done(function(result) {
				that._getNumberData(sNumber);
				that.setBusy(oTable,false);
			}).fail(function(result) {
				that.getPopup("prediction_error",result);
				that.setBusy(oTable,false);
			});
		},
		//Send positive preditions to service now
		onSendPrediction: function(oEvent){
			var that = this,
			oModel = that.getModel(),
			aPredictions = oModel.getProperty("/Predictions"),
			sNumber = oModel.getProperty("/Incident/number"),
			aPredictionsConfig = oModel.getProperty("/PredictionsConfig");
			if(aPredictions.length == 0){
				that.getPopup("no_predictions");
				return;
			}
			//Only positive
			aPredictions = aPredictions.filter(x=> x.feedback == true);
			if(aPredictions.length == 0){
				that.getPopup("no_predictions_positive");
				return;
			}
			//Only not sent
			aPredictions = aPredictions.filter(x=> x.feedback_sent == false);
			if(aPredictions.length == 0){
				that.getPopup("no_predictions_pending");
				return;
			}
			var oPayload = {
				"notes": aPredictions.map(function(prediction) {
					//Generate the note
					var sNote = "AI Predictions:";
					aPredictionsConfig.forEach(oConfig => {
						var sKey = oConfig.key;
						var sValue = prediction[sKey];
						if(sValue){
							sNote 	= sNote + "\n" 
									+ that.getText(sKey) + ": "
									+ sValue; 
						}
					}); 
					return {
						"number": sNumber,
						"uuid": prediction.uuid,
						"note": sNote
					}
				})
			}
			var that = this,
				oTable = that.byId("PredictionList");
			that.setBusy(oTable,true);			
			that.sendPredictions(oPayload).done(function(result) {
				that._getNumberData(sNumber);
				that.setBusy(oTable,false);
				that.getPopup("prediction_sent");
			}).fail(function(result) {
				that.getPopup("prediction_sent_error",result);
				that.setBusy(oTable,false);
			});
		},
		//Send predictions to service now
		sendPredictions: function(oPayload){
			return jQuery.ajax({
				url: "api/new_note",
				type: "POST",
				dataType: 'json',
				processData: false,
				contentType: 'application/json',
				data: JSON.stringify(oPayload)
			});
		},		
	});
});      