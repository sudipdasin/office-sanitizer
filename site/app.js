'use strict';
const command = document.getElementById('install-cmd');
const copy = document.getElementById('copy');
if (command && copy) copy.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(command.textContent);
    copy.textContent = 'Copied';
  } catch {
    copy.textContent = 'Select text to copy';
  }
});
fetch('/release.json', {cache: 'no-store'})
  .then(response => {
    if (!response.ok) throw new Error('No release');
    return response.json();
  })
  .then(release => {
    if (release.debian && /^[a-fA-F0-9]{64}$/.test(release.debian.sha256)) {
      document.getElementById('deb-sha').textContent = release.debian.sha256;
      document.getElementById('size').textContent =
        'Package size: ' + Math.ceil(release.debian.size / 1024) + ' KB';
    }
  })
  .catch(() => {
    document.getElementById('deb-sha').textContent = 'See SHA256SUMS for the exact package digest.';
  });
