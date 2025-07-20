/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class PaymentWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            amount: 0,
            payment_method: null,
            reference: '',
            processing: false
        });
    }

    async processPayment() {
        if (!this.state.amount || !this.state.payment_method) {
            this.notification.add("Veuillez remplir tous les champs requis", {
                type: "warning"
            });
            return;
        }

        this.state.processing = true;
        
        try {
            const result = await this.orm.call(
                "edu.student.payment",
                "process_payment",
                [{
                    amount: this.state.amount,
                    payment_method_id: this.state.payment_method,
                    reference: this.state.reference,
                    invoice_id: this.props.invoice_id
                }]
            );

            if (result.success) {
                this.notification.add("Paiement traité avec succès", {
                    type: "success"
                });
                
                // Émettre un événement pour actualiser la vue parent
                this.trigger('payment-processed', result);
            } else {
                this.notification.add(result.error || "Erreur lors du traitement", {
                    type: "danger"
                });
            }
        } catch (error) {
            console.error("Erreur de paiement:", error);
            this.notification.add("Erreur lors du traitement du paiement", {
                type: "danger"
            });
        } finally {
            this.state.processing = false;
        }
    }

    onAmountChange(event) {
        this.state.amount = parseFloat(event.target.value) || 0;
    }

    onPaymentMethodChange(event) {
        this.state.payment_method = parseInt(event.target.value) || null;
    }

    onReferenceChange(event) {
        this.state.reference = event.target.value;
    }
}

PaymentWidget.template = "edu_accounting_pro.PaymentWidget";
PaymentWidget.props = {
    invoice_id: { type: Number, optional: true },
    amount: { type: Number, optional: true },
    payment_methods: { type: Array, optional: true }
};

registry.category("components").add("PaymentWidget", PaymentWidget);
