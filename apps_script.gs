/**
 * Google Apps Script Web App for Instagram Auto Poster
 *
 * Searches BOTH URL columns (A: image, C: video) for a matching URL
 * and marks the corresponding Status column (B or D) as POSTED.
 *
 * Deploy as Web App:
 *   Extensions > Apps Script > paste this code > Deploy > New deployment
 *   Type: Web app | Execute as: Me | Who has access: Anyone
 *   Copy the deployment URL and use it in gsheet_poster.py
 */

function doGet(e) {
  var url = e.parameter.url;
  if (!url) {
    return ContentService.createTextOutput("NO_URL_PARAM");
  }

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  var data = sheet.getDataRange().getValues();
  var found = false;

  // Normalize for comparison (trim whitespace, ignore protocol differences)
  function normalize(s) {
    return String(s || "").trim().toLowerCase()
      .replace(/^https?:\/\//, "")
      .replace(/\/$/, "");
  }
  var targetNorm = normalize(url);

  for (var i = 1; i < data.length; i++) {  // skip header row
    var row = data[i];

    // Column A (index 0) = image URL, Column B (index 1) = its Status
    if (row[0] && normalize(row[0]) === targetNorm) {
      sheet.getRange(i + 1, 2).setValue("POSTED");  // column B
      found = true;
      break;
    }

    // Column C (index 2) = video URL, Column D (index 3) = its Status
    if (row.length > 2 && row[2] && normalize(row[2]) === targetNorm) {
      sheet.getRange(i + 1, 4).setValue("POSTED");  // column D
      found = true;
      break;
    }
  }

  if (found) {
    return ContentService.createTextOutput("UPDATED");
  } else {
    return ContentService.createTextOutput("NOT_FOUND");
  }
}
