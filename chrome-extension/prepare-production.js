// Script to prepare extension for production build
import { readFileSync, writeFileSync, existsSync, copyFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const backendUrl = process.env.BACKEND_URL || process.argv[2];

if (!backendUrl) {
  console.error('Error: BACKEND_URL environment variable or URL argument is required');
  console.error('Usage: BACKEND_URL=https://your-backend.run.app node prepare-production.js');
  console.error('   or: node prepare-production.js https://your-backend.run.app');
  process.exit(1);
}

console.log(`Preparing extension for production with backend: ${backendUrl}`);

// 1. Update manifest.json host_permissions
const manifestPath = join(__dirname, 'manifest.json');
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));

// Remove localhost and add production URL
manifest.host_permissions = [
  `${backendUrl}/*`,
  'https://accounts.google.com/*',
  'https://www.googleapis.com/*'
];

writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf8');
console.log('✓ Updated manifest.json host_permissions');

// 2. Create .env.production file
const envProdPath = join(__dirname, '.env.production');
writeFileSync(envProdPath, `VITE_API_BASE=${backendUrl}\n`, 'utf8');
console.log('✓ Created .env.production file');

console.log('\n✅ Extension prepared for production!');
console.log('Next steps:');
console.log('1. Run: npm run build');
console.log('2. The dist folder will contain your production-ready extension');
console.log('3. Zip the dist folder contents for Chrome Web Store submission');

