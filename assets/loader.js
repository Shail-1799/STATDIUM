(() => {
    const el = document.getElementById("football-loader-label");
    if (!el || el.dataset.started) return;

    el.dataset.started = "true";

    const labels = JSON.parse(el.dataset.labels);
    const interval = parseInt(el.dataset.interval);

    let i = 0;

    setInterval(() => {
        i = (i + 1) % labels.length;

        el.style.opacity = 0;

        setTimeout(() => {
            el.innerText = labels[i];
            el.style.opacity = 1;
        }, 180);

    }, interval);
})();