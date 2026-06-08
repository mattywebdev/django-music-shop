// Wait for the page to load before executing the script
// Get all info messages
var info_messages = document.getElementsByClassName('cart-tooltip');

setTimeout(function(){
    for (var i = 0; i < info_messages.length; i ++) {
        // Set display attribute as !important, neccessary when using bootstrap
        info_messages[i].setAttribute('style', 'display:none !important');
    }
}, 3000);

document.addEventListener('DOMContentLoaded', function() {
  const cartToggle = document.getElementById('cart-toggle');
  const cartDropdown = document.getElementById('cart-dropdown');
  const cartTooltip = document.getElementById('nav-cart-total'); // Element with tooltip

  cartToggle.addEventListener('click', function() {
    const isDropdownVisible = cartDropdown.style.display === 'block';
    
    // Toggle dropdown display
    cartDropdown.style.display = isDropdownVisible ? 'none' : 'block';
    
    // Hide tooltip when dropdown is visible
    if (!isDropdownVisible) {
      cartTooltip.classList.add('tooltip-hidden');
    } else {
      cartTooltip.classList.remove('tooltip-hidden');
    }
  });

  // Optional: Hide dropdown if clicked outside
  document.addEventListener('click', function(event) {
    if (!cartToggle.contains(event.target) && !cartDropdown.contains(event.target)) {
      cartDropdown.style.display = 'none';
      cartTooltip.classList.remove('tooltip-hidden');
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
            waveSurfer.drawBuffer(); // Draw the buffer (waveform)
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

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('cart-update-form');
  if (!form) return;

  const statusBox = document.getElementById('cart-status');
  const summaryTotal = document.getElementById('cart-summary-total');
  const summaryGrandTotal = document.getElementById('cart-summary-grand-total');
  const summaryCount = document.getElementById('cart-summary-count');
  const navCartTotal = document.getElementById('nav-cart-total');
  const navCartBadge = document.querySelector('.nav-cart-circle');
  let submitTimer;
  let hideTimer;
  let isSubmitting = false;

  function money(value) {
    return Number(value || 0).toFixed(2);
  }

  function showStatus(text = 'Updating cart...') {
    if (!statusBox) return;
    const label = statusBox.querySelector('.cart-status-text');
    if (label) label.textContent = text;
    statusBox.hidden = false;
    statusBox.classList.add('show');

    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      statusBox.classList.remove('show');
      setTimeout(() => {
        statusBox.hidden = true;
      }, 250);
    }, 1400);
  }

  function recalculateCart() {
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

    if (summaryTotal) summaryTotal.textContent = money(totalPrice);
    if (summaryGrandTotal) summaryGrandTotal.textContent = money(totalPrice);
    if (summaryCount) summaryCount.textContent = totalItems;
    if (navCartTotal) navCartTotal.textContent = money(totalPrice);
    if (navCartBadge) {
      navCartBadge.textContent = totalItems;
      navCartBadge.dataset.count = String(totalItems);
    }
  }

  function queueSubmit() {
    clearTimeout(submitTimer);
    showStatus();
    submitTimer = setTimeout(() => {
      if (isSubmitting) return;
      isSubmitting = true;
      form.requestSubmit();
    }, 850);
  }

  form.querySelectorAll('.cart-qty-btn').forEach(button => {
    button.addEventListener('click', () => {
      const row = button.closest('.cart-line-item');
      const input = row ? row.querySelector('.cart-qty-input') : null;
      if (!input) return;

      const current = Math.max(1, parseInt(input.value, 10) || 1);
      input.value = button.dataset.action === 'increase'
        ? current + 1
        : Math.max(1, current - 1);

      recalculateCart();
      queueSubmit();
    });
  });

  form.querySelectorAll('.cart-qty-input').forEach(input => {
    input.addEventListener('input', () => {
      recalculateCart();
      queueSubmit();
    });
    input.addEventListener('change', () => {
      recalculateCart();
      queueSubmit();
    });
  });
});
