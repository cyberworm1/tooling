/**
 * @file app.test.js
 * @description Tests for the Okta SSO sample application using Node's built-in test runner.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const { app, createMockOidc } = require('../app');

/**
 * Helper to run a test with a temporary server.
 * @param {(baseUrl: string) => Promise<void>} fn
 */
function withServer(fn) {
  return async () => {
    const server = app.listen(0);
    const { port } = server.address();
    const baseUrl = `http://127.0.0.1:${port}`;
    try {
      await fn(baseUrl);
    } finally {
      server.close();
    }
  };
}

test('GET / returns welcome message with login link', withServer(async (baseUrl) => {
  const response = await fetch(`${baseUrl}/`);
  const text = await response.text();
  assert.equal(response.status, 200);
  assert.match(text, /logging in with Okta/i);
}));

test('GET /dashboard allows authenticated mock user', withServer(async (baseUrl) => {
  const response = await fetch(`${baseUrl}/dashboard`);
  const text = await response.text();
  assert.equal(response.status, 200);
  assert.match(text, /Role: artist/);
}));

test('GET /admin forbids non-admin mock user', withServer(async (baseUrl) => {
  const response = await fetch(`${baseUrl}/admin`);
  const text = await response.text();
  assert.equal(response.status, 403);
  assert.match(text, /Forbidden/);
}));

test('Mock OIDC handler injects default user context', () => {
  const mockOidc = createMockOidc();
  const middleware = mockOidc.ensureAuthenticated();
  const req = {};
  const res = {};
  let called = false;

  return middleware(req, res, async () => {
    called = true;
  }).then(() => {
    assert.ok(req.userContext);
    assert.ok(req.userContext.userinfo.groups.includes('Artist'));
    assert.equal(called, true);
  });
});
