export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground noise-surface selection:bg-primary selection:text-primary-foreground">
      {children}
    </div>
  );
}
