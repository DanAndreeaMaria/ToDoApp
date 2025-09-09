// Script for changing the backgground color for the deleted tasks

document.querySelectorAll(".delete-btn").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.preventDefault(); // prevent the form from submitting

    const taskId = btn.dataset.id;
    const li = btn.closest("li"); // get the parent <li>

    // Step 1: Turn background red
    li.style.transition = "background-color 0.5s, opacity 0.5s";
    li.style.backgroundColor = "#f8d7da"; // light red
    li.style.opacity = "0.6";

    // Step 2: Wait 500ms, then remove from DOM
    setTimeout(() => {
      fetch(`/delete_task/${taskId}`, { method: "POST" })
        .then(() => li.remove()) // remove element after server confirms
        .catch((err) => console.error(err));
    }, 500);
  });
});
