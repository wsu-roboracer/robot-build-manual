// Custom JavaScript for Robot Build Manual
document.addEventListener("DOMContentLoaded", function () {
    const body = document.body;

    const button = document.createElement("button");
    button.className = "sidebar-toggle";
    button.setAttribute("aria-label", "Toggle navigation");
    button.setAttribute("title", "Toggle navigation");
    button.innerHTML = "<span></span><span></span><span></span>";

    document.body.appendChild(button);

    button.addEventListener("click", function () {
        body.classList.toggle("sidebar-collapsed");
    });
});
