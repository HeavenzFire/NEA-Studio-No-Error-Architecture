# Deployment Guide - EBC Studio

## Production Build Status
✅ Build completed successfully
- Output directory: `/workspace/dist/`
- Main bundle: `dist/assets/index-B2tu4OtB.js` (896.37 kB, 236.97 kB gzipped)
- Entry point: `dist/index.html`

## Deployment Options

### Option 1: Static Hosting (Recommended)

Upload the contents of the `dist/` folder to any static hosting service:

#### Netlify
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod --dir=dist
```

#### Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

#### GitHub Pages
```bash
# Install gh-pages
npm install -gh-pages --save-dev

# Add to package.json scripts:
"deploy": "gh-pages -d dist"

# Run deployment
npm run deploy
```

### Option 2: Docker Container

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Create `nginx.conf`:
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /assets {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Build and run:
```bash
docker build -t ebc-studio .
docker run -p 80:80 ebc-studio
```

### Option 3: Direct Server Deployment

```bash
# Copy dist folder to server
scp -r dist/* user@your-server:/var/www/ebc-studio/

# Configure nginx/apache to serve from that directory
```

### Option 4: Cloud Storage + CDN

#### AWS S3 + CloudFront
```bash
# Install AWS CLI
aws s3 sync dist/ s3://your-bucket-name

# Create CloudFront distribution pointing to the bucket
```

#### Google Cloud Storage
```bash
# Install gsutil
gsutil -m cp -r dist/* gs://your-bucket-name

# Enable website hosting
```

## Environment Variables for Production

For the AI spec formalization feature to work in production, ensure:

1. **Vite Environment Variables**: Update `vite.config.ts` to use import.meta.env:
```typescript
define: {
  'process.env.API_KEY': JSON.stringify(import.meta.env.VITE_GEMINI_API_KEY),
  'process.env.GEMINI_API_KEY': JSON.stringify(import.meta.env.VITE_GEMINI_API_KEY)
}
```

2. **Set environment variable** on your hosting platform:
   - Netlify: Site settings → Build & deploy → Environment
   - Vercel: Project settings → Environment Variables
   - Docker: Pass via docker-compose or kubernetes secrets

## Post-Deployment Verification

1. ✅ Check that the app loads without errors
2. ✅ Verify Reactive/Bounded mode switching works
3. ✅ Test all domain selections (GENERAL, MEDICAL_ROBOTICS, AEROSPACE, FINTECH)
4. ✅ Confirm automation loop functions
5. ✅ Validate charts render correctly
6. ⚠️ Test spec extraction (requires API key configuration)

## Performance Optimization

The build warning about chunk size can be addressed by:

1. **Code Splitting**: Add dynamic imports for heavy components
2. **Manual Chunks**: Configure in vite.config.ts:
```typescript
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom'],
        charts: ['recharts'],
        icons: ['lucide-react']
      }
    }
  }
}
```

## Monitoring

Add analytics/error tracking:
- Google Analytics
- Sentry
- LogRocket

## Security Considerations

1. Never commit `.env.local` with actual API keys
2. Use environment variables for sensitive data
3. Enable HTTPS on production deployment
4. Set appropriate CORS headers if needed

## Rollback Strategy

Keep previous builds available:
```bash
# Keep last N builds
mkdir -p backups
cp -r dist backups/dist-$(date +%Y%m%d-%H%M%S)
```

## Support

For issues related to:
- **Build failures**: Check Node.js version compatibility
- **Runtime errors**: Inspect browser console
- **API integration**: Verify GEMINI_API_KEY is set correctly
- **Performance**: Review bundle analysis with `npm run build -- --debug`
