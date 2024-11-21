/** @odoo-module **/
import { ListController } from "@web/views/list/list_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { FormController } from "@web/views/form/form_controller";
import { Dialog } from "@web/core/dialog/dialog";
import { BarcodeDialog } from "./barcode_dialog.js";
import { useChildRef, useService } from "@web/core/utils/hooks";
import { Component, onWillUnmount, EventBus } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class ComPartnerBarcodeRender extends FormController {
    setup() {
         this.bus = new EventBus();
         this.modalRef = useChildRef();
         this.isProcess = false;
         this.dialog = useService("dialog");
         this.notificationService = useService("notification");
         
         onWillUnmount(() => {
             if (this.stream) {
                 this.stream.getTracks().forEach((track) => track.stop());
                 this.stream = null;
             }
         });
         super.setup();
     }
     
    async PartnerBarcodeDialog() {
         var self = this;
         var load_params = self.model.config;
         var model = "res.partner";
         if(load_params.resId){
             var partner_id = load_params.resId;
         } else {
             this.notificationService.add(_t("Please save the contact first"), {
                 title: _t("Save Contact"),
                 type: "danger",
             });
             return;
         }

        try {
            this.dialog.add(BarcodeDialog, {
                title: _t("Partner Barcode Scanner"),
                partner_id: load_params.resId
            });
        } catch (err) {
            console.error('Camera access error:', err);
            this.notificationService.add(_t("Failed to access camera"), {
                title: _t("Camera Error"),
                type: "danger",
            });
        }
    }
 }
 ComPartnerBarcodeRender.template = "barcode_capturing_partner.partner_scanner";


// Tree View Version
export class ComPartnerBarcodeListRender extends ListController {
    setup() {
        this.bus = new EventBus();
        this.modalRef = useChildRef();
        this.isProcess = false;
        this.dialog = useService("dialog");
        this.notificationService = useService("notification");
        
        onWillUnmount(() => {
            if (this.stream) {
                this.stream.getTracks().forEach((track) => track.stop());
                this.stream = null;
            }
        });
        super.setup();
    }

    async PartnerBarcodeDialog() {
        var self = this;
        var load_params = self.model.config;
        var model = "res.partner";
        // if(load_params.resId){
        //     var partner_id = load_params.resId;
        // } else {
        //     this.notificationService.add(_t("Please save the contact first"), {
        //         title: _t("Save Contact"),
        //         type: "danger",
        //     });
        //     return;
        // }

       try {
           this.dialog.add(BarcodeDialog, {
               title: _t("Partner Barcode Scanner"),
               partner_id: load_params.resId
           });
       } catch (err) {
           console.error('Camera access error:', err);
           this.notificationService.add(_t("Failed to access camera"), {
               title: _t("Camera Error"),
               type: "danger",
           });
       }
   }
}
ComPartnerBarcodeListRender.template = "barcode_capturing_partner.list_scanner";


// Kanban View Version
export class ComPartnerBarcodeKanbanRender extends KanbanController {
    setup() {
        this.bus = new EventBus();
        this.modalRef = useChildRef();
        this.isProcess = false;
        this.dialog = useService("dialog");
        this.notificationService = useService("notification");
        
        onWillUnmount(() => {
            if (this.stream) {
                this.stream.getTracks().forEach((track) => track.stop());
                this.stream = null;
            }
        });
        super.setup();
    }

    async PartnerBarcodeDialog() {
        var self = this;
        var load_params = self.model.config;
        var model = "res.partner";
        // if(load_params.resId){
        //     var partner_id = load_params.resId;
        // } else {
        //     this.notificationService.add(_t("Please save the contact first"), {
        //         title: _t("Save Contact"),
        //         type: "danger",
        //     });
        //     return;
        // }

       try {
           this.dialog.add(BarcodeDialog, {
               title: _t("Partner Barcode Scanner"),
               partner_id: load_params.resId
           });
       } catch (err) {
           console.error('Camera access error:', err);
           this.notificationService.add(_t("Failed to access camera"), {
               title: _t("Camera Error"),
               type: "danger",
           });
       }
   }
}
ComPartnerBarcodeKanbanRender.template = "barcode_capturing_partner.kanban_scanner";