document.addEventListener("DOMContentLoaded", function () {
    console.log("JS loaded");
});

function toggleReply(id) {
    let box = document.getElementById("reply-box-" + id);
    box.style.display = box.style.display === "none" ? "block" : "none";
}
