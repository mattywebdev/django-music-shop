// Wait for the page to load before executing the script
// Get all info messages
var info_messages = document.getElementsByClassName('cart-tooltip');

setTimeout(function(){
    for (var i = 0; i < info_messages.length; i ++) {
        // Set display attribute as !important, neccessary when using bootstrap
        info_messages[i].setAttribute('style', 'display:none !important');
    }
}, 3000);

document.addEventListener('click', function(event) {
  const cartToggle = event.target.closest('#cart-toggle');
  const cartDropdown = document.getElementById('cart-dropdown');
  const cartTooltip = document.getElementById('nav-cart-total');

  if (cartToggle && cartDropdown) {
    event.preventDefault();
    const isDropdownVisible = cartDropdown.style.display === 'block';
    cartDropdown.style.display = isDropdownVisible ? 'none' : 'block';
    cartToggle.classList.toggle('is-open', !isDropdownVisible);
    cartToggle.setAttribute('aria-expanded', String(!isDropdownVisible));
    if (cartTooltip) cartTooltip.classList.toggle('tooltip-hidden', !isDropdownVisible);
    return;
  }

  const liveToggle = document.getElementById('cart-toggle');
  if (
    cartDropdown &&
    liveToggle &&
    !liveToggle.contains(event.target) &&
    !cartDropdown.contains(event.target)
  ) {
    cartDropdown.style.display = 'none';
    liveToggle.classList.remove('is-open');
    liveToggle.setAttribute('aria-expanded', 'false');
    if (cartTooltip) cartTooltip.classList.remove('tooltip-hidden');
  }
});

