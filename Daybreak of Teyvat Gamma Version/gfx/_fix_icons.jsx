// Fix Fatui/HIP icons: ensure 2-frame format with DOT_Infantryer right frame
#target photoshop
app.preferences.rulerUnits = Units.PIXELS;

var basePath = "C:/Users/LR/Documents/GitHub/Ilyich-Genshin-Test-Version/Daybreak of Teyvat Beta Version/gfx/";

// Step 1: Open DOT_Infantryer_small, extract right half
var dotPath = basePath + "texticons/unit_DOT_Infantryer_small.dds";
var dotDoc = app.open(new File(dotPath));
var dotW = dotDoc.width.value;
var dotH = dotDoc.height.value;
var halfW = dotW / 2;

// Crop to right half
dotDoc.crop([halfW, 0, dotW, dotH]);
dotDoc.flatten();

// Save right half as temp PNG
var tempFile = new File(basePath + "_temp_right.png");
var pngOpts = new ExportOptionsSaveForWeb();
pngOpts.format = SaveDocumentType.PNG;
pngOpts.PNG8 = false;
dotDoc.exportDocument(tempFile, ExportType.SAVEFORWEB, pngOpts);
dotDoc.close(SaveOptions.DONOTSAVECHANGES);

// Step 2: Process each target DDS
var targets = [
    // divisions_large
    "interface/counters/divisions_large/unit_SNE_electrohammer_icon.dds",
    "interface/counters/divisions_large/unit_SNE_anemoboxer_icon.dds",
    "interface/counters/divisions_large/unit_SNE_hydrogunner_icon.dds",
    "interface/counters/divisions_large/unit_SNE_cryogunner_icon.dds",
    "interface/counters/divisions_large/unit_SNE_pyroslinger_icon.dds",
    "interface/counters/divisions_large/unit_SNE_geochanter_icon.dds",
    "interface/counters/divisions_large/custom_template_028.dds",
    // divisions_small
    "interface/counters/divisions_small/onmap_unit_SNE_electrohammer_icon.dds",
    "interface/counters/divisions_small/onmap_unit_SNE_anemoboxer_icon.dds",
    "interface/counters/divisions_small/onmap_unit_SNE_hydrogunner_icon.dds",
    "interface/counters/divisions_small/onmap_unit_SNE_cryogunner_icon.dds",
    "interface/counters/divisions_small/onmap_unit_SNE_pyroslinger_icon.dds",
    "interface/counters/divisions_small/onmap_unit_SNE_geochanter_icon.dds",
    "interface/counters/divisions_small/custom_template_028.dds"
];

for (var i = 0; i < targets.length; i++) {
    var tgtPath = basePath + targets[i];
    var tgtFile = new File(tgtPath);
    if (!tgtFile.exists) {
        $.writeln("SKIP (not found): " + targets[i]);
        continue;
    }

    var tgtDoc = app.open(tgtFile);
    var tgtW = tgtDoc.width.value;
    var tgtH = tgtDoc.height.value;
    var tgtHalfW = tgtW / 2;

    // Delete right half content: select right half and clear
    tgtDoc.selection.select([[tgtHalfW, 0], [tgtW, 0], [tgtW, tgtH], [tgtHalfW, tgtH]]);
    tgtDoc.selection.clear();

    // Open temp right frame and copy
    var srcDoc = app.open(tempFile);
    srcDoc.selection.selectAll();
    srcDoc.selection.copy();
    srcDoc.close(SaveOptions.DONOTSAVECHANGES);

    // Paste into target (will be centered as new layer)
    tgtDoc.paste();
    var newLayer = tgtDoc.activeLayer;

    // Move the pasted layer to fill the right half
    // The pasted layer is the size of temp file (halfW x dotH)
    // We need to scale it to tgtHalfW x tgtH
    var srcW = halfW;
    var srcH = dotH;

    // Calculate position: we want the layer to occupy [tgtHalfW, 0, tgtW, tgtH]
    // The pasted layer is currently centered, so we need to move it
    var layerBounds = newLayer.bounds; // [left, top, right, bottom]
    var layerW = layerBounds[2].value - layerBounds[0].value;
    var layerH = layerBounds[3].value - layerBounds[1].value;

    // Scale the layer to fill right half (maintain aspect ratio, stretch to fill)
    var scaleX = (tgtHalfW / layerW) * 100;
    var scaleY = (tgtH / layerH) * 100;
    newLayer.resize(scaleX, scaleY, AnchorPosition.TOPLEFT);

    // Move to right half position: top-left at (tgtHalfW, 0)
    newLayer.translate(tgtHalfW - layerBounds[0].value, -layerBounds[1].value);

    // Merge and save
    tgtDoc.flatten();

    // Save as DDS
    var ddsFile = new File(tgtPath);
    var ddsOpts = new DDSExportOptions();
    ddsOpts.compressionType = DDSCompressionType.DXT5;
    ddsOpts.mipMaps = false;
    tgtDoc.saveAs(ddsFile, ddsOpts, true);
    tgtDoc.close(SaveOptions.DONOTSAVECHANGES);

    $.writeln("OK: " + targets[i] + " (" + tgtW + "x" + tgtH + ")");
}

// Cleanup temp file
tempFile.remove();
$.writeln("DONE - all icons fixed");
