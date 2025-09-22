// ticker.js
document.addEventListener("DOMContentLoaded", function () {
    const downloadBtn = document.getElementById("download-link");
    const chartImg = document.getElementById("chart-img");

    if (downloadBtn && chartImg) {
        downloadBtn.addEventListener("click", function () {
            const image = chartImg.src;
            downloadBtn.href = image;
        });
    }
});