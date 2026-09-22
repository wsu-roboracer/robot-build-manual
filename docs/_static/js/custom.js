// Custom JavaScript for Robot Build Manual
document.addEventListener("DOMContentLoaded", function () {
    const button = document.createElement("button");

    button.id = "sidebar-toggle";
    button.textContent = "MENU";

    document.body.appendChild(button);

    button.addEventListener("click", function () {
        document.body.classList.toggle("sidebar-collapsed");
    });
});
