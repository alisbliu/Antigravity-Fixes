const fs = require("fs");
const path = require("path");
const os = require("os");

const homeDir = os.homedir();
const files = [
  path.join(homeDir, ".antigravity-ide/extensions/github.vscode-pull-request-github-0.126.0-universal/dist/extension.js"),
  path.join(homeDir, ".antigravity/extensions/github.vscode-pull-request-github-0.126.0-universal/dist/extension.js")
];

files.forEach(file => {
  if (fs.existsSync(file)) {
    console.log("File exists:", file);
    const content = fs.readFileSync(file, "utf8");
    console.log("  Includes MarkdownString label Target 1 (M={label:new r.MarkdownString(this._getLabel(),!0)}):", content.includes("M={label:new r.MarkdownString(this._getLabel(),!0)}"));
    console.log("  Includes MarkdownString label Target 2 (b={label:new r.MarkdownString(`$(check) ${l}`,!0)}):", content.includes("b={label:new r.MarkdownString(`$(check) ${l}`,!0)}"));
    console.log("  Includes Patched Label 1 (M={label:this._getLabel()}):", content.includes("M={label:this._getLabel()}"));
    console.log("  Includes Patched Label 2 (b={label:`$(check) ${l}`}):", content.includes("b={label:`$(check) ${l}`}"));
  } else {
    console.log("File NOT found:", file);
  }
});
