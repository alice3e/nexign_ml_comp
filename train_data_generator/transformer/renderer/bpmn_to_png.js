/**
 * BPMN to PNG renderer using bpmn-js and Playwright
 * Converts BPMN XML to high-quality PNG images
 * 
 * Playwright is used instead of Puppeteer for better Apple Silicon (M1/M2/M3) compatibility
 */

const fs = require('fs');
const { chromium } = require('playwright');

/**
 * Render BPMN XML to PNG using Playwright
 * @param {string} bpmnXml - BPMN XML content
 * @param {object} options - Rendering options
 * @returns {Promise<Buffer>} PNG image buffer
 */
async function renderBpmnToPng(bpmnXml, options = {}) {
  const {
    width = 2048,
    height = 2048,
    backgroundColor = '#ffffff',
    padding = 20
  } = options;

  let browser;
  try {
    // Launch browser
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const context = await browser.newContext({
      viewport: { width, height }
    });

    const page = await context.newPage();

    // Create HTML with bpmn-js viewer
    const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      margin: 0;
      padding: ${padding}px;
      background-color: ${backgroundColor};
      overflow: hidden;
    }
    #canvas {
      width: ${width - 2 * padding}px;
      height: ${height - 2 * padding}px;
    }
    .bjs-powered-by {
      display: none !important;
    }
  </style>
  <link rel="stylesheet" href="https://unpkg.com/bpmn-js@17.0.0/dist/assets/diagram-js.css">
  <link rel="stylesheet" href="https://unpkg.com/bpmn-js@17.0.0/dist/assets/bpmn-font/css/bpmn.css">
</head>
<body>
  <div id="canvas"></div>
  <script src="https://unpkg.com/bpmn-js@17.0.0/dist/bpmn-viewer.development.js"></script>
  <script>
    const bpmnXML = ${JSON.stringify(bpmnXml)};
    
    const viewer = new BpmnJS({
      container: '#canvas'
    });

    viewer.importXML(bpmnXML).then(() => {
      const canvas = viewer.get('canvas');
      
      // Zoom to fit with padding
      canvas.zoom('fit-viewport', 'auto');
      
      // Get current zoom level and reduce it slightly to add padding
      const currentZoom = canvas.zoom();
      canvas.zoom(currentZoom * 0.95, 'auto');
      
      // Signal that rendering is complete
      window.renderComplete = true;
    }).catch(err => {
      console.error('Error rendering BPMN:', err);
      window.renderError = err.message;
    });
  </script>
</body>
</html>
    `;

    // Set content and wait for rendering
    await page.setContent(html, { waitUntil: 'networkidle' });

    // Wait for rendering to complete
    await page.waitForFunction(() => window.renderComplete || window.renderError, {
      timeout: 30000
    });

    // Check for errors
    const renderError = await page.evaluate(() => window.renderError);
    if (renderError) {
      throw new Error(`BPMN rendering failed: ${renderError}`);
    }

    // Take screenshot
    const screenshot = await page.screenshot({
      type: 'png',
      fullPage: false
    });

    await context.close();
    return screenshot;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

/**
 * Main CLI function
 */
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length < 2) {
    console.error('Usage: node bpmn_to_png.js <input.bpmn> <output.png> [options]');
    console.error('Options (JSON): {"width": 2048, "height": 2048, "backgroundColor": "#ffffff", "padding": 20}');
    process.exit(1);
  }

  const inputPath = args[0];
  const outputPath = args[1];
  const options = args[2] ? JSON.parse(args[2]) : {};

  try {
    // Read BPMN XML
    if (!fs.existsSync(inputPath)) {
      throw new Error(`Input file not found: ${inputPath}`);
    }

    const bpmnXml = fs.readFileSync(inputPath, 'utf-8');

    // Render to PNG
    console.log(`Rendering BPMN to PNG: ${inputPath} -> ${outputPath}`);
    const pngBuffer = await renderBpmnToPng(bpmnXml, options);

    // Write PNG file
    fs.writeFileSync(outputPath, pngBuffer);
    console.log(`Successfully rendered: ${outputPath}`);
    
    process.exit(0);
  } catch (err) {
    console.error(`Error: ${err.message}`);
    console.error(err.stack);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { renderBpmnToPng };