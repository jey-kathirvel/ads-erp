class BulkDelete {

    constructor(config) {

        this.tableId = config.tableId;
        this.checkboxClass = config.checkboxClass;
        this.selectAllId = config.selectAllId;
        this.deleteBtnId = config.deleteBtnId;
        this.url = config.url;

        this.init();

    }

    init() {

        this.selectAll = document.getElementById(this.selectAllId);

        this.deleteBtn = document.getElementById(this.deleteBtnId);

        this.registerEvents();

        this.refresh();

    }

    getCheckboxes() {

        return document.querySelectorAll("." + this.checkboxClass);

    }

    getSelectedIds() {

        return [...this.getCheckboxes()]
            .filter(c => c.checked)
            .map(c => Number(c.value));

    }

    registerEvents() {

        if (this.selectAll) {

            this.selectAll.addEventListener("change", () => {

                this.getCheckboxes().forEach(cb => {

                    cb.checked = this.selectAll.checked;

                });

                this.refresh();

            });

        }

        this.getCheckboxes().forEach(cb => {

            cb.addEventListener("change", () => {

                this.refresh();

            });

        });

        this.deleteBtn.addEventListener("click", () => {

            this.deleteSelected();

        });

    }

    refresh() {

        const count = this.getSelectedIds().length;

        this.deleteBtn.disabled = count === 0;

        this.deleteBtn.innerHTML =
            `<i class="fas fa-trash"></i> Delete Selected (${count})`;

    }

async deleteSelected() {

    const ids = this.getSelectedIds();

    if (ids.length === 0) {

        alert("Please select at least one invoice.");

        return;

    }

    if (!confirm(`Delete ${ids.length} invoice(s)?`)) {

        return;

    }

    try {

        const response = await fetch("/billing/bulk-delete", {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify({

                ids: ids

            })

        });

        if (!response.ok) {

            const text = await response.text();

            alert(text);

            return;

        }

        const result = await response.json();

        alert(
            `Deleted : ${result.deleted}\nSkipped : ${result.skipped}`
        );

        location.reload();

    }
    catch (e) {

        console.error(e);

        alert(e);

    }

}

}