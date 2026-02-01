/**
 * BPMN to PNG renderer using bpmn-js and Playwright
 * Optimized for clean rendering without UI elements
 */

const fs = require('fs');
const { chromium } = require('playwright');

async function renderBpmnToPng(bpmnXml, options = {}) {
  const {
    width = 2048,
    height = 2048,
    backgroundColor = '#ffffff',
    padding = 50,
    targetResolution = 2048  // Целевое разрешение для длинной стороны
  } = options;

  let browser;
  try {
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const context = await browser.newContext({
      viewport: { width, height }
    });

    const page = await context.newPage();

    const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      margin: 0;
      padding: 0;
      background-color: ${backgroundColor};
      overflow: hidden;
    }
    #canvas {
      width: ${width}px;
      height: ${height}px;
    }
    
    /* Hide all UI elements */
    .bjs-powered-by,
    .djs-palette,
    .djs-context-pad,
    .djs-popup,
    .djs-overlay-context-pad {
      display: none !important;
    }
    
    /* Ensure connections are behind shapes */
    .djs-connection {
      z-index: 1 !important;
    }
    
    .djs-shape {
      z-index: 10 !important;
    }
    
    /* Make sure text is always on top */
    .djs-label {
      z-index: 20 !important;
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
    const padding = ${padding};
    
    const viewer = new BpmnJS({
      container: '#canvas',
      width: ${width},
      height: ${height}
    });

    viewer.importXML(bpmnXML).then(() => {
      const canvas = viewer.get('canvas');
      const elementRegistry = viewer.get('elementRegistry');
      
      // Calculate diagram bounds
      const allElements = elementRegistry.getAll();
      
      if (allElements.length === 0) {
        window.renderError = 'No elements found in diagram';
        return;
      }
      
      let minX = Infinity, minY = Infinity;
      let maxX = -Infinity, maxY = -Infinity;
      
      allElements.forEach(element => {
        if (element.x !== undefined && element.y !== undefined) {
          minX = Math.min(minX, element.x);
          minY = Math.min(minY, element.y);
          maxX = Math.max(maxX, element.x + (element.width || 0));
          maxY = Math.max(maxY, element.y + (element.height || 0));
        }
      });
      
      const diagramWidth = maxX - minX;
      const diagramHeight = maxY - minY;
      
      const availableWidth = ${width} - (2 * padding);
      const availableHeight = ${height} - (2 * padding);
      
      const scaleX = availableWidth / diagramWidth;
      const scaleY = availableHeight / diagramHeight;
      // Убрано ограничение Math.min(..., 1) для масштабирования вверх
      const scale = Math.min(scaleX, scaleY);
      
      const centerX = minX + diagramWidth / 2;
      const centerY = minY + diagramHeight / 2;
      
      const viewportCenterX = ${width} / 2;
      const viewportCenterY = ${height} / 2;
      
      canvas.zoom(scale);
      canvas.viewbox({
        x: centerX - (viewportCenterX / scale),
        y: centerY - (viewportCenterY / scale),
        width: ${width} / scale,
        height: ${height} / scale
      });
      
      window.renderComplete = true;
    }).catch(err => {
      console.error('Error rendering BPMN:', err);
      window.renderError = err.message;
    });
  </script>
</body>
</html>
    `;

    await page.setContent(html, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => window.renderComplete || window.renderError, {
      timeout: 30000
    });

    const renderError = await page.evaluate(() => window.renderError);
    if (renderError) {
      throw new Error(`BPMN rendering failed: ${renderError}`);
    }

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

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length < 2) {
    console.error('Usage: node bpmn_to_png.js <input.bpmn> <output.png> [options]');
    process.exit(1);
  }

  const inputPath = args[0];
  const outputPath = args[1];
  const options = args[2] ? JSON.parse(args[2]) : {};

  try {
    if (!fs.existsSync(inputPath)) {
      throw new Error(`Input file not found: ${inputPath}`);
    }

    const bpmnXml = fs.readFileSync(inputPath, 'utf-8');
    console.log(`Rendering BPMN to PNG: ${inputPath} -> ${outputPath}`);
    
    const pngBuffer = await renderBpmnToPng(bpmnXml, options);
    fs.writeFileSync(outputPath, pngBuffer);
    
    console.log(`Successfully rendered: ${outputPath}`);
    process.exit(0);
  } catch (err) {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { renderBpmnToPng };