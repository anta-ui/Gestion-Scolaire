/**
 * Widgets du tableau de bord du portail parents
 * ===========================================
 */

odoo.define('edu_parent_portal.dashboard_widgets', function (require) {
    'use strict';
    
    var Widget = require('web.Widget');
    var core = require('web.core');
    
    var DashboardWidget = Widget.extend({
        template: 'edu_parent_portal.DashboardWidget',
        
        init: function(parent, options) {
            this._super(parent);
            this.options = options || {};
        },
        
        start: function() {
            var self = this;
            return this._super().then(function() {
                self._renderWidget();
            });
        },
        
        _renderWidget: function() {
            // Logique de rendu du widget
            console.log('Dashboard widget rendered');
        }
    });
    
    return {
        DashboardWidget: DashboardWidget
    };
});
