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

    // Create multiple bars for the placeholder effect
    for (let i = 0; i < 8; i++) {
        const bar = document.createElement('div');
        bar.className = 'bar';
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
            waveColor: 'violet',
            progressColor: 'purple',
            height: 80,
            barWidth: 2
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
        playButton.textContent = 'Play Preview';
    } else {
        waveSurfer.play();
        playButton.textContent = 'Pause Preview';

        // Update time display as audio plays
        waveSurfer.on('audioprocess', () => {
            const currentTime = waveSurfer.getCurrentTime();
            timeDisplay.textContent = formatTime(currentTime);
        });

        // Reset UI on finish
        waveSurfer.on('finish', () => {
            playButton.textContent = 'Play Preview';
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
  const form = document.getElementById('cart-update-form');   // make sure your <form> has this id
  const statusBox = document.getElementById('cart-status');
  if (!form || !statusBox) return;

  let submitTimer, hideTimer, isSubmitting = false;

  // tweak these two to taste
  const SHOW_MS = 1600;        // how long the toast stays visible
  const SUBMIT_DELAY_MS = 900; // delay before we actually submit

  function showStatus(text = 'Updating cart…') {
    const t = statusBox.querySelector('.cart-status-text');
    if (t) t.textContent = text;

    statusBox.hidden = false;
    statusBox.classList.add('show');

    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      statusBox.classList.remove('show');
      setTimeout(() => (statusBox.hidden = true), 5400);
    }, SHOW_MS);
  }

  function queueSubmit() {
    clearTimeout(submitTimer);
    showStatus(); // show immediately

    submitTimer = setTimeout(() => {
      if (isSubmitting) return;  // prevent double-submit
      isSubmitting = true;
      form.requestSubmit();      // page reload happens after this
    }, SUBMIT_DELAY_MS);
  }

  document.querySelectorAll('.btn-quantity, .quantity-input').forEach(el => {
    el.addEventListener('click', queueSubmit);
    el.addEventListener('change', queueSubmit);
  });
});