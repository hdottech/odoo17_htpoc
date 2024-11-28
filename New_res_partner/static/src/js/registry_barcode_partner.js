/** @odoo-module **/
import { formView } from '@web/views/form/form_view';
import { listView } from "@web/views/list/list_view";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { FormController } from '@web/views/form/form_controller';
import { registry } from "@web/core/registry";
import { ComPartnerBarcodeRender,ComPartnerBarcodeListRender,ComPartnerBarcodeKanbanRender } from './partner_barcode';

export const JsClassBarcodePartner = {
   ...formView,
   Controller: ComPartnerBarcodeRender,
};
registry.category("views").add("partner_barcode_form", JsClassBarcodePartner);


// List View Registration
export const JsClassBarcodePartnerList = {
   ...listView,
   Controller: ComPartnerBarcodeListRender,
};
registry.category("views").add("partner_barcode_list", JsClassBarcodePartnerList);


// Kanban View Registration
export const JsClassBarcodePartnerKanban = {
   ...kanbanView,
   Controller: ComPartnerBarcodeKanbanRender,
};
registry.category("views").add("partner_barcode_kanban", JsClassBarcodePartnerKanban);