const fs = require("fs");
const path = require("path");
const os = require("os");

const homeDir = os.homedir();
const extensionsDirs = [
  path.join(homeDir, ".antigravity-ide/extensions/github.vscode-pull-request-github-0.126.0-universal"),
  path.join(homeDir, ".antigravity/extensions/github.vscode-pull-request-github-0.126.0-universal")
];

extensionsDirs.forEach(dirPath => {
  const extJs = path.join(dirPath, "dist/extension.js");
  const pkgJson = path.join(dirPath, "package.json");

  // 1. Patch dist/extension.js
  if (fs.existsSync(extJs)) {
    console.log("Patching extension.js at:", extJs);
    let content = fs.readFileSync(extJs, "utf8");

    const t1 = "M={label:new r.MarkdownString(this._getLabel(),!0)}";
    const r1 = "M={label:this._getLabel()}";
    const t2 = "b={label:new r.MarkdownString(`$(check) ${l}`,!0)}";
    const r2 = "b={label:`$(check) ${l}`}";

    let modified = false;
    if (content.includes(t1)) {
      content = content.replace(t1, r1);
      modified = true;
      console.log("  Patched Target 1 (MarkdownString label)");
    } else {
      console.log("  Target 1 already patched or not found.");
    }

    if (content.includes(t2)) {
      content = content.replace(t2, r2);
      modified = true;
      console.log("  Patched Target 2 (MarkdownString check status)");
    } else {
      console.log("  Target 2 already patched or not found.");
    }

    if (modified) {
      fs.writeFileSync(extJs, content, "utf8");
      console.log("  Successfully saved extension.js");
    }
  } else {
    console.log("extension.js not found at:", extJs);
  }

  // 2. Patch package.json (Remove unauthorized Chat APIs)
  if (fs.existsSync(pkgJson)) {
    console.log("Patching package.json at:", pkgJson);
    try {
      const pkg = JSON.parse(fs.readFileSync(pkgJson, "utf8"));
      let modified = false;

      if (pkg.contributes && pkg.contributes.menus) {
        if (pkg.contributes.menus["chat/chatSessions"]) {
          delete pkg.contributes.menus["chat/chatSessions"];
          modified = true;
          console.log("  Removed proposed menu API: chat/chatSessions");
        }
        if (pkg.contributes.menus["chat/input/editing/sessionToolbar"]) {
          delete pkg.contributes.menus["chat/input/editing/sessionToolbar"];
          modified = true;
          console.log("  Removed proposed menu API: chat/input/editing/sessionToolbar");
        }
      }

      if (modified) {
        fs.writeFileSync(pkgJson, JSON.stringify(pkg, null, 2), "utf8");
        console.log("  Successfully saved package.json");
      } else {
        console.log("  package.json already clean.");
      }
    } catch (e) {
      console.error("  Error patching package.json:", e);
    }
  } else {
    console.log("package.json not found at:", pkgJson);
  }
});
