// Convert PSD files to DDS - with explicit file list
#target photoshop
app.preferences.rulerUnits = Units.PIXELS;

var logPath = "C:/Users/LR/Documents/GitHub/Ilyich-Genshin-Test-Version/Daybreak of Teyvat Beta Version/gfx/_convert_log.txt";
var logFile = new File(logPath);
logFile.open("w");
logFile.writeln("Starting PSD to DDS conversion (explicit paths)...");

// Use backslashes for paths as stored on disk
var basePath = "C:/Users/LR/Documents/GitHub/Ilyich-Genshin-Test-Version/Daybreak of Teyvat Beta Version/gfx/interface/counters/";

var psdPaths = [
    "divisions_large/unit_SNE_electrohammer_icon.psd",
    "divisions_large/unit_SNE_anemoboxer_icon.psd",
    "divisions_large/unit_SNE_hydrogunner_icon.psd",
    "divisions_large/unit_SNE_cryogunner_icon.psd",
    "divisions_large/unit_SNE_geochanter_icon.psd",
    "divisions_small/onmap_unit_SNE_electrohammer_icon.psd",
    "divisions_small/onmap_unit_SNE_anemoboxer_icon.psd",
    "divisions_small/onmap_unit_SNE_hydrogunner_icon.psd",
    "divisions_small/onmap_unit_SNE_cryogunner_icon.psd",
    "divisions_small/onmap_unit_SNE_geochanter_icon.psd"
];

// Check if custom_template_028.psd exists
var tmplLarge = new File(basePath + "divisions_large/custom_template_028.psd");
if (tmplLarge.exists) psdPaths.push("divisions_large/custom_template_028.psd");
var tmplSmall = new File(basePath + "divisions_small/custom_template_028.psd");
if (tmplSmall.exists) psdPaths.push("divisions_small/custom_template_028.psd");

logFile.writeln("PSD count: " + psdPaths.length);

for (var i = 0; i < psdPaths.length; i++) {
    var psdFullPath = basePath + psdPaths[i];
    var psdFile = new File(psdFullPath);

    if (!psdFile.exists) {
        logFile.writeln("MISSING: " + psdFullPath);
        continue;
    }

    logFile.writeln("Processing: " + psdPaths[i]);

    try {
        var doc = app.open(psdFile);
        logFile.writeln("  Size: " + doc.width.value + "x" + doc.height.value);

        var ddsPath = psdFullPath.replace(/\.psd$/i, ".dds");
        var ddsFile = new File(ddsPath);

        var opts = new DDSExportOptions();
        opts.compressionType = DDSCompressionType.DXT5;
        opts.mipMaps = false;

        doc.saveAs(ddsFile, opts, true);
        logFile.writeln("  OK: " + ddsPath);
        doc.close(SaveOptions.DONOTSAVECHANGES);
    } catch(e) {
        logFile.writeln("  ERROR: " + e.toString());
        try { app.activeDocument.close(SaveOptions.DONOTSAVECHANGES); } catch(e2) {}
    }
}

logFile.writeln("DONE");
logFile.close();
