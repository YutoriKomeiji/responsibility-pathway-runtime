/*
Language: JavaScript
Purpose: Progressive enhancement and demo navigation for the static RPR public website.
Boundary: No analytics, network calls, storage, credentials, or runtime control.
*/
(() => {
  "use strict";

  const isJapanese = document.documentElement.lang === "ja";
  const nav = document.querySelector(".site-header nav");
  if (nav && !nav.querySelector('a[href="demo.html"]')) {
    const demoLink = document.createElement("a");
    demoLink.href = "demo.html";
    demoLink.textContent = isJapanese ? "状態遷移デモ" : "State demo";
    const languageLink = nav.querySelector('[hreflang]');
    nav.insertBefore(demoLink, languageLink || null);
  }

  const demoSection = document.getElementById("demo");
  if (demoSection) {
    const actions = demoSection.querySelector(".actions");
    if (actions && !actions.querySelector('a[href="demo.html"]')) {
      const demoButton = document.createElement("a");
      demoButton.className = "button primary";
      demoButton.href = "demo.html";
      demoButton.textContent = isJapanese ? "ブラウザ内デモを試す" : "Try the browser demo";
      actions.prepend(demoButton);
    }
  }

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const targets = document.querySelectorAll(".reveal");

  if (reducedMotion || !("IntersectionObserver" in window)) {
    targets.forEach((element) => element.classList.add("visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      });
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
  );

  targets.forEach((element) => observer.observe(element));
})();
