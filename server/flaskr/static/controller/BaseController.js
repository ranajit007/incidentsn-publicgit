 
sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/core/UIComponent",
	"../model/formatter"
  ], function (Controller, UIComponent,formatter) {
    "use strict";
   
    return Controller.extend("ui.kolki.controller.BaseController", {
		formatter: formatter,
        // just this.getRouter() ...
        getRouter: function () {
            return UIComponent.getRouterFor(this);
        },
        // just this.getModel() ...
        getModel: function (sName) {
            return this.getView().getModel(sName);
        },
        // just this.setModel() ...
        setModel: function (oModel, sName) {
            return this.getView().setModel(oModel, sName);
        },
        // just this.getResoureBundle() ... 
        getResourceBundle: function () {
            return this.getOwnerComponent().getModel("i18n").getResourceBundle();
        },
        //get Text
        getText: function(sKey){
            return this.getResourceBundle().getText(sKey);
        },
        //Shows popup
        getPopup: function(sKey, oError){
            if(!!oError){
                console.log(oError);
            }
            sap.m.MessageToast.show(this.getText(sKey));
        },
        //Sets or resets default indicator
        setBusy: function(element,indicator){
            element.setBusy(indicator)
        },
        //Gets service promise
		getData: function(url){
			return jQuery.ajax({
				url: url,
				type: "GET"
			});
        },   
        //Returns text key for feedback
		getFeedbackKey: function(bValue,type=""){
			var sKey = "FeedbackPending";
			switch (bValue){
				default:
					sKey = "FeedbackPending";
					break;
				case true:
					sKey =  "FeedbackTrue";
					break;
				case false:
					sKey =  "FeedbackFalse";
					break;
			}
			return sKey + type;
        },  
        //Send information to CRUD service:
		sendCRUD_ProposedProcedure: function(aUpdate=[], aDelete=[],aCreate=[]){
			var oPayload = {
				"delete": aDelete,
				"update": aUpdate,
				"create": aCreate
			}
			return jQuery.ajax({
				url: "api/CRUD/ProposedProcedure",
				type: "POST",
				dataType: 'json',
				processData: false,
				contentType: 'application/json',
				data: JSON.stringify(oPayload)
			});
		},
    });
   
  });