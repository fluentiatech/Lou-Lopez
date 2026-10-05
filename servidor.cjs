// Local preview server for this folder:  node servidor.cjs [port]
// (python -m http.server drops connections on Windows when several images load at once.)
const http = require('http')
const fs = require('fs')
const path = require('path')

const root = __dirname
const port = Number(process.argv[2]) || 3210
const types = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.woff2': 'font/woff2',
  '.ico': 'image/x-icon',
}

http
  .createServer((req, res) => {
    let rel = decodeURIComponent(req.url.split('?')[0])
    if (rel.endsWith('/')) rel += 'index.html'
    const file = path.join(root, rel)
    if (!file.startsWith(root)) {
      res.writeHead(403).end()
      return
    }
    fs.readFile(file, (err, data) => {
      if (err) {
        res.writeHead(404, { 'Content-Type': 'text/plain' }).end('Not found')
        return
      }
      res.writeHead(200, {
        'Content-Type': types[path.extname(file).toLowerCase()] || 'application/octet-stream',
        'Cache-Control': 'no-cache',
      })
      res.end(data)
    })
  })
  .listen(port, () => console.log(`http://localhost:${port}/`))