document.addEventListener('DOMContentLoaded', function() {
  const mobileNav = document.getElementById('navbarNav');
  const backdrop = document.querySelector('[data-mobile-drawer-close]');
  const toggler = document.querySelector('[data-mobile-nav-toggle]');
  if (!mobileNav || !backdrop || !toggler) return;
  const drawerPlaceholder = document.createComment('mobile nav drawer home');
  const originalParent = mobileNav.parentNode;
  const originalNextSibling = mobileNav.nextSibling;
  let restoreTimer;

  function isMobileNav() {
    return window.matchMedia('(max-width: 991px)').matches;
  }

  function dockDrawerToBody() {
    if (mobileNav.parentNode === document.body) return;
    if (!drawerPlaceholder.parentNode) {
      originalParent.insertBefore(drawerPlaceholder, originalNextSibling);
    }
    document.body.appendChild(mobileNav);
  }

  function restoreDrawerHome() {
    if (mobileNav.parentNode !== document.body) return;
    originalParent.insertBefore(mobileNav, drawerPlaceholder);
    if (drawerPlaceholder.parentNode) {
      drawerPlaceholder.parentNode.removeChild(drawerPlaceholder);
    }
  }

  function clearMobileNavStyles() {
    [
      'position', 'top', 'right', 'z-index', 'display', 'visibility',
      'pointer-events', 'transform', 'height'
    ].forEach(function(prop) {
      mobileNav.style.removeProperty(prop);
    });
    [
      'position', 'inset', 'z-index', 'display', 'visibility',
      'pointer-events', 'opacity'
    ].forEach(function(prop) {
      backdrop.style.removeProperty(prop);
    });
  }

  function setMobileNav(open) {
    clearTimeout(restoreTimer);
    mobileNav.classList.remove('collapsing');
    mobileNav.classList.add('collapse');
    document.body.classList.toggle('mobile-nav-open', open);
    backdrop.classList.toggle('is-active', open);
    toggler.setAttribute('aria-expanded', String(open));

    if (!isMobileNav()) {
      mobileNav.classList.remove('show');
      backdrop.classList.remove('is-active');
      clearMobileNavStyles();
      restoreDrawerHome();
      return;
    }

    if (open) {
      dockDrawerToBody();
      mobileNav.classList.add('show');
      mobileNav.style.setProperty('position', 'fixed', 'important');
      mobileNav.style.setProperty('top', '0', 'important');
      mobileNav.style.setProperty('right', '0', 'important');
      mobileNav.style.setProperty('z-index', '1100', 'important');
      mobileNav.style.setProperty('display', 'block', 'important');
      mobileNav.style.setProperty('height', '100dvh', 'important');
      mobileNav.style.setProperty('visibility', 'visible', 'important');
      mobileNav.style.setProperty('pointer-events', 'auto', 'important');
      mobileNav.style.setProperty('transform', 'translateX(106%)', 'important');
      backdrop.style.setProperty('position', 'fixed', 'important');
      backdrop.style.setProperty('inset', '0', 'important');
      backdrop.style.setProperty('z-index', '1090', 'important');
      backdrop.style.setProperty('display', 'block', 'important');
      backdrop.style.setProperty('visibility', 'visible', 'important');
      backdrop.style.setProperty('pointer-events', 'auto', 'important');
      backdrop.style.setProperty('opacity', '1', 'important');
      requestAnimationFrame(function() {
        mobileNav.style.setProperty('transform', 'translateX(0)', 'important');
      });
      return;
    }

    mobileNav.classList.remove('show');
    backdrop.classList.remove('is-active');
    mobileNav.style.setProperty('pointer-events', 'none', 'important');
    mobileNav.style.setProperty('transform', 'translateX(106%)', 'important');
    backdrop.style.setProperty('pointer-events', 'none', 'important');
    backdrop.style.setProperty('opacity', '0', 'important');

    restoreTimer = window.setTimeout(function() {
      if (mobileNav.classList.contains('show')) return;
      mobileNav.style.setProperty('visibility', 'hidden', 'important');
      backdrop.style.setProperty('visibility', 'hidden', 'important');
      clearMobileNavStyles();
      restoreDrawerHome();
    }, 360);
  }

  toggler.addEventListener('click', function(event) {
    if (!isMobileNav()) return;
    event.preventDefault();
    event.stopPropagation();
    setMobileNav(!mobileNav.classList.contains('show'));
  });

  backdrop.addEventListener('click', function() {
    setMobileNav(false);
  });

  document.addEventListener('click', function(event) {
    if (!isMobileNav() || !mobileNav.classList.contains('show')) return;
    if (mobileNav.contains(event.target) || (toggler && toggler.contains(event.target))) return;
    setMobileNav(false);
  });

  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && isMobileNav()) {
      setMobileNav(false);
    }
  });

  mobileNav.querySelectorAll('a').forEach(function(link) {
    link.addEventListener('click', function() {
      if (isMobileNav()) {
        setMobileNav(false);
      }
    });
  });

  window.addEventListener('resize', function() {
    if (!isMobileNav()) {
      setMobileNav(false);
    }
  });
});


// scripts.js

// scripts.js

const waveSurfers = {};

// Function to format time for display
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
}


// Function to create a placeholder waveform
function createPlaceholderWaveform(containerId) {
    const container = document.getElementById(containerId);
    const placeholder = document.createElement('div');
    placeholder.className = 'placeholder-wave';

    // Create enough bars to read like a real loading waveform.
    for (let i = 0; i < 24; i++) {
        const bar = document.createElement('div');
        bar.className = 'bar';
        bar.style.height = `${24 + ((i * 17) % 58)}%`;
        placeholder.appendChild(bar);
    }

    container.appendChild(placeholder);
    return placeholder;
}

// Function to initialize WaveSurfer instances
function initializeWaveSurfers(trackData) {
    trackData.forEach(track => {
        // Create a placeholder waveform
        const placeholder = createPlaceholderWaveform(`waveform-${track.id}`);

        const waveSurfer = WaveSurfer.create({
            container: `#waveform-${track.id}`,
            waveColor: 'rgba(124, 200, 255, .55)',
            progressColor: '#9ee493',
            cursorColor: 'rgba(255,255,255,.75)',
            height: 58,
            barWidth: 2,
            barGap: 2,
            barRadius: 2
        });
        
        waveSurfer.load(track.previewClipUrl);

        // Hide the placeholder and show the waveform once loaded
        waveSurfer.on('ready', () => {
            placeholder.style.display = 'none'; // Hide the placeholder
        });

        waveSurfers[track.id] = waveSurfer;
    });
}

