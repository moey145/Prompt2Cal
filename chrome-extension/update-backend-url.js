// Script to update backend URL in constants.js for production
import { readFileSync, writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const backendUrl = process.env.BACKEND_URL || process.argv[2];

if (!backendUrl) {
  console.error('Error: BACKEND_URL environment variable or URL argument is required');
  console.error('Usage: BACKEND_URL=https://your-backend.run.app node update-backend-url.js');
  console.error('   or: node update-backend-url.js https://your-backend.run.app');
  process.exit(1);
}

const constantsPath = join(__dirname, 'src', 'utils', 'constants.js');
let constantsContent = readFileSync(constantsPath, 'utf8');

// Replace the API_BASE URL
constantsContent = constantsContent.replace(
  /export const API_BASE = ".*";/,
  `export const API_BASE = "${backendUrl}";`
);

writeFileSync(constantsPath, constantsContent, 'utf8');
console.log(`✓ Updated API_BASE to: ${backendUrl}`);

// Also update manifest.json host_permissions
const manifestPath = join(__dirname, 'manifest.json');
let manifestContent = JSON.parse(readFileSync(manifestPath, 'utf8'));

// Add backend URL to host_permissions if not already there
if (!manifestContent.host_permissions.includes(`${backendUrl}/*`)) {
  manifestContent.host_permissions.push(`${backendUrl}/*`);
  writeFileSync(manifestPath, JSON.stringify(manifestContent, null, 2), 'utf8');
  console.log(`✓ Updated manifest.json host_permissions`);
}

console.log('✅ Configuration updated!');

