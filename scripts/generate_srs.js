const { spawnSync } = require("node:child_process");
const path = require("node:path");
const result = spawnSync(process.env.PYTHON || "python", [path.join(__dirname, "build_documents.py")], { stdio: "inherit" });
process.exit(result.status ?? 1);