// Function to toggle play/pause
function togglePlay(trackId) {
    const playButton = document.getElementById('play-button-' + trackId);
    const timeDisplay = document.getElementById('time-display-' + trackId);
    const waveSurfer = waveSurfers[trackId];

    if (!waveSurfer) {
        console.error(`WaveSurfer instance not found for track ID: ${trackId}`);
        return;
    }

    if (waveSurfer.isPlaying()) {
        waveSurfer.pause();
        playButton.innerHTML = '<i class="fa-solid fa-play" aria-hidden="true"></i><span>Play</span>';
    } else {
        waveSurfer.play();
        playButton.innerHTML = '<i class="fa-solid fa-pause" aria-hidden="true"></i><span>Pause</span>';

        // Update time display as audio plays
        waveSurfer.on('audioprocess', () => {
            const currentTime = waveSurfer.getCurrentTime();
            timeDisplay.textContent = formatTime(currentTime);
        });

        // Reset UI on finish
        waveSurfer.on('finish', () => {
            playButton.innerHTML = '<i class="fa-solid fa-play" aria-hidden="true"></i><span>Play</span>';
            timeDisplay.textContent = '0:00';
            waveSurfer.seekTo(0);
        });
    }
}

// This will be called on DOMContentLoaded to set everything up
document.addEventListener('DOMContentLoaded', () => {
    const trackDataEl = document.getElementById('track-data');
    if (!trackDataEl) return;

    const trackData = JSON.parse(trackDataEl.textContent);
    initializeWaveSurfers(trackData);
});


// --- Tiny navbar typeahead ---
(function(){
  const form = document.getElementById('nav-search-form');
  const input = document.getElementById('nav-search');
  const menu  = document.getElementById('nav-suggest');
  if (!form || !input || !menu) return;

  const suggestURL = form.dataset.suggestUrl;
  const albumsURL  = form.dataset.albumsUrl;
  const tracksURL  = form.dataset.tracksUrl;
  let t = 0;

  function hide(){ menu.style.display='none'; menu.innerHTML=''; }
  function show(){ menu.style.display='block'; }

  input.addEventListener('input', () => {
    const q = input.value.trim();
    clearTimeout(t);
    if (!q) return hide();
    t = setTimeout(async () => {
      try {
        const r = await fetch(`${suggestURL}?q=${encodeURIComponent(q)}`);
        if (!r.ok) return hide();
        const data = await r.json();
        menu.innerHTML = '';
        const add = (href, left, right) => {
          const a = document.createElement('a');
          a.className = 'dropdown-item d-flex justify-content-between';
          a.href = href;
          a.textContent = left;
          if (right) { const s=document.createElement('small'); s.className='text-muted'; s.textContent=right; a.appendChild(s); }
          menu.appendChild(a);
        };
        (data.artists||[]).slice(0,5).forEach(a  => add(`${albumsURL}?q=${encodeURIComponent(a.name)}`, a.name, 'Artist'));
        (data.albums||[] ).slice(0,5).forEach(a => add(`${albumsURL}?q=${encodeURIComponent(a.title)}`, a.title, a.artist));
        (data.tracks || []).slice(0, 5).forEach(tk => add(`${tracksURL}?q=${encodeURIComponent(tk.title)}`, tk.title, tk.artist));
        // 🧢 Merchandise results
        (data.merch||[] ).slice(0,5).forEach(m =>add(`/merchandise/?q=${encodeURIComponent(m.title)}`, m.title, m.type));
        menu.children.length ? show() : hide();
      } catch (_) { hide(); }
    }, 150);
  });

  document.addEventListener('click', (e) => {
    if (!menu.contains(e.target) && e.target !== input) hide();
  });
})();

