/* =========================================================
   Decore — app.js
   UI interactivity: sidebar toggle, dark mode, loading
   spinner helpers, toast helper, confirmation modal helper.
   Includes localStorage state persistence for theme & sidebar.
   ========================================================= */

(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    restorePersistedStates();
    initSidebarToggle();
    initDarkModeToggle();
    initTooltips();
    hideInitialLoader();
    initProgressBarAnimations();
    initHoverPrefetch();
  });

  /* ---------------------------------------------------------
     State Persistence (Theme and Sidebar Collapse)
     --------------------------------------------------------- */
  function restorePersistedStates() {
    var root = document.documentElement;
    var wrapper = document.querySelector(".decore-wrapper");

    // Restore Theme
    var savedTheme = localStorage.getItem("decore-theme") || "light";
    root.setAttribute("data-bs-theme", savedTheme);

    // Sync header icon if it exists
    var themeToggle = document.getElementById("darkModeToggle");
    if (themeToggle) {
      var icon = themeToggle.querySelector(".bi");
      if (icon) {
        icon.className = savedTheme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
      }
    }

    // Sync settings page switch if it exists
    var themeSwitch = document.getElementById("darkModeSwitch");
    if (themeSwitch) {
      themeSwitch.checked = (savedTheme === "dark");
    }

    // Restore Sidebar State
    var savedSidebar = localStorage.getItem("decore-sidebar-collapsed");
    if (savedSidebar === "true" && wrapper) {
      wrapper.classList.add("sidebar-collapsed");
    }

    // Sync settings page switch if it exists
    var sidebarSwitch = document.getElementById("compactSidebar");
    if (sidebarSwitch && wrapper) {
      sidebarSwitch.checked = wrapper.classList.contains("sidebar-collapsed");
    }
  }

  /* ---------------------------------------------------------
     Sidebar toggle (desktop collapse / mobile off-canvas)
     --------------------------------------------------------- */
  function initSidebarToggle() {
    var wrapper = document.querySelector(".decore-wrapper");
    var desktopToggle = document.getElementById("sidebarToggleDesktop");
    var mobileToggle = document.getElementById("sidebarToggleMobile");
    var backdrop = document.querySelector(".decore-sidebar-backdrop");
    var settingsSidebarSwitch = document.getElementById("compactSidebar");

    function setSidebarCollapsed(collapsed) {
      if (!wrapper) return;
      if (collapsed) {
        wrapper.classList.add("sidebar-collapsed");
      } else {
        wrapper.classList.remove("sidebar-collapsed");
      }
      localStorage.setItem("decore-sidebar-collapsed", collapsed);

      // Keep settings checkbox in sync
      if (settingsSidebarSwitch) {
        settingsSidebarSwitch.checked = collapsed;
      }
    }

    if (desktopToggle && wrapper) {
      desktopToggle.addEventListener("click", function () {
        var nextState = !wrapper.classList.contains("sidebar-collapsed");
        setSidebarCollapsed(nextState);
      });
    }

    if (settingsSidebarSwitch && wrapper) {
      settingsSidebarSwitch.addEventListener("change", function () {
        setSidebarCollapsed(settingsSidebarSwitch.checked);
      });
    }

    if (mobileToggle && wrapper) {
      mobileToggle.addEventListener("click", function () {
        wrapper.classList.toggle("sidebar-mobile-open");
      });
    }

    if (backdrop && wrapper) {
      backdrop.addEventListener("click", function () {
        wrapper.classList.remove("sidebar-mobile-open");
      });
    }
  }

  /* ---------------------------------------------------------
     Dark mode toggle (UI only — swaps Bootstrap color mode)
     --------------------------------------------------------- */
  function initDarkModeToggle() {
    var toggle = document.getElementById("darkModeToggle");
    var themeSwitch = document.getElementById("darkModeSwitch");
    var root = document.documentElement;

    function applyTheme(theme) {
      root.classList.add("theme-transitioning");
      root.setAttribute("data-bs-theme", theme);
      localStorage.setItem("decore-theme", theme);

      setTimeout(function() {
        root.classList.remove("theme-transitioning");
      }, 500);

      // Sync header icon
      if (toggle) {
        var icon = toggle.querySelector(".bi");
        if (icon) {
          icon.className = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
        }
      }

      // Sync settings switch
      if (themeSwitch) {
        themeSwitch.checked = (theme === "dark");
      }
    }

    if (toggle) {
      toggle.addEventListener("click", function () {
        var current = root.getAttribute("data-bs-theme");
        var next = current === "dark" ? "light" : "dark";
        applyTheme(next);
      });
    }

    if (themeSwitch) {
      themeSwitch.addEventListener("change", function () {
        var next = themeSwitch.checked ? "dark" : "light";
        applyTheme(next);
      });
    }
  }

  /* ---------------------------------------------------------
     Bootstrap tooltips
     --------------------------------------------------------- */
  function initTooltips() {
    if (typeof bootstrap === "undefined") return;
    var triggers = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    triggers.forEach(function (el) {
      new bootstrap.Tooltip(el);
    });
  }

  /* ---------------------------------------------------------
     Loading overlay helpers
     --------------------------------------------------------- */
  function hideInitialLoader() {
    var overlay = document.getElementById("decoreLoadingOverlay");
    if (overlay) {
      overlay.classList.remove("active");
    }
  }

  window.decoreShowLoading = function () {
    var overlay = document.getElementById("decoreLoadingOverlay");
    if (overlay) overlay.classList.add("active");
  };

  window.decoreHideLoading = function () {
    var overlay = document.getElementById("decoreLoadingOverlay");
    if (overlay) overlay.classList.remove("active");
  };

  /* ---------------------------------------------------------
     Toast helper
     Usage: decoreToast("Saved successfully", "success")
     --------------------------------------------------------- */
  window.decoreToast = function (message, variant) {
    variant = variant || "primary";
    var container = document.getElementById("decoreToastContainer");
    if (!container || typeof bootstrap === "undefined") return;

    var wrapper = document.createElement("div");
    wrapper.className = "toast align-items-center text-bg-" + variant + " border-0";
    wrapper.setAttribute("role", "alert");
    wrapper.setAttribute("aria-live", "assertive");
    wrapper.setAttribute("aria-atomic", "true");
    wrapper.innerHTML =
      '<div class="d-flex">' +
      '<div class="toast-body">' + message + "</div>" +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>' +
      "</div>";

    container.appendChild(wrapper);
    var toast = new bootstrap.Toast(wrapper, { delay: 4000 });
    toast.show();

    wrapper.addEventListener("hidden.bs.toast", function () {
      wrapper.remove();
    });
  };

  /* ---------------------------------------------------------
     Confirmation modal helper
     Usage: decoreConfirm("Delete this item?", function () { ... })
     --------------------------------------------------------- */
  window.decoreConfirm = function (message, onConfirm) {
    var modalEl = document.getElementById("decoreConfirmModal");
    if (!modalEl || typeof bootstrap === "undefined") {
      if (window.confirm(message)) onConfirm();
      return;
    }

    var bodyEl = modalEl.querySelector(".decore-confirm-message");
    var confirmBtn = modalEl.querySelector(".decore-confirm-btn");
    if (bodyEl) bodyEl.textContent = message;

    var modal = bootstrap.Modal.getOrCreateInstance(modalEl);

    var handler = function () {
      modal.hide();
      confirmBtn.removeEventListener("click", handler);
      if (typeof onConfirm === "function") onConfirm();
    };
    confirmBtn.addEventListener("click", handler);

    modal.show();
  };

  /* ---------------------------------------------------------
     PWA Offline Attendance Sync engine using IndexedDB
     --------------------------------------------------------- */
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function openSyncDB() {
    return new Promise(function (resolve, reject) {
      var request = indexedDB.open('decore_offline_db', 1);
      request.onupgradeneeded = function (event) {
        var db = event.target.result;
        if (!db.objectStoreNames.contains('attendance_sync')) {
          db.createObjectStore('attendance_sync', { keyPath: 'id', autoIncrement: true });
        }
      };
      request.onsuccess = function (event) {
        resolve(event.target.result);
      };
      request.onerror = function (event) {
        reject(event.target.error);
      };
    });
  }

  window.decoreSaveOfflineAttendance = function (date, records) {
    return openSyncDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var transaction = db.transaction('attendance_sync', 'readwrite');
        var store = transaction.objectStore('attendance_sync');
        var data = {
          date: date,
          records: records,
          timestamp: Date.now()
        };
        var request = store.add(data);
        request.onsuccess = function () {
          resolve();
        };
        request.onerror = function () {
          reject(request.error);
        };
      });
    });
  };

  function getPendingAttendance() {
    return openSyncDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var transaction = db.transaction('attendance_sync', 'readonly');
        var store = transaction.objectStore('attendance_sync');
        var request = store.getAll();
        request.onsuccess = function () {
          resolve(request.result);
        };
        request.onerror = function () {
          reject(request.error);
        };
      });
    });
  }

  function deletePendingAttendance(id) {
    return openSyncDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var transaction = db.transaction('attendance_sync', 'readwrite');
        var store = transaction.objectStore('attendance_sync');
        var request = store.delete(id);
        request.onsuccess = function () {
          resolve();
        };
        request.onerror = function () {
          reject(request.error);
        };
      });
    });
  }

  window.decoreSyncPendingAttendance = function () {
    if (!navigator.onLine) return;

    getPendingAttendance().then(function (pendingItems) {
      if (!pendingItems || pendingItems.length === 0) return;

      pendingItems.forEach(function (item) {
        var csrfToken = getCookie('csrftoken') || '';

        fetch('/attendance/sheet/', {
          method: "POST",
          body: JSON.stringify({
            date: item.date,
            records: item.records
          }),
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
            "X-Requested-With": "XMLHttpRequest"
          }
        })
        .then(function (res) {
          return res.json();
        })
        .then(function (data) {
          if (data.success) {
            deletePendingAttendance(item.id).then(function () {
              window.decoreToast("Offline attendance sheet for " + item.date + " synced successfully!", "success");
            });
          }
        })
        .catch(function (err) {
          console.error("Auto-sync failed for item", item.id, err);
        });
      });
    });
  };

  function updateOnlineStatus() {
    var badge = document.getElementById("decoreOfflineBadge");
    if (!badge) return;
    if (navigator.onLine) {
      badge.classList.add("d-none");
      badge.classList.remove("d-inline-flex");
    } else {
      badge.classList.remove("d-none");
      badge.classList.add("d-inline-flex");
    }
  }

  // Run auto-sync triggers
  document.addEventListener("DOMContentLoaded", function () {
    updateOnlineStatus();
    setTimeout(window.decoreSyncPendingAttendance, 2000);
  });
  window.addEventListener("online", function() {
    updateOnlineStatus();
    window.decoreSyncPendingAttendance();
  });
  window.addEventListener("offline", updateOnlineStatus);

  // iOS PWA Standalone Mode Navigation Hack
  // Prevents internal links from launching standard Safari browser wrapper
  if (("standalone" in window.navigator) && window.navigator.standalone) {
    document.addEventListener('click', function(event) {
      var noddy = event.target;
      while (noddy && noddy.nodeName !== "A" && noddy.nodeName !== "HTML") {
        noddy = noddy.parentNode;
      }
      if (noddy && 'href' in noddy && noddy.href.indexOf('http') !== -1 && (noddy.href.indexOf(document.location.host) !== -1)) {
        event.preventDefault();
        document.location.href = noddy.href;
      }
    }, false);
  }

  /* ---------------------------------------------------------
     Hover Prefetch — start fetching the next page as soon as
     the user hovers a nav link for 65ms. By click time, the
     browser already has the page in-cache → near-instant load.
     --------------------------------------------------------- */
  function initHoverPrefetch() {
    var prefetched = new Set();
    var hoverTimer = null;

    function prefetchUrl(url) {
      if (prefetched.has(url)) return;
      prefetched.add(url);
      var link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = url;
      link.as = 'document';
      document.head.appendChild(link);
    }

    document.addEventListener('mouseover', function(e) {
      var anchor = e.target.closest('a');
      if (!anchor || !anchor.href || anchor.target ||
          anchor.getAttribute('download') ||
          anchor.href.startsWith('javascript:') ||
          anchor.href.includes('#') ||
          !anchor.href.includes(location.hostname)) return;

      hoverTimer = setTimeout(function() {
        prefetchUrl(anchor.href);
      }, 65);
    }, { passive: true });

    document.addEventListener('mouseout', function() {
      clearTimeout(hoverTimer);
    }, { passive: true });

    // Touch: prefetch on touchstart (before touchend/click fires)
    document.addEventListener('touchstart', function(e) {
      var anchor = e.target.closest('a');
      if (!anchor || !anchor.href || anchor.target ||
          anchor.getAttribute('download') ||
          anchor.href.startsWith('javascript:') ||
          anchor.href.includes('#') ||
          !anchor.href.includes(location.hostname)) return;
      prefetchUrl(anchor.href);
    }, { passive: true });
  }

  /* ---------------------------------------------------------
     Worksite Progress Bar Animations
     --------------------------------------------------------- */
  function initProgressBarAnimations() {
    requestAnimationFrame(function() {
      var progressBars = document.querySelectorAll('.progress-bar[data-progress]');
      progressBars.forEach(function (bar) {
        bar.style.willChange = 'width';
        bar.style.width = '0%';
        requestAnimationFrame(function() {
          bar.style.width = (bar.getAttribute('data-progress') || 0) + '%';
        });
      });
    });
  }

  /* ---------------------------------------------------------
     Instant 0ms Link Navigation Feedback + View Transitions
     --------------------------------------------------------- */
  var _navBar = null;
  function getNavBar() { return _navBar || (_navBar = document.getElementById('topNavProgressBar')); }

  function showNavBar() {
    var bar = getNavBar();
    if (!bar) return;
    bar.style.transition = 'none';
    bar.style.opacity = '1';
    bar.style.width = '0%';
    requestAnimationFrame(function() {
      bar.style.transition = 'width 0.18s cubic-bezier(0.4,0,0.2,1), opacity 0.12s ease';
      bar.style.width = '55%';
      setTimeout(function() { bar.style.width = '88%'; }, 90);
    });
  }

  function finishNavBar() {
    var bar = getNavBar();
    if (!bar) return;
    bar.style.width = '100%';
    setTimeout(function() { bar.style.opacity = '0'; bar.style.width = '0'; }, 250);
  }

  document.addEventListener('click', function(e) {
    var anchor = e.target.closest('a');
    if (anchor && anchor.href && !anchor.target &&
        !anchor.getAttribute('download') &&
        !anchor.href.startsWith('javascript:') &&
        !anchor.href.includes('#') &&
        anchor.href.includes(location.hostname)) {
      showNavBar();
    }
  });

  // View Transitions API — smooth cross-page animation (Chrome 111+)
  if (document.startViewTransition) {
    document.addEventListener('click', function(e) {
      var anchor = e.target.closest('a');
      if (!anchor || !anchor.href || anchor.target ||
          anchor.getAttribute('download') ||
          anchor.href.startsWith('javascript:') ||
          anchor.href.includes('#') ||
          !anchor.href.includes(location.hostname)) return;

      // Never intercept clicks inside the sidebar nav — let sidebar handle its own state
      if (anchor.closest('.decore-sidebar-nav')) {
        // Just close the mobile sidebar and let the browser navigate normally
        var wrapper = document.querySelector('.decore-wrapper');
        if (wrapper) wrapper.classList.remove('sidebar-mobile-open');
        return; // let default navigation happen
      }

      // For all other internal links, use View Transition
      e.preventDefault();
      var dest = anchor.href;
      document.startViewTransition(function() {
        window.location.href = dest;
      });
    });
  } else {
    // Fallback for browsers without View Transitions: close mobile sidebar on nav
    document.addEventListener('click', function(e) {
      var anchor = e.target.closest('a');
      if (!anchor || !anchor.closest('.decore-sidebar-nav')) return;
      var wrapper = document.querySelector('.decore-wrapper');
      if (wrapper) wrapper.classList.remove('sidebar-mobile-open');
    });
  }


  // Finish progress bar on new page paint
  window.addEventListener('pageshow', function(e) {
    finishNavBar();
    if (e.persisted) {
      // bfcache restore — reset immediately
      var bar = getNavBar();
      if (bar) { bar.style.transition = 'none'; bar.style.opacity = '0'; bar.style.width = '0'; }
    }
  });

  // Reset progress bar on bfcache restore (browser back button)
  window.addEventListener('popstate', function() {
    finishNavBar();
  });
