'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Terminal, ArrowRight, AlertCircle } from 'lucide-react';

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTarget = searchParams.get('redirect') || '/onboarding';

  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/auth/session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'AlphaForge-Client',
        },
        body: JSON.stringify({ token: `demo-token-${Date.now()}` }),
      });

      if (!res.ok) {
        throw new Error('Registration failed to create session');
      }

      router.push(redirectTarget);
    } catch (err: any) {
      setError(err.message || 'Registration failed');
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md p-8 rounded-3xl border border-border/80 bg-surface/70 backdrop-blur-xl shadow-2xl space-y-6">
      <div className="text-center space-y-2">
        <Link href="/" className="inline-flex items-center gap-2 group mb-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary to-accent flex items-center justify-center text-primary-foreground font-black shadow-lg shadow-primary/20">
            <Terminal size={18} />
          </div>
          <span className="font-black text-xl tracking-tight uppercase gradient-text">AlphaForge</span>
        </Link>
        <h2 className="text-2xl font-black uppercase tracking-tight text-foreground">Create Account</h2>
        <p className="text-xs text-muted-foreground font-medium">
          Join the non-custodial quantitative intelligence network.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-red/10 border border-red/20 flex items-center gap-2.5 text-xs font-bold text-red">
          <AlertCircle size={15} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleRegister} className="space-y-4">
        <div className="space-y-1.5">
          <Label className="text-xs font-black uppercase tracking-wider text-muted-foreground">Trader Name / Handle</Label>
          <Input
            type="text"
            placeholder="QuantTrader01"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
            className="h-11 bg-background/50 border-border/80"
          />
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs font-black uppercase tracking-wider text-muted-foreground">Email</Label>
          <Input
            type="email"
            placeholder="trader@hedgefund.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="h-11 bg-background/50 border-border/80"
          />
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs font-black uppercase tracking-wider text-muted-foreground">Password</Label>
          <Input
            type="password"
            placeholder="••••••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            className="h-11 bg-background/50 border-border/80"
          />
        </div>

        <Button
          type="submit"
          disabled={isLoading}
          className="w-full h-12 uppercase text-xs font-black tracking-wider bg-primary hover:bg-primary/90 text-primary-foreground gap-2 mt-2 shadow-lg shadow-primary/20"
        >
          {isLoading ? 'Creating Account...' : 'Continue to Onboarding'} <ArrowRight size={14} />
        </Button>
      </form>

      <div className="text-center pt-2 border-t border-border/40 text-xs text-muted-foreground">
        Already have an account?{' '}
        <Link href="/login" className="font-bold text-foreground hover:underline">
          Sign in
        </Link>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-background noise-surface">
      <Suspense fallback={<div className="text-xs font-mono text-muted-foreground">Loading registration...</div>}>
        <RegisterForm />
      </Suspense>
    </div>
  );
}

