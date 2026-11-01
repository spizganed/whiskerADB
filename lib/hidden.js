#!/usr/bin/env node
// hidden.js: a display that no window shows, made by scrcpy-server (the Android side of scrcpy).
// The server makes the display while its video and control sockets stay open, so this process keeps both open and
// drains them. It writes the display id and the SurfaceFlinger id for pp, then runs until pp display off kills it.
// usage: node hidden.js JAR SIZE OUTDIR     (SIZE like 1080x2400/420)
const { execFileSync, spawn } = require('node:child_process');
const net = require('node:net');
const fs = require('node:fs');
const [jar, size, out] = process.argv.slice(2);
const VERSION = process.env.PP_SCRCPY_VERSION || '5.0.1';
const adb = (...a) => execFileSync('adb', a, { encoding: 'utf8' });

adb('push', jar, '/data/local/tmp/scrcpy-server.jar');
const port = Number(adb('forward', 'tcp:0', 'localabstract:scrcpy').trim());
// Low rate and bit rate: nobody watches the video, the server only needs a sink.
const server = spawn('adb', ['shell', `CLASSPATH=/data/local/tmp/scrcpy-server.jar app_process / com.genymobile.scrcpy.Server ${VERSION} tunnel_forward=true audio=false max_fps=2 video_bit_rate=200000 new_display=${size}`], { stdio: 'ignore' });
server.on('exit', () => process.exit(1));

// adb accepts a TCP connection before the server listens; a connection that closes with no byte is tried again.
function open(label, done) {
  const s = net.connect(port, '127.0.0.1');
  let got = false;
  s.on('data', () => { if (!got) { got = true; done(s); } });
  s.on('error', () => {});
  s.on('close', () => { if (!got) setTimeout(() => open(label, done), 300); });
}
open('video', () => open('control', () => {}));

const started = Date.now();
const poll = setInterval(() => {
  if (Date.now() - started > 30000) { console.error('hidden: the display did not start'); process.exit(1); }
  try {
    const m = adb('shell', 'cmd display get-displays').match(/Display id (\d+): DisplayInfo\{"scrcpy"/);
    const sf = adb('shell', 'dumpsys SurfaceFlinger --display-id').match(/^Display (\d+) \(Virtual display\): displayName="scrcpy"/m);
    if (!m || !sf) return;
    fs.writeFileSync(`${out}/display.sf`, sf[1] + '\n');
    fs.writeFileSync(`${out}/display`, m[1] + '\n');
    clearInterval(poll);
  } catch {}
}, 700);

const stop = () => { try { server.kill(); } catch {} try { adb('forward', '--remove', `tcp:${port}`); } catch {} process.exit(0); };
process.on('SIGTERM', stop); process.on('SIGINT', stop);
