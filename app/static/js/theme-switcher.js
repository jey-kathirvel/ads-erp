(function () {

    function loadTheme() {

        const savedTheme =
            localStorage.getItem("ads-theme") || "dark";

        applyTheme(savedTheme);

    }

    function applyTheme(theme) {

        document.body.setAttribute(
            "data-theme",
            theme
        );

        const themeCss =
            document.getElementById("ads-theme-css");

        if (themeCss) {

            themeCss.href =
                theme === "light"
                    ? "/static/css/ads-light.css?v=1"
                    : "/static/css/ads-dark.css?v=1";

        }

        localStorage.setItem(
            "ads-theme",
            theme
        );

        updateButton(theme);

    }

    function updateButton(theme) {

        const btn =
            document.getElementById("themeToggle");

        if (!btn) return;

        btn.innerHTML =
            theme === "dark"
                ? '<i class="fas fa-sun"></i>'
                : '<i class="fas fa-moon"></i>';

        btn.title =
            theme === "dark"
                ? "Switch to Light Theme"
                : "Switch to Dark Theme";

    }

    function toggleTheme() {

        const current =
            document.body.getAttribute("data-theme") || "dark";

        applyTheme(
            current === "dark"
                ? "light"
                : "dark"
        );

    }

    document.addEventListener(
        "DOMContentLoaded",
        function () {

            loadTheme();

            const btn =
                document.getElementById("themeToggle");

            if (btn) {

                btn.addEventListener(
                    "click",
                    toggleTheme
                );

            }

        }
    );

})();