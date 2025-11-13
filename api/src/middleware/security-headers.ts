/**
 * security-headers.ts - Security headers middleware for Express API
 *
 * Implements OWASP-recommended security headers to protect against
 * common web vulnerabilities (XSS, clickjacking, MIME sniffing, etc.)
 *
 * References:
 *   - OWASP Secure Headers Project: https://owasp.org/www-project-secure-headers/
 *   - Mozilla Observatory: https://observatory.mozilla.org/
 *
 * Created: 2025-01-12
 */

import { Request, Response, NextFunction } from 'express';

/**
 * Security headers configuration interface
 */
interface SecurityHeadersConfig {
  /**
   * Content Security Policy directives
   * Prevents XSS attacks by controlling resource loading
   */
  contentSecurityPolicy?: {
    directives?: {
      defaultSrc?: string[];
      scriptSrc?: string[];
      styleSrc?: string[];
      imgSrc?: string[];
      fontSrc?: string[];
      connectSrc?: string[];
      frameSrc?: string[];
      objectSrc?: string[];
      mediaSrc?: string[];
      workerSrc?: string[];
      formAction?: string[];
      frameAncestors?: string[];
      baseUri?: string[];
      upgradeInsecureRequests?: boolean;
    };
    reportOnly?: boolean;
  };

  /**
   * HTTP Strict Transport Security (HSTS)
   * Forces HTTPS connections
   */
  strictTransportSecurity?: {
    maxAge?: number;
    includeSubDomains?: boolean;
    preload?: boolean;
  };

  /**
   * X-Frame-Options
   * Prevents clickjacking attacks
   */
  xFrameOptions?: 'DENY' | 'SAMEORIGIN';

  /**
   * X-Content-Type-Options
   * Prevents MIME type sniffing
   */
  xContentTypeOptions?: boolean;

  /**
   * X-XSS-Protection (legacy, but still useful for older browsers)
   * Enables browser XSS filter
   */
  xXssProtection?: boolean;

  /**
   * Referrer-Policy
   * Controls referrer information sent with requests
   */
  referrerPolicy?: string;

  /**
   * Permissions-Policy (formerly Feature-Policy)
   * Controls browser features and APIs
   */
  permissionsPolicy?: {
    geolocation?: string[];
    microphone?: string[];
    camera?: string[];
    payment?: string[];
    usb?: string[];
    accelerometer?: string[];
    gyroscope?: string[];
    magnetometer?: string[];
  };
}

/**
 * Default security headers configuration (OWASP recommended)
 */
const DEFAULT_CONFIG: SecurityHeadersConfig = {
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"], // Unsafe-inline needed for some CSS frameworks
      imgSrc: ["'self'", 'data:', 'https:'],
      fontSrc: ["'self'", 'data:'],
      connectSrc: ["'self'"],
      frameSrc: ["'none'"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      workerSrc: ["'self'", 'blob:'],
      formAction: ["'self'"],
      frameAncestors: ["'none'"],
      baseUri: ["'self'"],
      upgradeInsecureRequests: true,
    },
    reportOnly: false,
  },

  strictTransportSecurity: {
    maxAge: 31536000, // 1 year
    includeSubDomains: true,
    preload: false, // Set to true only after registering with hstspreload.org
  },

  xFrameOptions: 'DENY',
  xContentTypeOptions: true,
  xXssProtection: true,

  referrerPolicy: 'strict-origin-when-cross-origin',

  permissionsPolicy: {
    geolocation: [],
    microphone: [],
    camera: [],
    payment: [],
    usb: [],
    accelerometer: [],
    gyroscope: [],
    magnetometer: [],
  },
};

/**
 * Build Content-Security-Policy header value from directives
 */
function buildCSPHeader(directives: any): string {
  const policies: string[] = [];

  for (const [key, value] of Object.entries(directives)) {
    if (key === 'upgradeInsecureRequests' && value === true) {
      policies.push('upgrade-insecure-requests');
      continue;
    }

    if (Array.isArray(value) && value.length > 0) {
      // Convert camelCase to kebab-case
      const directive = key.replace(/([A-Z])/g, '-$1').toLowerCase();
      policies.push(`${directive} ${value.join(' ')}`);
    }
  }

  return policies.join('; ');
}

/**
 * Build Permissions-Policy header value from policies
 */
function buildPermissionsPolicyHeader(policies: any): string {
  const directives: string[] = [];

  for (const [feature, origins] of Object.entries(policies)) {
    if (Array.isArray(origins)) {
      if (origins.length === 0) {
        directives.push(`${feature}=()`);
      } else {
        directives.push(`${feature}=(${origins.join(' ')})`);
      }
    }
  }

  return directives.join(', ');
}

