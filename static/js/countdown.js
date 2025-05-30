document.addEventListener("DOMContentLoaded", () => {
  const estimatedTime = parseInt(document.getElementById("countdown").dataset.time);

  let seconds = estimatedTime;
  const countdownEl = document.getElementById("countdown");
  const progressBar = document.getElementById("progress-bar");

  function updateCountdown() {
    let minutes = Math.floor(seconds / 60);
    let secs = seconds % 60;
    countdownEl.textContent = `${minutes}m ${secs}s`;

    let percent = Math.max((seconds / estimatedTime) * 100, 0);
    progressBar.style.width = `${percent}%`;
    progressBar.setAttribute('aria-valuenow', percent.toFixed(0));

    if (seconds > 0) {
      seconds--;
      setTimeout(updateCountdown, 1000);
    } else {
      countdownEl.textContent = "✅ Done";
      progressBar.classList.remove("progress-bar-animated");
    }
  }

  if (estimatedTime > 0) updateCountdown();
});
