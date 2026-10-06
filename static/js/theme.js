// Appearance setting: "system" (follow the device), "light" or "dark".
// The choice is saved in localStorage; base.html applies it before paint.
(function () {
  "use strict";

  const STORAGE_KEY = "theme";
  const root = document.documentElement;
  const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

  function readSaved() {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      return value === "light" || value === "dark" ? value : "system";
    } catch (e) {
      return "system";
    }
  }

  function save(value) {
    try {
      if (value === "system") localStorage.removeItem(STORAGE_KEY);
      else localStorage.setItem(STORAGE_KEY, value);
    } catch (e) {
      // Storage blocked (private mode etc.): the choice still applies for this page.
    }
  }

  function apply(value) {
    if (value === "light" || value === "dark") root.dataset.theme = value;
    else delete root.dataset.theme;
  }

  // --- Panel ---
  const toggle = document.getElementById("settings-toggle");
  const panel = document.getElementById("settings-panel");
  const wrapper = document.getElementById("settings");
  const systemHint = document.getElementById("theme-system-hint");
  if (!toggle || !panel) return;

  function setOpen(open) {
    panel.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
    if (open) {
      const checked = panel.querySelector('input[name="theme"]:checked');
      if (checked) checked.focus();
    }
  }

  toggle.addEventListener("click", function () {
    setOpen(panel.hidden);
  });

  document.addEventListener("click", function (event) {
    if (!panel.hidden && !wrapper.contains(event.target)) setOpen(false);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !panel.hidden) {
      setOpen(false);
      toggle.focus();
    }
  });

  // --- Theme radios ---
  const radios = panel.querySelectorAll('input[name="theme"]');
  const current = readSaved();
  radios.forEach(function (radio) {
    radio.checked = radio.value === current;
    radio.addEventListener("change", function () {
      if (!radio.checked) return;
      save(radio.value);
      apply(radio.value);
    });
  });

  function updateSystemHint() {
    if (systemHint) systemHint.textContent = darkQuery.matches ? "dark" : "light";
  }
  updateSystemHint();
  darkQuery.addEventListener("change", updateSystemHint);
})();