(function(){
  let cartSubmitTimer;
  let cartStatusTimer;

  function money(value) {
    return Number(value || 0).toFixed(2);
  }

  function getCookie(name) {
    return document.cookie
      .split('; ')
      .find(row => row.startsWith(`${name}=`))
      ?.split('=')[1] || '';
  }

  function showCartStatus(text = 'Updating cart...') {
    const statusBox = document.getElementById('cart-status');
    if (!statusBox) return;
    const label = statusBox.querySelector('.cart-status-text');
    if (label) label.textContent = text;
    statusBox.hidden = false;
    statusBox.classList.add('show');

    clearTimeout(cartStatusTimer);
    cartStatusTimer = setTimeout(() => {
      statusBox.classList.remove('show');
      setTimeout(() => {
        statusBox.hidden = true;
      }, 250);
    }, 1400);
  }

  function showNavToast(text) {
    const toastArea = document.getElementById('nav-toast-area');
    if (!toastArea || !text) return;
    toastArea.textContent = text;
    toastArea.classList.add('is-visible');
    clearTimeout(toastArea._hideTimer);
    toastArea._hideTimer = setTimeout(() => {
      toastArea.classList.remove('is-visible');
    }, 1600);
  }

  function updateCartChrome(data) {
    if (!data) return;

    const total = data.cart_total_price ?? data.total_price;
    const count = data.cart_count ?? data.total_quantity;
    const navCartTotals = document.querySelectorAll('#nav-cart-total, .nav-cart-total-display');
    const navCartBadges = document.querySelectorAll('.nav-cart-circle');
    const cdTotal = document.getElementById('cd-total');

    if (total !== undefined) {
      navCartTotals.forEach(el => {
        el.textContent = money(total);
      });
    }
    if (cdTotal && total !== undefined) cdTotal.textContent = money(total);
    if (count !== undefined) {
      navCartBadges.forEach(badge => {
        badge.textContent = count;
        badge.dataset.count = String(count);
      });
    }

    if (data.cart_dropdown_html) {
      const oldDropdown = document.getElementById('cart-dropdown');
      if (oldDropdown) {
        const wasOpen = oldDropdown.style.display === 'block';
        oldDropdown.outerHTML = data.cart_dropdown_html;
        const newDropdown = document.getElementById('cart-dropdown');
        if (newDropdown && wasOpen) newDropdown.style.display = 'block';
      }
    }
  }

  function updateCartPageFromPayload(data) {
    if (!data) return;

    const summaryTotal = document.getElementById('cart-summary-total');
    const summaryGrandTotal = document.getElementById('cart-summary-grand-total');
    const summaryCount = document.getElementById('cart-summary-count');
    const countPill = document.querySelector('.cart-count-pill strong');
    const countLabel = document.querySelector('.cart-count-pill span');
    const total = data.cart_total_price ?? data.total_price;
    const count = Number(data.total_quantity ?? data.cart_count ?? 0);

    if (summaryTotal && total !== undefined) summaryTotal.textContent = money(total);
    if (summaryGrandTotal && total !== undefined) summaryGrandTotal.textContent = money(total);
    if (summaryCount) summaryCount.textContent = count;
    if (countPill) countPill.textContent = count;
    if (countLabel) countLabel.textContent = count === 1 ? 'item' : 'items';

    Object.entries(data.items || {}).forEach(([key, item]) => {
      const input = document.querySelector(`[name="quantity_${key}"]`);
      const row = input ? input.closest('.cart-line-item') : null;
      const price = row ? row.querySelector('.price') : null;
      if (input) input.value = item.quantity;
      if (price) price.textContent = money(item.total_price);
    });
  }

  function recalculateCartPage() {
    const form = document.getElementById('cart-update-form');
    if (!form) return;

    let totalItems = 0;
    let totalPrice = 0;

    form.querySelectorAll('.cart-line-item').forEach(row => {
      const input = row.querySelector('.cart-qty-input');
      const linePrice = row.querySelector('.price');
      if (!input || !linePrice) return;

      const quantity = Math.max(1, parseInt(input.value, 10) || 1);
      const unitPrice = parseFloat(input.dataset.price || '0');
      input.value = quantity;
      totalItems += quantity;
      totalPrice += quantity * unitPrice;
      linePrice.textContent = money(quantity * unitPrice);
    });

    updateCartChrome({ cart_count: totalItems, cart_total_price: money(totalPrice) });
    updateCartPageFromPayload({ total_quantity: totalItems, total_price: money(totalPrice) });
  }

  async function fetchJson(url, options = {}) {
    const headers = {
      'Accept': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      ...(options.headers || {})
    };
    const response = await fetch(url, { ...options, headers });
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      window.location.href = response.url || url;
      return null;
    }
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.message || 'Request failed');
    return data;
  }

  function queueCartSubmit() {
    const form = document.getElementById('cart-update-form');
    if (!form) return;

    clearTimeout(cartSubmitTimer);
    showCartStatus();
    cartSubmitTimer = setTimeout(async () => {
      try {
        const data = await fetchJson(form.action, {
          method: 'POST',
          body: new FormData(form),
          headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        updateCartChrome(data);
        updateCartPageFromPayload(data);
        showCartStatus(data?.message || 'Cart updated.');
      } catch (error) {
        showCartStatus('Could not update cart.');
      }
    }, 500);
  }

  document.addEventListener('click', async (event) => {
    const addLink = event.target.closest('a[href*="/add_to_cart/"]');
    if (addLink) {
      event.preventDefault();
      addLink.classList.add('is-loading');
      try {
        const data = await fetchJson(addLink.href);
        updateCartChrome(data);
        updateCartPageFromPayload(data);
        showNavToast(data?.message || 'Added to cart.');
      } catch (error) {
        showNavToast('Could not add item.');
      } finally {
        addLink.classList.remove('is-loading');
      }
      return;
    }

    const removeLink = event.target.closest('a[href*="/remove_from_cart/"]');
    if (removeLink) {
      event.preventDefault();
      try {
        const data = await fetchJson(removeLink.href);
        const row = removeLink.closest('.cart-line-item');
        if (row) row.remove();
        updateCartChrome(data);
        updateCartPageFromPayload(data);
        showCartStatus(data?.message || 'Removed from cart.');
        showNavToast(data?.message || 'Removed from cart.');
        if ((data?.cart_count || 0) === 0 && document.querySelector('.cart-page')) {
          window.location.reload();
        }
      } catch (error) {
        showCartStatus('Could not remove item.');
      }
      return;
    }

    const qtyButton = event.target.closest('.cart-qty-btn');
    if (qtyButton) {
      const row = qtyButton.closest('.cart-line-item');
      const input = row ? row.querySelector('.cart-qty-input') : null;
      if (!input) return;

      const current = Math.max(1, parseInt(input.value, 10) || 1);
      input.value = qtyButton.dataset.action === 'increase'
        ? current + 1
        : Math.max(1, current - 1);

      recalculateCartPage();
      queueCartSubmit();
    }
  });

  document.addEventListener('input', (event) => {
    if (!event.target.matches('.cart-qty-input')) return;
    recalculateCartPage();
    queueCartSubmit();
  });

  document.addEventListener('change', (event) => {
    if (!event.target.matches('.cart-qty-input')) return;
    recalculateCartPage();
    queueCartSubmit();
  });

  document.addEventListener('submit', async (event) => {
    const favForm = event.target.closest('form[action*="/favorite/toggle/"]');
    if (!favForm) return;

    event.preventDefault();
    const button = favForm.querySelector('button');
    if (button) button.disabled = true;

    try {
      const data = await fetchJson(favForm.action, {
        method: 'POST',
        body: new FormData(favForm),
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
      });

      if (button) {
        const icon = button.querySelector('i');
        button.classList.toggle('is-favorite', !!data.is_favorite);
        button.title = data.is_favorite ? 'Remove from favourites' : 'Add to favourites';
        if (icon) {
          icon.classList.toggle('fa-solid', !!data.is_favorite);
          icon.classList.toggle('fa-regular', !data.is_favorite);
        }
      }

      const favBadge = document.querySelector('.nav-badge');
      if (favBadge && data.favorites_count !== undefined) {
        favBadge.textContent = data.favorites_count;
        favBadge.hidden = Number(data.favorites_count) === 0;
      }
      showNavToast(data?.message || 'Favourites updated.');
    } catch (error) {
      showNavToast('Could not update favourites.');
    } finally {
      if (button) button.disabled = false;
    }
  });
})();
