/* =========================================================
   QuizNest — main.js
   Shared behaviour: navbar scroll state, scroll-reveal, footer year
   ========================================================= */
document.addEventListener("DOMContentLoaded", function () {

  /* ---- Footer year ---- */
  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---- Navbar background on scroll ---- */
  var navbar = document.getElementById("qsNavbar");
  function updateNavbar() {
    if (!navbar) return;
    if (window.scrollY > 24) {
      navbar.classList.add("qs-scrolled");
    } else {
      navbar.classList.remove("qs-scrolled");
    }
  }
  updateNavbar();
  window.addEventListener("scroll", updateNavbar, { passive: true });

  /* ---- Scroll-reveal animation ---- */
  var revealEls = document.querySelectorAll(".qs-reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var delay = entry.target.getAttribute("data-delay");
            if (delay) {
              entry.target.style.transitionDelay = delay + "ms";
            }
            entry.target.classList.add("qs-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach(function (el) { observer.observe(el); });
  } else {
    // Fallback: reveal everything immediately
    revealEls.forEach(function (el) { el.classList.add("qs-visible"); });
  }

  /* ---- Auto-close mobile navbar after clicking a link ---- */
  var navLinks = document.querySelectorAll("#qsNav .nav-link, #qsNav .btn");
  var navCollapseEl = document.getElementById("qsNav");
  if (navCollapseEl && window.bootstrap) {
    var bsCollapse = new bootstrap.Collapse(navCollapseEl, { toggle: false });
    navLinks.forEach(function (link) {
      link.addEventListener("click", function () {
        if (navCollapseEl.classList.contains("show")) {
          bsCollapse.hide();
        }
      });
    });
  }
});
