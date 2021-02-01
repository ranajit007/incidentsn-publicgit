sap.ui.define([
	"sap/ui/core/UIComponent",
	"sap/ui/Device",
	"./model/models",
	"sap/f/FlexibleColumnLayoutSemanticHelper"
], function(UIComponent, Device, models, JSONModel, jQuery, FlexibleColumnLayoutSemanticHelper) {
	"use strict";

	return UIComponent.extend("ui.kolki.Component", {

		metadata: {
			manifest: "json"
		},

		init: function() {

			UIComponent.prototype.init.apply(this, arguments);
			this.setModel(models.createDeviceModel(), "device");
			this.getRouter().initialize();
		}
	});
});