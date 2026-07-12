/* ============================================================================
 * ADS ERP
 * Enterprise Bulk Edit Framework
 * File : app/static/js/bulk-edit.js
 * Version : 1.0
 * ========================================================================== */

class BulkEdit {

    constructor(config) {

        this.tableId = config.tableId;
        this.checkboxClass = config.checkboxClass;
        this.selectAllId = config.selectAllId;
        this.bulkEditBtnId = config.bulkEditBtnId;
        this.bulkDeleteBtnId = config.bulkDeleteBtnId;
        this.modalId = config.modalId;
        this.formId = config.formId;

        this.init();

    }

    init() {

        this.table = document.getElementById(this.tableId);

        this.selectAll =
            document.getElementById(this.selectAllId);

        this.bulkEditBtn =
            document.getElementById(this.bulkEditBtnId);

        this.bulkDeleteBtn =
            document.getElementById(this.bulkDeleteBtnId);

        this.modal =
            document.getElementById(this.modalId);

        this.form =
            document.getElementById(this.formId);

        this.registerCheckboxEvents();

        this.registerToolbarEvents();

        this.refreshToolbar();

    }

    registerCheckboxEvents() {

        if (this.selectAll) {

            this.selectAll.addEventListener("change", () => {

                this.getCheckboxes().forEach(cb => {

                    cb.checked = this.selectAll.checked;

                });

                this.refreshToolbar();

            });

        }

        this.getCheckboxes().forEach(cb => {

            cb.addEventListener("change", () => {

                this.refreshToolbar();

            });

        });

    }

    registerToolbarEvents() {

        if (this.bulkEditBtn) {

            this.bulkEditBtn.addEventListener("click", () => {

                this.openModal();

            });

        }

        if (this.bulkDeleteBtn) {

            this.bulkDeleteBtn.addEventListener("click", async () => {

                const ids = this.getSelectedIds();

                if (ids.length === 0) {

                    alert("Please select at least one record.");

                    return;

                }

                if (!confirm("Delete selected customers?")) {

                    return;

                }

                const response = await fetch("/customers/bulk-delete", {

                    method: "POST",

                    headers: {

                        "Content-Type": "application/json"

                    },

                    body: JSON.stringify({

                        ids: ids

                    })

                });

                const result = await response.json();

                alert(
                    "Deleted : " + result.deleted +
                    "\nSkipped : " + result.skipped
                );

                location.reload();

            });

        }

    }

    getCheckboxes() {

        return document.querySelectorAll(

            "." + this.checkboxClass

        );

    }

    getSelectedIds() {

        return [...this.getCheckboxes()]

            .filter(c => c.checked)

            .map(c => parseInt(c.value));

    }

    refreshToolbar() {

        const count = this.getSelectedIds().length;

        if (this.bulkEditBtn) {

            this.bulkEditBtn.disabled = count === 0;

            this.bulkEditBtn.innerHTML =
                "Bulk Edit (" + count + ")";

        }

        if (this.bulkDeleteBtn) {

            this.bulkDeleteBtn.disabled = count === 0;

            this.bulkDeleteBtn.innerHTML =
                "Delete Selected (" + count + ")";

        }

        if (this.selectAll) {

            const total = this.getCheckboxes().length;

            this.selectAll.checked =
                total > 0 && count === total;

        }

    }

    openModal() {

        if (this.getSelectedIds().length === 0) {
            alert("Please select at least one record.");
            return;
        }

        if (window.jQuery) {
            $("#bulkEditModal").modal("show");
        } else {
            this.modal.style.display = "block";
            this.modal.classList.add("show");
        }

    }

    closeModal() {

        if (window.jQuery) {
            $("#bulkEditModal").modal("hide");
        } else {
            this.modal.classList.remove("show");
            this.modal.style.display = "none";
        }

    }

    async submit(url) {

        const ids = this.getSelectedIds();

        if (ids.length === 0)
            return;

        const formData = new FormData(this.form);

        let fields = {};

        formData.forEach((value, key) => {

            if (value !== "")
                fields[key] = value;

        });

        const response = await fetch(url, {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify({

                ids: ids,

                fields: fields

            })

        });

        const result = await response.json();

        alert(

            "Updated : " + result.updated +

            "\nSkipped : " + result.skipped

        );

        location.reload();

    }

}