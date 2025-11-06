import { copyFileSync, mkdirSync, existsSync, readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Create dist directory if it doesn't exist
if (!existsSync('dist')) {
  mkdirSync('dist');
}

// Copy static files to dist
const filesToCopy = [
  'background.js',
  'content.js',
  'content.css',
  'backend-config.js'
];

filesToCopy.forEach(file => {
  try {
    copyFileSync(join(__dirname, file), join(__dirname, 'dist', file));
    console.log(`✓ Copied ${file}`);
  } catch (err) {
    console.error(`✗ Error copying ${file}:`, err.message);
  }
});

// Copy manifest.json
try {
  copyFileSync(
    join(__dirname, 'manifest.json'),
    join(__dirname, 'dist', 'manifest.json')
  );
  console.log(`✓ Copied manifest.json`);
} catch (err) {
  console.error(`✗ Error copying manifest:`, err.message);
}

// Ensure dist/icons exists and copy available SVG assets only
if (!existsSync('dist/icons')) {
  mkdirSync('dist/icons');
}

const svgIconFiles = ['Logo.svg', 'DarkModeLogo.svg'];
svgIconFiles.forEach(file => {
  try {
    copyFileSync(
      join(__dirname, 'icons', file),
      join(__dirname, 'dist', 'icons', file)
    );
    console.log(`✓ Copied icons/${file}`);
  } catch (err) {
    console.warn(`⚠ Skipping icons/${file}:`, err.message);
  }
});

console.log('\n✅ Build complete! Load the "dist" folder in Chrome.');

