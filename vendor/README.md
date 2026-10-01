# vendor/

`anthropic-sdk-0.131.0.js` is the official Anthropic TypeScript SDK
([@anthropic-ai/sdk](https://www.npmjs.com/package/@anthropic-ai/sdk) 0.131.0, MIT license, see
`LICENSE-anthropic-sdk`) bundled into one browser module. The website loads it only
when someone labels posts with their own API key. It's served from this repo instead
of a CDN so that no third-party script runs on a page holding an API key.

To rebuild it, for example for a newer SDK version:

```bash
npm install @anthropic-ai/sdk@0.131.0 esbuild
echo "export { default } from '@anthropic-ai/sdk';" > entry.mjs
npx esbuild entry.mjs --bundle --format=esm --platform=browser --minify \
  --legal-comments=inline --outfile=anthropic-sdk-0.131.0.js
```

If you change the version, update the file name in `loadSDK()` in `index.html`.
