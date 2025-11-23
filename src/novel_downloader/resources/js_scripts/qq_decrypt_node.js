#!/usr/bin/env node

// ---- GLOBAL ENVIRONMENT SHIMS ----
const _realSetInterval = global.setInterval;
global.setInterval = function(fn, t) {
  if (typeof fn === "string") {
    if (fn.includes("debugger")) {
      // console.log("Blocked interval:", fn);
      return 0;
    }
    // if (/somePattern/.test(fn)) return 0;
  }
  return _realSetInterval(fn, t);
};

const shimEnv = {
  location: {
    protocol: "https:",
    hostname: "book.qq.com",
  },
  document: {
    createElement: (tag) => {
      if (tag === "iframe") {
        const win = {};
        win.window = win;
        win.eval = (code) => eval(code);
        return {
          style: {},
          contentWindow: win,
        };
      }
      return { style: {}, appendChild: () => {} };
    },
    body: { appendChild: () => {} },
  },
};

global.window = global;
globalThis.window = global;
globalThis.self = global;

for (const [key, value] of Object.entries(shimEnv)) {
  globalThis[key] = value;
}

// ---- DECRYPT FUNCTION ----
const Fock = require("./cefc2a5d.pz1phw.js");

async function decrypt(enContent, cuChapterId, fkp, fuid) {
  Fock.setupUserKey(fuid);
  eval(atob(fkp));

  return new Promise((resolve, reject) => {
    Fock.unlock(enContent, cuChapterId, (code, decrypted) => {
      if (code === 0) {
        resolve(decrypted);
      } else {
        reject(new Error(`Fock.unlock failed, code=${code}`));
      }
    });
  });
}

// ---- MAIN ----
let input = "";

process.stdin.on("data", chunk => input += chunk);

process.stdin.on("end", async () => {
  try {
    const [raw_enContent, raw_cuChapterId, raw_fkp, raw_fuid] = JSON.parse(input);

    const result = await decrypt(
      String(raw_enContent),
      String(raw_cuChapterId),
      String(raw_fkp),
      String(raw_fuid),
    );

    process.stdout.write(result);
    process.exit(0);
  } catch (err) {
    console.error(String(err));
    process.exit(1);
  }
});
