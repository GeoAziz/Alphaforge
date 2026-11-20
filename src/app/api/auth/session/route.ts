import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Route handler for setting/clearing session cookies securely.
 */
export async function POST(request: NextRequest) {
  try {
    const origin = request.headers.get('origin');
    const secFetchSite = request.headers.get('sec-fetch-site');

    // Basic CSRF validation
    if (secFetchSite && secFetchSite !== 'same-origin' && secFetchSite !== 'same-site') {
      return NextResponse.json({ error: 'Forbidden cross-origin request' }, { status: 403 });
    }

    const body = await request.json();
    const { token } = body;

    if (!token || typeof token !== 'string') {
      return NextResponse.json({ error: 'Token is required' }, { status: 400 });
    }

    const response = NextResponse.json({ success: true });
    
    // Set HTTP-only secure session cookie (5 days expiry)
    response.cookies.set('__session', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 24 * 5,
    });

    return response;
  } catch (error: any) {
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE() {
  const response = NextResponse.json({ success: true });
  response.cookies.set('__session', '', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 0,
  });
  return response;
}
