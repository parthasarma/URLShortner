async function shortenUrl() {
  const input = document.getElementById('long-url');
  const resultEl = document.getElementById('shorten-result');
  const errorEl = document.getElementById('shorten-error');
  const url = input.value.trim();

  resultEl.classList.add('hidden');
  errorEl.classList.add('hidden');
  resultEl.innerHTML = '';
  errorEl.textContent = '';

  if (!url) {
    errorEl.textContent = 'Please enter a URL';
    errorEl.classList.remove('hidden');
    return;
  }

  try {
    const res = await fetch('/api/shorten', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to shorten');
    }
    const a = document.createElement('a');
    a.href = data.short_url;
    a.textContent = data.short_url;
    a.target = '_blank';
    a.rel = 'noopener';
    resultEl.appendChild(a);
    resultEl.classList.remove('hidden');
  } catch (e) {
    errorEl.textContent = e.message || 'Error shortening URL';
    errorEl.classList.remove('hidden');
  }
}

async function lookupUrl() {
  const input = document.getElementById('short-input');
  const resultEl = document.getElementById('lookup-result');
  const errorEl = document.getElementById('lookup-error');
  const val = input.value.trim();

  resultEl.classList.add('hidden');
  errorEl.classList.add('hidden');
  resultEl.innerHTML = '';
  errorEl.textContent = '';

  if (!val) {
    errorEl.textContent = 'Please enter a short URL or code';
    errorEl.classList.remove('hidden');
    return;
  }

  try {
    const res = await fetch('/api/lookup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ short: val })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Not found');
    }
    const a = document.createElement('a');
    a.href = data.long_url;
    a.textContent = data.long_url;
    a.target = '_blank';
    a.rel = 'noopener';
    resultEl.appendChild(a);
    resultEl.classList.remove('hidden');
  } catch (e) {
    errorEl.textContent = e.message || 'Short URL not found';
    errorEl.classList.remove('hidden');
  }
}

function setup() {
  document.getElementById('shorten-btn').addEventListener('click', shortenUrl);
  document.getElementById('lookup-btn').addEventListener('click', lookupUrl);

  const longInput = document.getElementById('long-url');
  longInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') shortenUrl();
  });

  const shortInput = document.getElementById('short-input');
  shortInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') lookupUrl();
  });

  // focus first input
  longInput.focus();
}

document.addEventListener('DOMContentLoaded', setup);
