/**
 * vite.config.ts - Vite configuration with security headers
 *
 * Configures Vite build tool with:
 * - React + TypeScript support
 * - Security headers plugin
 * - Three.js optimization (for 3D rendering)
 * - Path aliases
 * - Development server configuration
 *
 * Created: 2025-01-12
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import type { Plugin } from 'vite';

/**
 * Vite plugin to add security headers to development server responses
 *
 * Note: In production (nginx), security headers are set by nginx configuration.
 * This plugin ensures consistent security headers during development.
 */
function securityHeadersPlugin(): Plugin {
  return {
    name: 'security-headers',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        // Content Security Policy (CSP)
        // Allows Three.js WebGL and inline styles needed for React
        res.setHeader(
          'Content-Security-Policy',
          [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // unsafe-eval needed for Three.js
            "style-src 'self' 'unsafe-inline'", // unsafe-inline needed for styled-components
            "img-src 'self' data: https: blob:",
            "font-src 'self' data:",
            "connect-src 'self' ws: wss:", // WebSocket for HMR and spatial engine
            "worker-src 'self' blob:", // Web Workers for Three.js
            "frame-src 'none'",
            "object-src 'none'",
            "base-uri 'self'",
          ].join('; ')
        );

        // X-Frame-Options - Prevent clickjacking
        res.setHeader('X-Frame-Options', 'DENY');

        // X-Content-Type-Options - Prevent MIME sniffing
        res.setHeader('X-Content-Type-Options', 'nosniff');

        // X-XSS-Protection (legacy, but helpful for older browsers)
        res.setHeader('X-XSS-Protection', '1; mode=block');

        // Referrer-Policy - Control referrer information
        res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');

        // Permissions-Policy - Disable unnecessary browser features
        res.setHeader(
          'Permissions-Policy',
          [
            'geolocation=()',
            'microphone=()',
            'camera=()',
            'payment=()',
            'usb=()',
          ].join(', ')
        );

        // Additional security headers
        res.setHeader('X-DNS-Prefetch-Control', 'off');
        res.setHeader('X-Download-Options', 'noopen');
        res.setHeader('X-Permitted-Cross-Domain-Policies', 'none');

        next();
      });
    },
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    securityHeadersPlugin(),
  ],

  // Path aliases for cleaner imports
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@services': path.resolve(__dirname, './src/services'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@assets': path.resolve(__dirname, './src/assets'),
    },
  },

  // Development server configuration
  server: {
    port: 5173,
    host: '0.0.0.0', // Allow access from WSL2
    strictPort: true,
    open: false,

    // Proxy API requests to backend
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:3001',
        ws: true,
        changeOrigin: true,
      },
    },

    // CORS configuration for development
    cors: {
      origin: ['http://localhost:3001', 'http://localhost:3000'],
      credentials: true,
    },
  },

  // Build optimization
  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: 'terser',

    // Chunk splitting for better caching
    rollupOptions: {
      output: {
        manualChunks: {
          // Three.js and related libraries in separate chunk
          'three': ['three', '@react-three/fiber', '@react-three/drei'],
          // React core
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // UI libraries
          'ui-vendor': ['@mui/material', '@emotion/react', '@emotion/styled'],
        },
      },
    },

    // Terser options for production minification
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true,
      },
    },

    // Large chunk warning threshold (Three.js is large)
    chunkSizeWarningLimit: 1000, // 1MB
  },

  // Dependency optimization
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'three',
      '@react-three/fiber',
      '@react-three/drei',
    ],
    exclude: [],
  },

  // Environment variable prefix
  // Only variables starting with VITE_ will be exposed to client
  envPrefix: 'VITE_',

  // Preview server (for testing production build)
  preview: {
    port: 4173,
    host: '0.0.0.0',
    strictPort: true,
  },
});
