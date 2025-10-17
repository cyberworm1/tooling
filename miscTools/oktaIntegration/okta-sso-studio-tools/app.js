/**
 * @file app.js
 * @description Minimal Express-style HTTP server that demonstrates Okta SSO concepts for studio tools.
 *              The implementation avoids external runtime dependencies so it can run in restricted
 *              environments while still illustrating how Okta middleware would integrate.
 */

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

try {
  // Optional dependency: load environment variables when dotenv is available.
  // eslint-disable-next-line global-require, import/no-extraneous-dependencies
  require('dotenv').config();
} catch (error) {
  // Safe to ignore when dotenv is not installed.
}

const port = Number(process.env.PORT) || 3000;

/**
 * Simple response helper.
 * @param {import('node:http').ServerResponse} res Response object
 * @param {number} status HTTP status code
 * @param {string} body Response body
 * @param {Record<string,string>} headers Additional headers
 */
function send(res, status, body, headers = {}) {
  const finalHeaders = {
    'Content-Type': 'text/html; charset=utf-8',
    ...headers
  };
  res.writeHead(status, finalHeaders);
  res.end(body);
}

/**
 * Runs middleware/handler pipeline sequentially.
 * @param {import('node:http').IncomingMessage} req Request object
 * @param {import('node:http').ServerResponse} res Response object
 * @param {Array<Function>} handlers Middleware/handlers list
 */
async function runPipeline(req, res, handlers) {
  let index = -1;

  const next = async () => {
    index += 1;
    const handler = handlers[index];
    if (!handler) {
      return;
    }
    await handler(req, res, next);
  };

  await next();
}

/**
 * Creates a lightweight application with Express-like routing capabilities.
 * @returns {{get: Function, use: Function, listen: Function, handle: Function}}
 */
function createApp() {
  const routes = [];
  const middlewares = [];

  return {
    use(fn) {
      middlewares.push(fn);
    },
    get(routePath, ...handlers) {
      routes.push({ method: 'GET', routePath, handlers });
    },
    async handle(req, res) {
      const handlers = [...middlewares];
      const match = routes.find((route) => route.method === req.method && route.routePath === req.url);
      if (match) {
        handlers.push(...match.handlers);
      } else {
        handlers.push((_req, response) => {
          send(response, 404, 'Not Found');
        });
      }

      try {
        await runPipeline(req, res, handlers);
      } catch (error) {
        console.error('Unhandled error', error);
        send(res, 500, 'Internal Server Error');
      }
    },
    listen(listenPort, callback) {
      const server = http.createServer((req, res) => {
        this.handle(req, res);
      });
      return server.listen(listenPort, callback);
    }
  };
}

/**
 * Provides a mock OIDC handler used for local development and automated tests.
 * The handler enriches requests with a user context similar to what Okta middleware would provide.
 *
 * @returns {{router: Function, ensureAuthenticated: Function, isMock: boolean}}
 */
function createMockOidc() {
  return {
    isMock: true,
    router: async (_req, _res, next) => {
      await next();
    },
    ensureAuthenticated: () => async (req, _res, next) => {
      if (!req.userContext) {
        req.userContext = {
          userinfo: {
            name: 'Mock User',
            email: 'mock.user@example.com',
            groups: ['Artist']
          }
        };
      }
      await next();
    }
  };
}

/**
 * Attempts to create a real Okta ExpressOIDC client. When dependencies or configuration are missing,
 * the function falls back to the mock implementation defined above.
 *
 * @returns {{router: Function, ensureAuthenticated: Function, isMock?: boolean}}
 */
function createOidcClient() {
  const requiredVars = ['OKTA_CLIENT_ID', 'OKTA_CLIENT_SECRET', 'OKTA_ISSUER'];
  const hasConfig = requiredVars.every((key) => Boolean(process.env[key]));

  if (hasConfig) {
    try {
      // eslint-disable-next-line global-require, import/no-extraneous-dependencies
      const { ExpressOIDC } = require('@okta/oidc-middleware');
      return new ExpressOIDC({
        issuer: process.env.OKTA_ISSUER,
        client_id: process.env.OKTA_CLIENT_ID,
        client_secret: process.env.OKTA_CLIENT_SECRET,
        appBaseUrl: process.env.APP_BASE_URL || `http://localhost:${port}`,
        scope: 'openid profile email groups',
        routes: {
          login: { path: '/login' },
          callback: { path: '/callback' }
        }
      });
    } catch (error) {
      console.warn('Falling back to mock OIDC handler:', error.message);
    }
  } else {
    console.warn('Okta environment variables missing; using mock OIDC handler for local development.');
  }

  return createMockOidc();
}

const app = createApp();
const oidc = createOidcClient();

app.use(async (req, _res, next) => {
  req.session = req.session || {};
  await next();
});

app.use(async (req, res, next) => {
  const normalizedPath = req.url === '/' ? '/index.html' : req.url;
  const filePath = path.join(__dirname, 'public', normalizedPath);
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const content = fs.readFileSync(filePath, 'utf8');
    send(res, 200, content);
    return;
  }
  await next();
});

if (oidc.router) {
  app.use(async (req, res, next) => {
    await oidc.router(req, res, next);
  });
}

/**
 * Middleware that derives a user role from group membership and ensures a safe fallback.
 *
 * @param {import('node:http').IncomingMessage & {userContext?: any, userRole?: string}} req
 * @param {import('node:http').ServerResponse} res
 * @param {Function} next
 */
async function checkRole(req, res, next) {
  if (!req.userContext) {
    send(res, 401, 'Unauthorized');
    return;
  }

  const groups = req.userContext?.userinfo?.groups || [];
  if (groups.includes('Admin')) {
    req.userRole = 'admin';
  } else if (groups.includes('Artist')) {
    req.userRole = 'artist';
  } else if (groups.includes('Editor')) {
    req.userRole = 'editor';
  } else {
    req.userRole = 'guest';
  }

  await next();
}

app.get('/', async (_req, res) => {
  send(res, 200, 'Welcome to Studio Tools. <a href="/login">Login with Okta</a>');
});

app.get('/dashboard', oidc.ensureAuthenticated(), checkRole, async (req, res) => {
  send(res, 200, `Hello, ${req.userContext.userinfo.name}! Role: ${req.userRole}`);
});

app.get('/admin', oidc.ensureAuthenticated(), checkRole, async (req, res) => {
  if (req.userRole !== 'admin') {
    send(res, 403, 'Forbidden');
    return;
  }
  send(res, 200, 'Admin Dashboard: View logs here.');
});

if (require.main === module) {
  const startServer = () => {
    app.listen(port, () => {
      console.log(`App running on http://localhost:${port}`);
    });
  };

  if (typeof oidc.on === 'function' && !oidc.isMock) {
    oidc.on('ready', startServer);
    oidc.on('error', (err) => {
      console.error('OIDC configuration error', err);
      process.exit(1);
    });
  } else {
    startServer();
  }
}

module.exports = { app, createApp, createMockOidc, createOidcClient, send, checkRole };
