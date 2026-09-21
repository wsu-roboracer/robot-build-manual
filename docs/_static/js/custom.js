// Custom JavaScript for Robot Build Manual
document.addEventListener("DOMContentLoaded", function () {
    const body = document.body;

    // Create the toggle button
    const button = document.createElement("button");
    button.className = "sidebar-toggle";
    button.setAttribute("aria-label", "Hide navigation");
    button.setAttribute("title", "Hide navigation");
    button.innerHTML = "‹";

    // Add the button to the page
    document.body.appendChild(button);

    button.addEventListener("click", function () {
        body.classList.toggle("sidebar-collapsed");

        const collapsed = body.classList.contains("sidebar-collapsed");

        // Change the arrow depending on sidebar state
        button.innerHTML = collapsed ? "›" : "‹";

        button.setAttribute(
            "aria-label",
            collapsed ? "Show navigation" : "Hide navigation"
        );

        button.setAttribute(
            "title",
            collapsed ? "Show navigation" : "Hide navigation"
        );
    });
});
