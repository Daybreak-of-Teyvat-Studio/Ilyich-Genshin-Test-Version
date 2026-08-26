// Fix all custom DDS icons to proper 2-frame format
// Left frame: custom icon (scaled from full canvas to half width)
// Right frame: DOT_Infantryer right icon (scaled to fit)
// Saves as PNG first, then use texconv to convert to DDS
#target photoshop
app.preferences.rulerUnits = Units.PIXELS;

var baseDir = "C:/Users/LR/Documents/GitHub/Ilyich-Genshin-Test-Version/Daybreak of Teyvat Beta Version/gfx/";
var logFile = new File(baseDir + "_fix_log.txt");
logFile.open("w");
function log(msg) { logFile.writeln(msg); $.writeln(msg); }

log("=== Fix All Icons (PNG version) ===");

// Step 1: Extract right half of DOT_Infantryer_small
log("Step 1: Extract DOT_Infantryer right frame");
var dotPath = baseDir + "texticons/unit_DOT_Infantryer_small.dds";
var dotDoc = app.open(new File(dotPath));
var dotW = dotDoc.width.value;
var dotH = dotDoc.height.value;
var halfDotW = dotW / 2;
log("  DOT_Infantryer: " + dotW + "x" + dotH);

// Crop to right half
dotDoc.crop([halfDotW, 0, dotW, dotH]);
dotDoc.flatten();
log("  Cropped to right half: " + dotDoc.width.value + "x" + dotDoc.height.value);

// Save as temp PNG
var tempRightPath = baseDir + "_temp_right.png";
var tempRightFile = new File(tempRightPath);
var pngOpts = new ExportOptionsSaveForWeb();
pngOpts.format = SaveDocumentType.PNG;
pngOpts.PNG8 = false;
dotDoc.exportDocument(tempRightFile, ExportType.SAVEFORWEB, pngOpts);
dotDoc.close(SaveOptions.DONOTSAVECHANGES);
log("  Temp saved: " + tempRightPath);

// Step 2: Process each target DDS
var targets = [
    // divisions_large
    "interface/counters/divisions_large/unit_SNE_electrohammer_icon.dds",
    "interface/counters/divisions_large/unit_SNE_anemoboxer_icon.dds",
    "interface/counters/divisions_large/unit_SNE_hydrogunner_icon.dds",
    "interface/counters/divisions_large/unit_SNE_cryogunner_icon.dds",
    "interface/counters/divisions_large/unit_SNE_geochanter_icon.dds",
    "interface/counters/divisions_large/custom_template_028.dds",
    // divisions_small
    "interface/counters/divisions_small/onmap_unit_SNE_electrohammer_icon.dds",
    "interface/counters/divisions_small/onmap_unit_SNE_anemoboxer_icon.dds",
    "interface/counters/divisions_small/onmap_unit_SNE_hydrogunner_icon.dds",
    "interface/counters/divisions_small/onmap_unit_SNE_cryogunner_icon.dds",
    "interface/counters/divisions_small/onmap_unit_SNE_geochanter_icon.dds",
    "interface/counters/divisions_small/custom_template_028.dds"
];

log("\nStep 2: Process " + targets.length + " target DDS files");

for (var t = 0; t < targets.length; t++) {
    var tgtPath = baseDir + targets[t];
    var tgtFile = new File(tgtPath);

    if (!tgtFile.exists) {
        log("  SKIP (not found): " + targets[t]);
        continue;
    }

    log("  [" + (t+1) + "/" + targets.length + "] " + targets[t]);

    try {
        // Open target DDS
        var tgtDoc = app.open(tgtFile);
        var tgtW = tgtDoc.width.value;
        var tgtH = tgtDoc.height.value;
        var frameW = tgtW / 2;
        log("    Size: " + tgtW + "x" + tgtH + ", frame: " + frameW + "x" + tgtH);

        // Copy entire content
        tgtDoc.selection.selectAll();
        tgtDoc.selection.copy();
        tgtDoc.close(SaveOptions.DONOTSAVECHANGES);

        // Create new doc at frame size (half width)
        var newDoc = app.documents.add(frameW, tgtH, 72, "fixed", NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
        newDoc.paste();
        var layer1 = newDoc.activeLayer;

        // Scale to fit frame: compress horizontally to 50% of original
        var scaleX = (frameW / tgtW) * 100;
        layer1.resize(scaleX, 100, AnchorPosition.TOPLEFT);
        newDoc.flatten();

        // Double canvas width (add right half space)
        newDoc.resizeCanvas(tgtW, tgtH, AnchorPosition.MIDDLELEFT);
        log("    Canvas resized to: " + newDoc.width.value + "x" + newDoc.height.value);

        // Open temp right frame and copy
        var srcDoc = app.open(tempRightFile);
        srcDoc.selection.selectAll();
        srcDoc.selection.copy();
        srcDoc.close(SaveOptions.DONOTSAVECHANGES);

        // Paste into target
        newDoc.paste();
        var layer2 = newDoc.activeLayer;
        var b = layer2.bounds;
        var pastedW = b[2].value - b[0].value;
        var pastedH = b[3].value - b[1].value;
        log("    Pasted right frame: " + pastedW + "x" + pastedH + " at (" + b[0].value + "," + b[1].value + ")");

        // Scale to fill right half
        scaleX = (frameW / pastedW) * 100;
        var scaleY = (tgtH / pastedH) * 100;
        layer2.resize(scaleX, scaleY, AnchorPosition.TOPLEFT);

        // Get new bounds and translate to right half position
        b = layer2.bounds;
        var moveX = frameW - b[0].value;
        var moveY = 0 - b[1].value;
        layer2.translate(moveX, moveY);
        log("    Moved right frame to: (" + frameW + ",0)");

        newDoc.flatten();

        // Save as PNG (will convert to DDS later)
        var pngPath = tgtPath.replace(/\.dds$/i, "_fixed.png");
        var pngFile = new File(pngPath);
        pngOpts = new ExportOptionsSaveForWeb();
        pngOpts.format = SaveDocumentType.PNG;
        pngOpts.PNG8 = false;
        newDoc.exportDocument(pngFile, ExportType.SAVEFORWEB, pngOpts);
        log("    Saved PNG: " + pngPath);

        newDoc.close(SaveOptions.DONOTSAVECHANGES);

    } catch(e) {
        log("    ERROR: " + e.toString());
        try { app.activeDocument.close(SaveOptions.DONOTSAVECHANGES); } catch(e2) {}
    }
}

// Cleanup temp
try { tempRightFile.remove(); } catch(e) {}
log("\nDONE - All icons saved as PNG, ready for texconv conversion");
logFile.close();
