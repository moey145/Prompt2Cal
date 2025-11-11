// Quick script to update extension config with backend URL
// Usage: node update-extension-config.js https://your-backend.run.app

const fs = require('fs');
const path = require('path');

const backendUrl = process.argv[2];

if (!backendUrl) {
  console.error('Usage: node update-extension-config.js <backend-url>');
  console.error('Example: node update-extension-config.js https://prompt2cal-backend-xxxxx.run.app');
  process.exit(1);
}

// Update backend-config.js
const configPath = path.join(__dirname, 'chrome-extension/backend-config.js');
let config = fs.readFileSync(configPath, 'utf8');
config = config.replace(
  /API_BASE:\s*"[^"]*"/,
  `API_BASE: "${backendUrl}"`
);
fs.writeFileSync(configPath, config);
console.log(`✓ Updated backend-config.js with: ${backendUrl}`);

// Update manifest.json
const manifestPath = path.join(__dirname, 'chrome-extension/manifest.json');
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
manifest.host_permissions = [
  `${backendUrl}/*`,
  'https://accounts.google.com/*',
  'https://www.googleapis.com/*'
];
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
console.log(`✓ Updated manifest.json with: ${backendUrl}/*`);

console.log('\n✅ Configuration updated! Now run: cd chrome-extension && npm run build');

