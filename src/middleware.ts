import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Next.js Edge Middleware for Route Access & Session Validation
 * Enforces dual-layer authentication boundaries and safe deep-link preservation.
 */
export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  // 1. Static asset bypass
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.startsWith('/static') ||
    pathname.includes('.') ||
    pathname === '/favicon.ico'
  ) {
    return NextResponse.next();
  }

  // 2. Public route whitelist
  const isPublicMarketingRoute =
    pathname === '/' ||
    pathname === '/chart' ||
    pathname.startsWith('/chart/') ||
    pathname === '/proofs' ||
    pathname.startsWith('/proofs/');

  const isPublicAuthRoute =
    pathname === '/login' ||
    pathname === '/register' ||
    pathname === '/forgot-password';

  const sessionCookie = request.cookies.get('__session')?.value;
  const hasSession = Boolean(sessionCookie && sessionCookie.length > 20);

  // 3. Authenticated visitor trying to access auth pages -> route to terminal
  if (isPublicAuthRoute && hasSession) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Allow public routes
  if (isPublicMarketingRoute || isPublicAuthRoute) {
    return NextResponse.next();
  }

  // 4. Protected terminal routes (everything else)
  if (!hasSession) {
    // Sanitize redirect URL (internal safe paths only)
    const targetPath = pathname + search;
    const safeRedirect = targetPath.startsWith('/') && !targetPath.startsWith('//')
      ? encodeURIComponent(targetPath)
      : encodeURIComponent('/dashboard');

    const loginUrl = new URL(`/login?redirect=${safeRedirect}`, request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