/**
 * Security headers middleware
 *
 * Usage:
 *   import { securityHeaders } from './middleware/security-headers';
 *   app.use(securityHeaders());
 *
 *   // Or with custom config:
 *   app.use(securityHeaders({
 *     contentSecurityPolicy: {
 *       directives: {
 *         scriptSrc: ["'self'", "https://cdn.example.com"]
 *       }
 *     }
 *   }));
 *
 * @param config Custom security headers configuration
 * @returns Express middleware function
 */
export function securityHeaders(
  config: SecurityHeadersConfig = {}
): (req: Request, res: Response, next: NextFunction) => void {
  // Merge custom config with defaults
  const mergedConfig = {
    ...DEFAULT_CONFIG,
    ...config,
    contentSecurityPolicy: {
      ...DEFAULT_CONFIG.contentSecurityPolicy,
      ...config.contentSecurityPolicy,
      directives: {
        ...DEFAULT_CONFIG.contentSecurityPolicy?.directives,
        ...config.contentSecurityPolicy?.directives,
      },
    },
    strictTransportSecurity: {
      ...DEFAULT_CONFIG.strictTransportSecurity,
      ...config.strictTransportSecurity,
    },
    permissionsPolicy: {
      ...DEFAULT_CONFIG.permissionsPolicy,
      ...config.permissionsPolicy,
    },
  };

  return (req: Request, res: Response, next: NextFunction): void => {
    // Content-Security-Policy
    if (mergedConfig.contentSecurityPolicy?.directives) {
      const cspHeader = buildCSPHeader(mergedConfig.contentSecurityPolicy.directives);
      const headerName = mergedConfig.contentSecurityPolicy.reportOnly
        ? 'Content-Security-Policy-Report-Only'
        : 'Content-Security-Policy';
      res.setHeader(headerName, cspHeader);
    }

    // HTTP Strict-Transport-Security (HSTS)
    if (mergedConfig.strictTransportSecurity) {
      const { maxAge, includeSubDomains, preload } = mergedConfig.strictTransportSecurity;
      let hstsValue = `max-age=${maxAge}`;
      if (includeSubDomains) hstsValue += '; includeSubDomains';
      if (preload) hstsValue += '; preload';
      res.setHeader('Strict-Transport-Security', hstsValue);
    }

    // X-Frame-Options
    if (mergedConfig.xFrameOptions) {
      res.setHeader('X-Frame-Options', mergedConfig.xFrameOptions);
    }

    // X-Content-Type-Options
    if (mergedConfig.xContentTypeOptions) {
      res.setHeader('X-Content-Type-Options', 'nosniff');
    }

    // X-XSS-Protection (legacy support)
    if (mergedConfig.xXssProtection) {
      res.setHeader('X-XSS-Protection', '1; mode=block');
    }

    // Referrer-Policy
    if (mergedConfig.referrerPolicy) {
      res.setHeader('Referrer-Policy', mergedConfig.referrerPolicy);
    }

    // Permissions-Policy
    if (mergedConfig.permissionsPolicy) {
      const permissionsHeader = buildPermissionsPolicyHeader(mergedConfig.permissionsPolicy);
      if (permissionsHeader) {
        res.setHeader('Permissions-Policy', permissionsHeader);
      }
    }

    // Additional security headers
    res.setHeader('X-DNS-Prefetch-Control', 'off');
    res.setHeader('X-Download-Options', 'noopen');
    res.setHeader('X-Permitted-Cross-Domain-Policies', 'none');

    next();
  };
}

/**
 * Development mode security headers (more permissive)
 * Allows hot module reloading and development tools
 */
export function devSecurityHeaders(): (req: Request, res: Response, next: NextFunction) => void {
  return securityHeaders({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'"], // Allow eval for HMR
        styleSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["'self'", 'data:', 'https:', 'http:'],
        fontSrc: ["'self'", 'data:'],
        connectSrc: ["'self'", 'ws:', 'wss:'], // Allow WebSocket for HMR
        frameSrc: ["'self'"],
        objectSrc: ["'none'"],
        upgradeInsecureRequests: false, // Don't force HTTPS in development
      },
    },
    strictTransportSecurity: undefined, // No HSTS in development
  });
}

/**
 * Example usage in Express app:
 *
 * ```typescript
 * import express from 'express';
 * import { securityHeaders, devSecurityHeaders } from './middleware/security-headers';
 *
 * const app = express();
 *
 * // Use appropriate headers based on environment
 * if (process.env.NODE_ENV === 'production') {
 *   app.use(securityHeaders());
 * } else {
 *   app.use(devSecurityHeaders());
 * }
 *
 * // Your routes here
 * app.get('/api/health', (req, res) => {
 *   res.json({ status: 'ok' });
 * });
 *
 * app.listen(3001, () => {
 *   console.log('Server running with security headers');
 * });
 * ```
 */
