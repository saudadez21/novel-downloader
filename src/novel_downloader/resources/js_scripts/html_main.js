document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupImageFullscreen();
  setupScrollButtons();
  setupFontControls();
  setupProgressBar();
  setupFloatingMenuButton();
  setupAutoHideFloatingControls();
  setupStickyNavToggle();
});

function setupNavigation() {
  const nav = document.querySelector(".chapter-nav");
  if (!nav) return;

  const prev = document.getElementById("prev-link");
  const next = document.getElementById("next-link");

  if (!nav.dataset.prev) {
    prev.classList.add("disabled");
    prev.removeAttribute("href");
  }
  if (!nav.dataset.next) {
    next.classList.add("disabled");
    next.removeAttribute("href");
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft" && nav.dataset.prev) window.location.href = nav.dataset.prev;
    else if (e.key === "ArrowRight" && nav.dataset.next) window.location.href = nav.dataset.next;
    else if (e.key === "Escape") window.location.href = nav.dataset.menu;
  });
}

function setupFloatingMenuButton() {
  const menuBtn = document.getElementById("menu-button");
  const fc = document.getElementById("floating-controls");
  if (!menuBtn || !fc) return;
  const menuLink = fc.dataset.menu || "../index.html";
  menuBtn.addEventListener("click", () => {
    window.location.href = menuLink;
  });
}

function setupImageFullscreen() {
  if (!document.getElementById("img-overlay")) {
    const overlay = document.createElement("div");
    overlay.id = "img-overlay";
    overlay.className = "hidden";
    overlay.innerHTML = '<img id="img-fullscreen" src="" alt="">';
    document.body.appendChild(overlay);
  }

  const overlay = document.getElementById("img-overlay");
  const fullImg = document.getElementById("img-fullscreen");

  document.querySelectorAll("img").forEach((img) => {
    img.addEventListener("click", () => {
      if (img.closest("#img-overlay")) return;
      fullImg.src = img.src;
      overlay.classList.remove("hidden");
    });
  });

  overlay.addEventListener("click", () => {
    overlay.classList.add("hidden");
    fullImg.src = "";
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !overlay.classList.contains("hidden")) {
      overlay.classList.add("hidden");
      fullImg.src = "";
    }
  });
}

function setupScrollButtons() {
  const topBtn = document.getElementById("scroll-top");
  const bottomBtn = document.getElementById("scroll-bottom");
  if (topBtn) topBtn.onclick = () => window.scrollTo({ top: 0, behavior: "smooth" });
  if (bottomBtn) bottomBtn.onclick = () =>
    window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
}

function setupFontControls() {
  const plus = document.getElementById("font-plus");
  const minus = document.getElementById("font-minus");
  let size = parseFloat(localStorage.getItem("fontSize") || "1");
  document.body.style.fontSize = size + "em";
  function changeSize(delta) {
    size = Math.min(2, Math.max(0.8, size + delta));
    document.body.style.fontSize = size + "em";
    localStorage.setItem("fontSize", size);
  }
  if (plus) plus.onclick = () => changeSize(0.1);
  if (minus) minus.onclick = () => changeSize(-0.1);
}

function setupProgressBar() {
  const bar = document.getElementById("progress-bar");
  if (!bar) return;
  window.addEventListener("scroll", () => {
    const scrollTop = window.scrollY;
    const docHeight = document.body.scrollHeight - window.innerHeight;
    const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    bar.style.width = progress + "%";
  });
}

function setupAutoHideFloatingControls() {
  const fc = document.getElementById("floating-controls");
  if (!fc) return;
  let hideTimer;
  document.addEventListener("mousemove", () => {
    fc.classList.remove("hidden");
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => fc.classList.add("hidden"), 2500);
  });
}

function setupStickyNavToggle() {
  const btn = document.getElementById("toggle-sticky");
  const nav = document.querySelector(".chapter-nav");
  if (!btn || !nav) return;

  // Restore saved preference
  const stickyEnabled = localStorage.getItem("stickyNav") === "true";
  if (stickyEnabled) nav.classList.add("sticky");
  updateButtonState();

  btn.addEventListener("click", () => {
    nav.classList.toggle("sticky");
    const enabled = nav.classList.contains("sticky");
    localStorage.setItem("stickyNav", enabled);
    updateButtonState();
  });

  function updateButtonState() {
    if (nav.classList.contains("sticky")) {
      btn.textContent = "S*"; // active indicator
      btn.title = "取消固定导航";
    } else {
      btn.textContent = "S";
      btn.title = "固定导航";
    }
  }
}
