sap.ui.define([], function () {
	"use strict";

	return {
		/**
		 * Rounds the currency value to 2 digits
		 *
		 * @public
		 * @param {string} sValue value to be formatted
		 * @returns {string} formatted currency value with 2 digits
		 */
		currencyValue : function (sValue) {
			if (!sValue) {
				return "";
			}
			return parseFloat(sValue).toFixed(2);
		},
		//Text for feedback input
		feedbackText : function (bValue) {
			var oController = this.oView.getController();
			var sKey = oController.getFeedbackKey(bValue);
			return oController.getText(sKey);
		},
		//Icon for feedback input
		feedbackIcon: function (bValue){
			var oController = this.oView.getController();
			var sKey = oController.getFeedbackKey(bValue,"_ICON");
			return oController.getText(sKey);
		},
		//State for feedback input
		feedbackState: function (bValue){
			var oController = this.oView.getController();
			var sKey = oController.getFeedbackKey(bValue,"_STATE");
			return oController.getText(sKey);
		},		
		//Text for prediction type
		predictionType: function (sKey){
			if(!sKey) return "";
			var oController = this.oView.getController();
			return oController.getText(sKey);
		}
	};
});