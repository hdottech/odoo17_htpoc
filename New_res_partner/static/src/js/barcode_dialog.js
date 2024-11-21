/** @odoo-module */
import { browser } from "@web/core/browser/browser";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useChildRef, useService } from "@web/core/utils/hooks";
import { Component, useRef, onWillUnmount } from "@odoo/owl";
var beep = new Audio('/barcode_capturing_sale_purchase/static/src/audio/beep_scan.mp3');

//BarcodeDialog is a component that captures barcode input through the device's camera,
// processes the scanned barcode, and interacts with the Odoo backend to perform
//  actions based on the scanned data.
export class BarcodeDialog extends Component {
    async setup() {
        super.setup();
        this.env.dialogData.dismiss = () => this._cancel();
        this.orm = useService('orm');
        this.notificationService = useService("notification");
        this.modalRef = useChildRef();
        this.videoPreviewRef = useRef("videoPreview");
        this.isMounted = true;

        // Cleanup function to stop video stream when component unmounts
        onWillUnmount(() => {
            this.isMounted = false;
            this._stopVideoStream();
        });

        this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        this.videoPreviewRef.el.srcObject = this.stream;
        this.videoPreviewRef.el.play();

        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                constraints: {
                    video: {
                        facingMode: { exact: "environment" }
                    }
                },
                numOfWorkers: navigator.hardwareConcurrency,
                target: this.videoPreviewRef.el,
            },
            decoder: {
                readers: ['code_128_reader']
            }
        }, (err) => {
            if (err) {
                return;
            }
            Quagga.start();
        });

        Quagga.onDetected((result) => {
            if (!this.isMounted) return;
            var barcode = result.codeResult.code;
            Quagga.offDetected();
            Quagga.stop();
            this.scan_product(barcode);
        });
    }
    //    Handles the cancellation of the dialog.
    async _cancel() {
        return this.execButton(this.props.cancel);
    }
    //    Handles the confirmation of the dialog.
    async _dialogConfirm() {
        return this.execButton(this.props.confirm);
    }
    //  Processes the scanned product by barcode.
    async scan_product(barcode) {
        if (!this.isMounted) return;
        var last_code = barcode;
        var last_result = [];
        last_result.push(last_code);
        last_result = [];
        Quagga.stop();
        var partner_id = this.props.partner_id;
        var method = this.props.model === "res.partner";
        try {
            const data = await this.orm.call("res.partner", "barcode_search", [last_code, partner_id]);
            if (!this.isMounted) return;

            if (data === true) {
                this.notificationService.add(_t("找不到該聯絡人"), {
                    title: _t("掃描失敗"),
                    type: "danger",
                });
            } else if(data === false){
                // const notificationMessage = this._formatPartnerNotification(data);
                this.notificationService.add(_t("不可入場"), {
                    title: _t("掃描失敗"),
                    type: "danger",
                });
            }else{
                this.notificationService.add(_t("可以入場"), {
                    title: _t("掃描成功"),
                    type: "success",
                });
            }
        } catch (error) {
            if (this.isMounted) {
                console.error("Error scanning : ", error);
            }
        }

        this._stopVideoStream();
        this.props.close();
    }
    //   Stops the video stream if it is active.
    _stopVideoStream() {
        if (this.videoPreviewRef.el && this.videoPreviewRef.el.srcObject) {
            const tracks = this.videoPreviewRef.el.srcObject.getTracks();
            tracks.forEach((track) => track.stop());
        }
    }
    // sets button disabled
    setButtonsDisabled(disabled) {
        this.isProcess = disabled;
        if (!this.modalRef.el) {
            return;
        }
        for (const button of [...this.modalRef.el.querySelectorAll(".modal-footer button")]) {
            button.disabled = disabled;
        }
    }

    async execButton(callback) {
        if (this.isProcess) {
            return;
        }
        this.setButtonsDisabled(true);
        if (callback) {
            let shouldClose;
            try {
                shouldClose = await callback();
            } catch (e) {
                this.props.close();
                throw e;
            }
            if (shouldClose === false) {
                this.setButtonsDisabled(false);
                return;
            }
        }
        Quagga.stop();
        this._stopVideoStream();
        this.props.close();
    }
}

BarcodeDialog.template = "BarcodeDialog";
BarcodeDialog.components = { Dialog };
BarcodeDialog.props = {
    close: Function,
    order_id: Number,
    model: String,
    title: {
        validate: (m) => {
            return (
                typeof m === "string" || (typeof m === "object" && typeof m.toString === "function")
            );
        },
        optional: true,
    },
    body: String,
    confirm: { type: Function, optional: true },
    confirmLabel: { type: String, optional: true },
    confirmClass: { type: String, optional: true },
    cancel: { type: Function, optional: true },
    cancelLabel: { type: String, optional: true },
};
BarcodeDialog.defaultProps = {
    confirmLabel: _t("Ok"),
    cancelLabel: _t("Cancel"),
    confirmClass: "btn-primary",
    title: _t("Confirmation"),
};
