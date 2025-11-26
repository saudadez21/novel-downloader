#!/usr/bin/env node

let code = "";
process.stdin.on("data", chunk => code += chunk);
process.stdin.on("end", () => {
  try {
    // Make sure object literals parse correctly
    const result = eval("(" + code + ")");
    console.log(JSON.stringify(result));
  } catch (err) {
    console.error("Error:", err);
    process.exit(1);
  }
});
