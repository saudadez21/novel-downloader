window = global;
null_fun = function(){console.log(arguments);}
window.outerHeight = 1000
window.innerHeight = 100
globalThis = window
self = window
window.location = {}
location.protocol = "https:"
location.hostname = "vipreader.qidian.com"
setTimeout = null_fun
setInterval = null_fun
document = {createElement: null_fun, documentElement: {}, createEvent: null_fun, currentScript: {src: "https://qdfepccdn.qidian.com/www.qidian.com/fock/116594983210.js"}, domain: 'qidian.com'}
navigator = {userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'}
performance = {}
performance.navigation = {type: 1}

// ---- DECRYPT FUNCTION ----
const Fock = require('./4819793b.qeooxh.js');

async function decrypt(enContent, cuChapterId, fkp, fuid) {
  Fock.initialize();
  Fock.setupUserKey(fuid);
  eval(atob(fkp));
  isFockInit = true;

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
const fs = require('fs');

(async () => {
  const [inputPath, outputPath] = process.argv.slice(2);
  if (!inputPath || !outputPath) {
    console.error(
      "Usage: node script.js <input.json> <output.txt>"
    );
    process.exit(1);
  }

  try {
    const inputData = fs.readFileSync(inputPath, "utf-8");
    const [
      raw_enContent,
      raw_cuChapterId,
      raw_fkp,
      raw_fuid
    ] = JSON.parse(inputData);

    const decryptPromise = decrypt(
      String(raw_enContent),
      String(raw_cuChapterId),
      String(raw_fkp),
      String(raw_fuid)
    );

    const timeoutMs = 5000;
    const timerPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error(`decrypt timeout after ${timeoutMs}ms`));
      }, timeoutMs);
    });

    const result = await Promise.race([
      decryptPromise,
      timerPromise
    ]);

    fs.writeFileSync(outputPath, result, "utf-8");
  } catch (err) {
    console.error("Failed to decrypt:", err);
    process.exit(1);
  }
})();
